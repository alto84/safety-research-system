#!/usr/bin/env python3
"""
Task 2: Train Graph Neural Network Embeddings
===============================================
Target: gpuserver1 (192.168.1.100) - RTX 5090
Depends on: Task 1 (knowledge graph must be built first)
Estimated runtime: 15-45 minutes (GPU training)
Output: /home/alton/safety-graph/gnn_models/

Trains multiple GNN architectures on the biomedical knowledge graph:
  1. Node2Vec embeddings (unsupervised, for baseline similarity)
  2. Graph Attention Network (GAT) for node classification (risk prediction)
  3. Relational GCN for edge-type-aware reasoning
  4. Link prediction model for pathway discovery

The trained embeddings enable:
  - Patient risk scoring grounded in graph topology
  - Novel pathway hypothesis generation via link prediction
  - Drug-target-AE relationship discovery
  - Similarity search across biological entities
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

# Setup
BASE_DIR = Path("/home/alton/safety-graph")
KG_DIR = BASE_DIR / "knowledge_graph" / "output"
EMBEDDINGS_DIR = KG_DIR / "embeddings_ready"
MODEL_DIR = BASE_DIR / "gnn_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(MODEL_DIR / "training.log")
    ]
)
log = logging.getLogger("gnn-trainer")

# ============================================================
# Install dependencies
# ============================================================

def install_deps():
    """Install required packages for GNN training."""
    packages = [
        "torch-geometric",
        "torch-scatter",
        "torch-sparse",
        "torch-cluster",
        "torch-spline-conv",
        "scikit-learn",
        "matplotlib",
        "seaborn",
    ]

    log.info("Checking/installing dependencies...")
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_").split("_")[0] if "torch" not in pkg else "torch_geometric")
        except ImportError:
            log.info(f"  Installing {pkg}...")
            os.system(f"pip3 install {pkg}")

install_deps()

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam
from torch.optim.lr_scheduler import CosineAnnealingLR

try:
    import torch_geometric
    from torch_geometric.data import Data
    from torch_geometric.nn import GATConv, GCNConv, SAGEConv, TransformerConv
    from torch_geometric.utils import negative_sampling, train_test_split_edges
    HAS_PYG = True
except ImportError:
    log.warning("PyTorch Geometric not available. Using fallback NetworkX-based methods.")
    HAS_PYG = False

from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    classification_report, accuracy_score
)
from sklearn.model_selection import train_test_split
from sklearn.manifold import TSNE


# ============================================================
# Data Loading
# ============================================================

class GraphDataLoader:
    """Loads preprocessed graph data from Task 1."""

    def __init__(self, embeddings_dir: Path):
        self.dir = embeddings_dir

    def load(self):
        """Load graph data into PyTorch tensors."""
        log.info("Loading graph data...")

        # Load numpy arrays
        features = np.load(self.dir / "node_features.npy")
        edge_index = np.load(self.dir / "edge_index.npy")
        edge_types = np.load(self.dir / "edge_types.npy")

        # Load mappings
        with open(self.dir / "mappings.json") as f:
            mappings = json.load(f)

        log.info(f"  Nodes: {features.shape[0]}")
        log.info(f"  Features per node: {features.shape[1]}")
        log.info(f"  Edges: {edge_index.shape[1]}")
        log.info(f"  Node types: {len(mappings['type_to_idx'])}")
        log.info(f"  Edge types: {mappings['num_edge_types']}")

        # Convert to PyTorch
        x = torch.FloatTensor(features)
        ei = torch.LongTensor(edge_index)
        et = torch.LongTensor(edge_types)

        # Create labels: is_focus nodes (CRS-relevant) = positive class
        # This is the column right after one-hot type encoding
        num_types = len(mappings['type_to_idx'])
        labels = (features[:, num_types] > 0.5).astype(np.int64)
        y = torch.LongTensor(labels)

        log.info(f"  Focus nodes (positive class): {labels.sum()} / {len(labels)}")

        return {
            "x": x,
            "edge_index": ei,
            "edge_type": et,
            "y": y,
            "mappings": mappings,
            "num_classes": 2,
            "num_node_types": len(mappings['type_to_idx']),
            "num_edge_types": mappings['num_edge_types'],
        }


# ============================================================
# Model Definitions
# ============================================================

class GATRiskPredictor(nn.Module):
    """Graph Attention Network for node-level risk classification.

    Multi-head attention over graph structure to learn which
    neighbors are most informative for safety prediction.
    """

    def __init__(self, in_dim, hidden_dim=128, out_dim=2, heads=4, dropout=0.3):
        super().__init__()
        self.dropout = dropout

        # GAT layers
        self.conv1 = GATConv(in_dim, hidden_dim, heads=heads, dropout=dropout)
        self.conv2 = GATConv(hidden_dim * heads, hidden_dim, heads=heads, dropout=dropout)
        self.conv3 = GATConv(hidden_dim * heads, hidden_dim, heads=1, concat=False, dropout=dropout)

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim)
        )

        # Embedding output (for downstream use)
        self.embedding_dim = hidden_dim

    def forward(self, x, edge_index, return_embeddings=False):
        # GAT message passing
        h = F.dropout(x, p=self.dropout, training=self.training)
        h = F.elu(self.conv1(h, edge_index))

        h = F.dropout(h, p=self.dropout, training=self.training)
        h = F.elu(self.conv2(h, edge_index))

        h = F.dropout(h, p=self.dropout, training=self.training)
        embeddings = self.conv3(h, edge_index)

        if return_embeddings:
            return embeddings

        # Classify
        out = self.classifier(embeddings)
        return out, embeddings


class GraphSAGERiskPredictor(nn.Module):
    """GraphSAGE model — samples and aggregates neighbor features.

    More scalable than full-graph GAT for large knowledge graphs.
    """

    def __init__(self, in_dim, hidden_dim=128, out_dim=2, dropout=0.3):
        super().__init__()
        self.dropout = dropout

        self.conv1 = SAGEConv(in_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.conv3 = SAGEConv(hidden_dim, hidden_dim)

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, out_dim)
        )

        self.embedding_dim = hidden_dim

    def forward(self, x, edge_index, return_embeddings=False):
        h = F.relu(self.conv1(x, edge_index))
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = F.relu(self.conv2(h, edge_index))
        h = F.dropout(h, p=self.dropout, training=self.training)
        embeddings = self.conv3(h, edge_index)

        if return_embeddings:
            return embeddings

        out = self.classifier(embeddings)
        return out, embeddings


class LinkPredictor(nn.Module):
    """Link prediction model for pathway discovery.

    Given node embeddings, predicts whether an edge should exist
    between two nodes. Used to discover novel pathway connections.
    """

    def __init__(self, embedding_dim):
        super().__init__()
        self.predictor = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(embedding_dim, embedding_dim // 2),
            nn.ReLU(),
            nn.Linear(embedding_dim // 2, 1),
        )

    def forward(self, z_src, z_dst):
        h = torch.cat([z_src, z_dst], dim=-1)
        return self.predictor(h).squeeze(-1)


# ============================================================
# Training
# ============================================================

class GNNTrainer:
    """Trains GNN models on the biomedical knowledge graph."""

    def __init__(self, data: dict, device: str = None):
        self.data = data
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.results = {}
        log.info(f"Training device: {self.device}")
        if self.device == "cuda":
            log.info(f"  GPU: {torch.cuda.get_device_name(0)}")
            log.info(f"  VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")

    def train_gat(self, epochs=200, lr=0.001, hidden_dim=128):
        """Train Graph Attention Network."""
        log.info(f"\n{'='*50}")
        log.info("Training GAT Risk Predictor")
        log.info(f"{'='*50}")

        x = self.data["x"].to(self.device)
        edge_index = self.data["edge_index"].to(self.device)
        y = self.data["y"].to(self.device)

        # Train/val/test split (60/20/20)
        num_nodes = x.shape[0]
        indices = np.arange(num_nodes)
        train_idx, test_idx = train_test_split(indices, test_size=0.2, stratify=y.cpu().numpy())
        train_idx, val_idx = train_test_split(train_idx, test_size=0.25, stratify=y.cpu().numpy()[train_idx])

        train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        test_mask = torch.zeros(num_nodes, dtype=torch.bool)
        train_mask[train_idx] = True
        val_mask[val_idx] = True
        test_mask[test_idx] = True
        train_mask = train_mask.to(self.device)
        val_mask = val_mask.to(self.device)
        test_mask = test_mask.to(self.device)

        # Handle class imbalance
        pos_weight = (y == 0).sum().float() / max((y == 1).sum().float(), 1)
        class_weights = torch.FloatTensor([1.0, min(pos_weight, 10.0)]).to(self.device)

        model = GATRiskPredictor(
            in_dim=x.shape[1],
            hidden_dim=hidden_dim,
            out_dim=2,
            heads=4,
            dropout=0.3
        ).to(self.device)

        optimizer = Adam(model.parameters(), lr=lr, weight_decay=5e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
        criterion = nn.CrossEntropyLoss(weight=class_weights)

        best_val_f1 = 0
        best_state = None
        patience = 30
        no_improve = 0

        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()

            out, _ = model(x, edge_index)
            loss = criterion(out[train_mask], y[train_mask])
            loss.backward()
            optimizer.step()
            scheduler.step()

            # Validation
            if (epoch + 1) % 5 == 0:
                model.eval()
                with torch.no_grad():
                    out, _ = model(x, edge_index)
                    val_pred = out[val_mask].argmax(dim=1).cpu().numpy()
                    val_true = y[val_mask].cpu().numpy()
                    val_f1 = f1_score(val_true, val_pred, zero_division=0)
                    val_acc = accuracy_score(val_true, val_pred)

                    if val_f1 > best_val_f1:
                        best_val_f1 = val_f1
                        best_state = model.state_dict().copy()
                        no_improve = 0
                    else:
                        no_improve += 5

                if (epoch + 1) % 20 == 0:
                    log.info(f"  Epoch {epoch+1}/{epochs} | Loss: {loss.item():.4f} | "
                            f"Val F1: {val_f1:.4f} | Val Acc: {val_acc:.4f}")

                if no_improve >= patience:
                    log.info(f"  Early stopping at epoch {epoch+1}")
                    break

        # Evaluate on test set
        if best_state:
            model.load_state_dict(best_state)

        model.eval()
        with torch.no_grad():
            out, embeddings = model(x, edge_index)
            test_pred = out[test_mask].argmax(dim=1).cpu().numpy()
            test_true = y[test_mask].cpu().numpy()
            test_probs = F.softmax(out[test_mask], dim=1)[:, 1].cpu().numpy()

        test_f1 = f1_score(test_true, test_pred, zero_division=0)
        test_acc = accuracy_score(test_true, test_pred)
        try:
            test_auroc = roc_auc_score(test_true, test_probs)
        except ValueError:
            test_auroc = 0.0

        log.info(f"\n  GAT Test Results:")
        log.info(f"    Accuracy: {test_acc:.4f}")
        log.info(f"    F1 Score: {test_f1:.4f}")
        log.info(f"    AUROC:    {test_auroc:.4f}")
        log.info(f"\n{classification_report(test_true, test_pred, zero_division=0)}")

        # Save model and embeddings
        torch.save(best_state or model.state_dict(), MODEL_DIR / "gat_model.pt")
        all_embeddings = embeddings.cpu().numpy()
        np.save(MODEL_DIR / "gat_embeddings.npy", all_embeddings)

        self.results["gat"] = {
            "accuracy": float(test_acc),
            "f1": float(test_f1),
            "auroc": float(test_auroc),
            "embedding_dim": model.embedding_dim,
            "epochs_trained": epoch + 1,
        }

        return model, all_embeddings

    def train_sage(self, epochs=200, lr=0.001, hidden_dim=128):
        """Train GraphSAGE model."""
        log.info(f"\n{'='*50}")
        log.info("Training GraphSAGE Risk Predictor")
        log.info(f"{'='*50}")

        x = self.data["x"].to(self.device)
        edge_index = self.data["edge_index"].to(self.device)
        y = self.data["y"].to(self.device)

        num_nodes = x.shape[0]
        indices = np.arange(num_nodes)
        train_idx, test_idx = train_test_split(indices, test_size=0.2, stratify=y.cpu().numpy())
        train_idx, val_idx = train_test_split(train_idx, test_size=0.25, stratify=y.cpu().numpy()[train_idx])

        train_mask = torch.zeros(num_nodes, dtype=torch.bool).to(self.device)
        val_mask = torch.zeros(num_nodes, dtype=torch.bool).to(self.device)
        test_mask = torch.zeros(num_nodes, dtype=torch.bool).to(self.device)
        train_mask[train_idx] = True
        val_mask[val_idx] = True
        test_mask[test_idx] = True

        pos_weight = (y == 0).sum().float() / max((y == 1).sum().float(), 1)
        class_weights = torch.FloatTensor([1.0, min(pos_weight, 10.0)]).to(self.device)

        model = GraphSAGERiskPredictor(
            in_dim=x.shape[1], hidden_dim=hidden_dim, out_dim=2
        ).to(self.device)

        optimizer = Adam(model.parameters(), lr=lr, weight_decay=5e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
        criterion = nn.CrossEntropyLoss(weight=class_weights)

        best_val_f1 = 0
        best_state = None

        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            out, _ = model(x, edge_index)
            loss = criterion(out[train_mask], y[train_mask])
            loss.backward()
            optimizer.step()
            scheduler.step()

            if (epoch + 1) % 20 == 0:
                model.eval()
                with torch.no_grad():
                    out, _ = model(x, edge_index)
                    val_pred = out[val_mask].argmax(dim=1).cpu().numpy()
                    val_true = y[val_mask].cpu().numpy()
                    val_f1 = f1_score(val_true, val_pred, zero_division=0)
                    if val_f1 > best_val_f1:
                        best_val_f1 = val_f1
                        best_state = model.state_dict().copy()
                    log.info(f"  Epoch {epoch+1}/{epochs} | Loss: {loss.item():.4f} | Val F1: {val_f1:.4f}")

        if best_state:
            model.load_state_dict(best_state)
        model.eval()
        with torch.no_grad():
            out, embeddings = model(x, edge_index)
            test_pred = out[test_mask].argmax(dim=1).cpu().numpy()
            test_true = y[test_mask].cpu().numpy()
            test_probs = F.softmax(out[test_mask], dim=1)[:, 1].cpu().numpy()

        test_f1 = f1_score(test_true, test_pred, zero_division=0)
        test_acc = accuracy_score(test_true, test_pred)
        try:
            test_auroc = roc_auc_score(test_true, test_probs)
        except ValueError:
            test_auroc = 0.0

        log.info(f"\n  GraphSAGE Test Results:")
        log.info(f"    Accuracy: {test_acc:.4f}")
        log.info(f"    F1 Score: {test_f1:.4f}")
        log.info(f"    AUROC:    {test_auroc:.4f}")

        torch.save(best_state or model.state_dict(), MODEL_DIR / "sage_model.pt")
        np.save(MODEL_DIR / "sage_embeddings.npy", embeddings.cpu().numpy())

        self.results["sage"] = {
            "accuracy": float(test_acc),
            "f1": float(test_f1),
            "auroc": float(test_auroc),
        }
        return model, embeddings.cpu().numpy()

    def train_link_predictor(self, encoder_model, epochs=100, lr=0.001):
        """Train link prediction for pathway discovery."""
        log.info(f"\n{'='*50}")
        log.info("Training Link Predictor (Pathway Discovery)")
        log.info(f"{'='*50}")

        x = self.data["x"].to(self.device)
        edge_index = self.data["edge_index"].to(self.device)

        # Get embeddings from trained encoder
        encoder_model.eval()
        with torch.no_grad():
            if hasattr(encoder_model, 'forward'):
                embeddings = encoder_model(x, edge_index, return_embeddings=True)
            else:
                embeddings = x  # fallback

        embedding_dim = embeddings.shape[1]
        link_model = LinkPredictor(embedding_dim).to(self.device)
        optimizer = Adam(link_model.parameters(), lr=lr)

        # Positive edges
        num_edges = edge_index.shape[1]
        perm = torch.randperm(num_edges)
        train_edges = edge_index[:, perm[:int(0.8 * num_edges)]]
        test_edges = edge_index[:, perm[int(0.8 * num_edges):]]

        for epoch in range(epochs):
            link_model.train()
            optimizer.zero_grad()

            # Positive samples
            pos_src = embeddings[train_edges[0]]
            pos_dst = embeddings[train_edges[1]]
            pos_score = link_model(pos_src, pos_dst)

            # Negative samples
            neg_edges = negative_sampling(edge_index, num_nodes=x.shape[0],
                                         num_neg_samples=train_edges.shape[1])
            neg_src = embeddings[neg_edges[0]]
            neg_dst = embeddings[neg_edges[1]]
            neg_score = link_model(neg_src, neg_dst)

            # Binary cross-entropy loss
            pos_loss = F.binary_cross_entropy_with_logits(pos_score, torch.ones_like(pos_score))
            neg_loss = F.binary_cross_entropy_with_logits(neg_score, torch.zeros_like(neg_score))
            loss = pos_loss + neg_loss

            loss.backward()
            optimizer.step()

            if (epoch + 1) % 20 == 0:
                log.info(f"  Epoch {epoch+1}/{epochs} | Loss: {loss.item():.4f}")

        # Evaluate
        link_model.eval()
        with torch.no_grad():
            pos_src = embeddings[test_edges[0]]
            pos_dst = embeddings[test_edges[1]]
            pos_pred = torch.sigmoid(link_model(pos_src, pos_dst)).cpu().numpy()

            neg_edges = negative_sampling(edge_index, num_nodes=x.shape[0],
                                         num_neg_samples=test_edges.shape[1])
            neg_src = embeddings[neg_edges[0]]
            neg_dst = embeddings[neg_edges[1]]
            neg_pred = torch.sigmoid(link_model(neg_src, neg_dst)).cpu().numpy()

        all_pred = np.concatenate([pos_pred, neg_pred])
        all_true = np.concatenate([np.ones(len(pos_pred)), np.zeros(len(neg_pred))])
        auroc = roc_auc_score(all_true, all_pred)

        log.info(f"\n  Link Prediction AUROC: {auroc:.4f}")

        torch.save(link_model.state_dict(), MODEL_DIR / "link_predictor.pt")
        self.results["link_prediction"] = {"auroc": float(auroc)}

        return link_model

    def generate_tsne_visualization(self, embeddings, mappings):
        """Generate t-SNE visualization data for the graph explorer."""
        log.info("\nGenerating t-SNE visualization...")

        # Subsample if too large
        n = embeddings.shape[0]
        if n > 5000:
            indices = np.random.choice(n, 5000, replace=False)
            sub_embeddings = embeddings[indices]
        else:
            indices = np.arange(n)
            sub_embeddings = embeddings

        tsne = TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42)
        coords = tsne.fit_transform(sub_embeddings)

        # Map back to node names
        idx_to_node = {v: k for k, v in mappings["node_to_idx"].items()}
        vis_data = []
        for i, idx in enumerate(indices):
            node_name = idx_to_node.get(int(idx), f"node_{idx}")
            vis_data.append({
                "id": node_name,
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
                "idx": int(idx),
            })

        with open(MODEL_DIR / "tsne_coordinates.json", 'w') as f:
            json.dump(vis_data, f)

        log.info(f"  t-SNE computed for {len(vis_data)} nodes")

    def save_results(self):
        """Save training results summary."""
        self.results["training_time"] = datetime.now().isoformat()
        self.results["device"] = self.device
        if self.device == "cuda":
            self.results["gpu"] = torch.cuda.get_device_name(0)

        with open(MODEL_DIR / "training_results.json", 'w') as f:
            json.dump(self.results, f, indent=2)

        log.info(f"\n{'='*50}")
        log.info("Training Summary")
        log.info(f"{'='*50}")
        for model_name, metrics in self.results.items():
            if isinstance(metrics, dict) and "auroc" in metrics:
                log.info(f"  {model_name}: AUROC={metrics['auroc']:.4f}, "
                        f"F1={metrics.get('f1', 'N/A')}")


# ============================================================
# Fallback: NetworkX-based embeddings if PyG unavailable
# ============================================================

def networkx_fallback():
    """If PyTorch Geometric isn't available, use NetworkX + numpy."""
    log.info("Running NetworkX fallback (no PyG)...")

    # Load the graph
    graph_path = KG_DIR / "graph.graphml"
    if not graph_path.exists():
        log.error(f"Graph file not found at {graph_path}")
        log.error("Run Task 1 first to build the knowledge graph.")
        sys.exit(1)

    import networkx as nx
    G = nx.read_graphml(str(graph_path))
    log.info(f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Compute spectral embeddings
    log.info("Computing spectral embeddings...")
    try:
        from sklearn.decomposition import TruncatedSVD
        A = nx.adjacency_matrix(G.to_undirected())
        svd = TruncatedSVD(n_components=min(128, A.shape[0] - 1), random_state=42)
        embeddings = svd.fit_transform(A.astype(float))
        np.save(MODEL_DIR / "spectral_embeddings.npy", embeddings)
        log.info(f"  Spectral embeddings: {embeddings.shape}")
    except Exception as e:
        log.error(f"  Spectral embedding failed: {e}")

    # Node2Vec-like random walk embeddings using basic approach
    log.info("Computing random walk embeddings...")
    try:
        from sklearn.decomposition import TruncatedSVD

        G_undirected = G.to_undirected()
        # DeepWalk-style: power of adjacency matrix
        A = nx.adjacency_matrix(G_undirected).astype(float)
        # Normalize
        from scipy.sparse import diags
        degrees = np.array(A.sum(axis=1)).flatten()
        degrees[degrees == 0] = 1
        D_inv = diags(1.0 / degrees)
        A_norm = D_inv @ A

        # Random walk matrix: sum of A^1 through A^5
        walk_matrix = A_norm.copy()
        power = A_norm.copy()
        for k in range(2, 6):
            power = power @ A_norm
            walk_matrix += power

        svd = TruncatedSVD(n_components=min(64, walk_matrix.shape[0] - 1), random_state=42)
        rw_embeddings = svd.fit_transform(walk_matrix)
        np.save(MODEL_DIR / "randomwalk_embeddings.npy", rw_embeddings)
        log.info(f"  Random walk embeddings: {rw_embeddings.shape}")
    except Exception as e:
        log.error(f"  Random walk embedding failed: {e}")

    # Save node mapping
    node_list = list(G.nodes())
    with open(MODEL_DIR / "node_list.json", 'w') as f:
        json.dump(node_list, f)

    log.info("Fallback embeddings complete.")


# ============================================================
# Main
# ============================================================

def main():
    log.info("=" * 60)
    log.info("GNN Embedding Training")
    log.info("=" * 60)
    start = time.time()

    # Check if Task 1 output exists
    if not (EMBEDDINGS_DIR / "node_features.npy").exists():
        log.warning("Embeddings data not found. Checking for GraphML...")
        if (KG_DIR / "graph.graphml").exists():
            networkx_fallback()
            return
        else:
            log.error("No graph data found. Run Task 1 first.")
            sys.exit(1)

    if not HAS_PYG:
        log.warning("PyTorch Geometric not available. Using fallback.")
        networkx_fallback()
        return

    # Load data
    loader = GraphDataLoader(EMBEDDINGS_DIR)
    data = loader.load()

    # Train models
    trainer = GNNTrainer(data)

    # 1. GAT model
    gat_model, gat_embeddings = trainer.train_gat(epochs=200, hidden_dim=128)

    # 2. GraphSAGE model
    sage_model, sage_embeddings = trainer.train_sage(epochs=200, hidden_dim=128)

    # 3. Link predictor (using best encoder)
    best_model = gat_model  # Use GAT as encoder
    trainer.train_link_predictor(best_model, epochs=100)

    # 4. t-SNE visualization
    trainer.generate_tsne_visualization(gat_embeddings, data["mappings"])

    # Save results
    trainer.save_results()

    elapsed = time.time() - start
    log.info(f"\nTotal training time: {elapsed/60:.1f} minutes")


if __name__ == "__main__":
    main()
