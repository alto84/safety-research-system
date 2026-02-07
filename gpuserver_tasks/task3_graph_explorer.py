#!/usr/bin/env python3
"""
Task 3: Interactive Knowledge Graph Explorer
==============================================
Target: gpuserver1 (192.168.1.100)
Depends on: Task 1 (knowledge graph), Task 2 (embeddings optional)
Port: 5002
Output: Web application at http://192.168.1.100:5002

A beautiful, interactive web application for exploring the
biomedical knowledge graph. Built with Flask + D3.js force-directed
graph visualization.

Features:
  - Interactive force-directed graph layout (D3.js v7)
  - Node type filtering (Protein, Cytokine, Drug, Pathway, etc.)
  - Search by node name or type
  - Pathway highlighting (trace CRS, ICANS, HLH cascades)
  - Node detail panel with all attributes and connections
  - Neighborhood expansion (click to explore connections)
  - Edge type filtering
  - t-SNE embedding view (if Task 2 completed)
  - Export selected subgraph as JSON
  - Dark theme matching dashboard aesthetic
  - Patient Risk Overlay with lab value inputs
  - Risk Score Calculator (EASIX, HScore, CAR-HEMATOTOX)
  - Pathway animation with step-by-step cascade flow
  - Node comparison panel
  - Bookmark/save state to URL hash
  - Export graph as SVG/PNG
  - Statistics dashboard
  - Dark/Light theme toggle
  - Keyboard shortcuts
  - Mini-map overview
  - Responsive design for tablets and desktops
  - Full accessibility support
"""

import os
import json
import logging
from pathlib import Path
from collections import defaultdict

try:
    from flask import Flask, render_template_string, jsonify, request
    from flask_cors import CORS
except ImportError:
    os.system("pip3 install flask flask-cors")
    from flask import Flask, render_template_string, jsonify, request
    from flask_cors import CORS

# Setup
BASE_DIR = Path("/home/alton/psp-graph")
KG_DIR = BASE_DIR / "knowledge_graph" / "output"
MODEL_DIR = BASE_DIR / "gnn_models"
PORT = 5002

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("graph-explorer")

app = Flask(__name__)
CORS(app)

# ============================================================
# Data Loading
# ============================================================

graph_data = {"nodes": [], "edges": [], "metadata": {}}
node_index = {}  # name -> node data
adjacency = defaultdict(list)  # node -> [(neighbor, edge_data)]
tsne_coords = {}  # node_id -> (x, y)


def load_graph():
    """Load graph data into memory."""
    global graph_data, node_index, adjacency, tsne_coords

    json_path = KG_DIR / "graph_data.json"
    if not json_path.exists():
        log.error(f"Graph data not found at {json_path}")
        log.error("Run Task 1 first.")
        return False

    log.info(f"Loading graph from {json_path}...")
    with open(json_path) as f:
        graph_data = json.load(f)

    # Build index
    for node in graph_data["nodes"]:
        node_index[node["id"]] = node

    # Build adjacency
    for edge in graph_data["edges"]:
        adjacency[edge["source"]].append({
            "target": edge["target"],
            "type": edge.get("type", "RELATED"),
            "source_db": edge.get("source", ""),
        })
        adjacency[edge["target"]].append({
            "target": edge["source"],
            "type": edge.get("type", "RELATED"),
            "source_db": edge.get("source", ""),
        })

    # Load t-SNE if available
    tsne_path = MODEL_DIR / "tsne_coordinates.json"
    if tsne_path.exists():
        with open(tsne_path) as f:
            for item in json.load(f):
                tsne_coords[item["id"]] = (item["x"], item["y"])
        log.info(f"  Loaded t-SNE for {len(tsne_coords)} nodes")

    meta = graph_data.get("metadata", {})
    log.info(f"  Nodes: {meta.get('node_count', len(graph_data['nodes']))}")
    log.info(f"  Edges: {meta.get('edge_count', len(graph_data['edges']))}")
    return True


# ============================================================
# API Routes
# ============================================================

@app.route("/api/stats")
def api_stats():
    """Graph statistics."""
    meta = graph_data.get("metadata", {})
    return jsonify({
        "nodes": meta.get("node_count", len(graph_data["nodes"])),
        "edges": meta.get("edge_count", len(graph_data["edges"])),
        "node_types": meta.get("node_types", {}),
        "edge_types": meta.get("edge_types", {}),
        "has_tsne": len(tsne_coords) > 0,
    })


@app.route("/api/search")
def api_search():
    """Search nodes by name or type."""
    query = request.args.get("q", "").lower()
    node_type = request.args.get("type", "")
    limit = int(request.args.get("limit", 50))

    results = []
    for node in graph_data["nodes"]:
        if node_type and node.get("type") != node_type:
            continue
        if query and query not in node["id"].lower():
            continue
        results.append({
            "id": node["id"],
            "type": node.get("type", "Unknown"),
            "is_focus": node.get("is_focus", False),
            "degree": len(adjacency.get(node["id"], [])),
            "pagerank": node.get("pagerank", 0),
        })
        if len(results) >= limit:
            break

    results.sort(key=lambda x: x.get("pagerank", 0), reverse=True)
    return jsonify(results)


@app.route("/api/node/<path:node_id>")
def api_node(node_id):
    """Get node details and neighborhood."""
    node = node_index.get(node_id)
    if not node:
        return jsonify({"error": "Node not found"}), 404

    neighbors = adjacency.get(node_id, [])
    return jsonify({
        "node": node,
        "neighbors": neighbors[:100],
        "degree": len(neighbors),
        "tsne": tsne_coords.get(node_id),
    })


@app.route("/api/subgraph")
def api_subgraph():
    """Get subgraph around a node (for visualization)."""
    center = request.args.get("center", "")
    depth = int(request.args.get("depth", 2))
    max_nodes = int(request.args.get("max_nodes", 150))
    filter_type = request.args.get("filter_type", "")

    if not center or center not in node_index:
        return jsonify({"error": "Center node not found"}), 404

    # BFS to collect neighborhood
    visited = set()
    queue = [(center, 0)]
    nodes = []
    edges = []

    while queue and len(visited) < max_nodes:
        node_id, d = queue.pop(0)
        if node_id in visited:
            continue
        if d > depth:
            continue

        visited.add(node_id)
        node = node_index.get(node_id, {"id": node_id, "type": "Unknown"})

        if filter_type and node.get("type") != filter_type and node_id != center:
            continue

        nodes.append({
            "id": node_id,
            "type": node.get("type", "Unknown"),
            "is_focus": node.get("is_focus", False),
            "pagerank": node.get("pagerank", 0),
            "degree_centrality": node.get("degree_centrality", 0),
            "is_center": node_id == center,
            "depth": d,
        })

        for neighbor in adjacency.get(node_id, []):
            target = neighbor["target"]
            if d < depth:
                queue.append((target, d + 1))
            if target in visited:
                edges.append({
                    "source": node_id,
                    "target": target,
                    "type": neighbor["type"],
                })

    return jsonify({"nodes": nodes, "edges": edges})


@app.route("/api/pathway/<path:pathway_name>")
def api_pathway(pathway_name):
    """Get a named pathway trace."""
    pathways = {
        "crs": ["CAR-T_Cell", "IFNG", "Macrophage", "IL6", "IL6ST", "JAK1",
                "STAT3", "Endothelial_Cell", "ANGPT2", "VWF", "CRS_Grade_3"],
        "icans": ["CAR-T_Cell", "IFNG", "IL6", "TNF", "IL1B",
                  "Blood_Brain_Barrier", "BBB_Disruption", "Cerebral_Edema", "ICANS_Grade_3"],
        "hlh": ["IFNG", "IL18", "Macrophage", "Hemophagocytosis",
                "Hyperferritinemia", "Pancytopenia", "HLH_MAS"],
        "il6_cascade": ["IL6", "IL6R", "IL6ST", "JAK1", "STAT3", "IL6",
                       "Endothelial_Cell", "ICAM1", "VCAM1"],
        "tocilizumab": ["Tocilizumab", "IL6R", "IL6ST", "JAK1", "STAT3"],
    }

    path = pathways.get(pathway_name.lower(), [])
    if not path:
        return jsonify({"error": f"Unknown pathway: {pathway_name}"}), 404

    nodes = []
    edges = []
    for node_id in path:
        node = node_index.get(node_id, {"id": node_id, "type": "Unknown"})
        nodes.append({
            "id": node_id,
            "type": node.get("type", "Unknown"),
            "is_focus": True,
            "on_pathway": True,
        })

    for i in range(len(path) - 1):
        edges.append({
            "source": path[i],
            "target": path[i + 1],
            "type": "PATHWAY_STEP",
            "on_pathway": True,
        })

    return jsonify({"name": pathway_name, "nodes": nodes, "edges": edges})


@app.route("/api/tsne")
def api_tsne():
    """Get t-SNE coordinates for all nodes."""
    if not tsne_coords:
        return jsonify({"error": "t-SNE not available. Run Task 2 first."}), 404

    data = []
    for node_id, (x, y) in tsne_coords.items():
        node = node_index.get(node_id, {})
        data.append({
            "id": node_id,
            "x": x,
            "y": y,
            "type": node.get("type", "Unknown"),
            "is_focus": node.get("is_focus", False),
        })

    return jsonify(data)

# ============================================================
# Main HTML Template (Improved v2.0)
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Biomedical Knowledge Graph Explorer</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#06090f;--bg-alt:#0c1220;--card:#111827;--card-hover:#162032;
  --border:#1e293b;--border-hover:#334155;
  --text:#f1f5f9;--text-secondary:#cbd5e1;--muted:#64748b;--muted-light:#94a3b8;
  --blue:#3b82f6;--blue-dim:rgba(59,130,246,0.12);--blue-glow:rgba(59,130,246,0.25);
  --cyan:#06b6d4;--cyan-dim:rgba(6,182,212,0.12);
  --green:#10b981;--green-dim:rgba(16,185,129,0.12);
  --amber:#f59e0b;--amber-dim:rgba(245,158,11,0.12);
  --red:#ef4444;--red-dim:rgba(239,68,68,0.12);
  --purple:#8b5cf6;--purple-dim:rgba(139,92,246,0.12);
  --pink:#ec4899;--indigo:#6366f1;--teal:#14b8a6;--orange:#f97316;
  --radius:8px;--radius-sm:5px;--radius-lg:12px;
  --shadow:0 4px 24px rgba(0,0,0,0.4);--shadow-sm:0 2px 8px rgba(0,0,0,0.3);
  --mono:'JetBrains Mono',monospace;--sans:'Inter',sans-serif;
  --transition:all 0.2s cubic-bezier(0.4,0,0.2,1);
  --sidebar-w:290px;--detail-w:320px;--header-h:52px;
}
[data-theme="light"]{
  --bg:#f8fafc;--bg-alt:#f1f5f9;--card:#ffffff;--card-hover:#f8fafc;
  --border:#e2e8f0;--border-hover:#cbd5e1;
  --text:#0f172a;--text-secondary:#334155;--muted:#64748b;--muted-light:#475569;
  --blue:#2563eb;--blue-dim:rgba(37,99,235,0.08);--blue-glow:rgba(37,99,235,0.15);
  --shadow:0 4px 24px rgba(0,0,0,0.08);--shadow-sm:0 2px 8px rgba(0,0,0,0.05);
}
html{font-size:14px;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
body{font-family:var(--sans);background:var(--bg);color:var(--text);overflow:hidden;height:100vh}

/* Loading overlay */
.loading-overlay{position:fixed;inset:0;background:var(--bg);z-index:9999;display:flex;flex-direction:column;
  align-items:center;justify-content:center;transition:opacity 0.5s ease}
.loading-overlay.hidden{opacity:0;pointer-events:none}
.loading-spinner{width:48px;height:48px;border:3px solid var(--border);border-top-color:var(--blue);
  border-radius:50%;animation:spin 0.8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-text{margin-top:1rem;font-size:0.85rem;color:var(--muted);font-family:var(--mono)}
.loading-progress{width:200px;height:3px;background:var(--border);border-radius:2px;margin-top:0.75rem;overflow:hidden}
.loading-progress-bar{height:100%;background:linear-gradient(90deg,var(--blue),var(--cyan));border-radius:2px;
  width:0%;transition:width 0.3s ease}

/* Toast notifications */
.toast-container{position:fixed;top:calc(var(--header-h) + 12px);right:12px;z-index:10000;display:flex;flex-direction:column;gap:8px}
.toast{padding:0.6rem 1rem;border-radius:var(--radius);font-size:0.8rem;display:flex;align-items:center;gap:0.5rem;
  animation:toastIn 0.3s ease;box-shadow:var(--shadow);max-width:360px;border:1px solid var(--border)}
.toast.error{background:var(--red-dim);border-color:var(--red);color:var(--red)}
.toast.success{background:var(--green-dim);border-color:var(--green);color:var(--green)}
.toast.info{background:var(--blue-dim);border-color:var(--blue);color:var(--blue)}
.toast.warning{background:var(--amber-dim);border-color:var(--amber);color:var(--amber)}
.toast-close{margin-left:auto;cursor:pointer;opacity:0.6;font-size:1rem;line-height:1}
.toast-close:hover{opacity:1}
@keyframes toastIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}

/* Connection indicator */
.conn-indicator{width:8px;height:8px;border-radius:50%;display:inline-block}
.conn-indicator.connected{background:var(--green);box-shadow:0 0 6px var(--green)}
.conn-indicator.disconnected{background:var(--red);box-shadow:0 0 6px var(--red)}
.conn-indicator.loading{background:var(--amber);animation:pulse 1.5s ease infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}

/* App layout */
.app{display:grid;grid-template-columns:var(--sidebar-w) 1fr var(--detail-w);grid-template-rows:var(--header-h) 1fr;
  height:100vh;transition:grid-template-columns 0.3s ease}
.app.sidebar-collapsed{grid-template-columns:0px 1fr var(--detail-w)}
.app.detail-collapsed{grid-template-columns:var(--sidebar-w) 1fr 0px}
.app.both-collapsed{grid-template-columns:0px 1fr 0px}

/* Header */
.header{grid-column:1/-1;display:flex;align-items:center;gap:1rem;padding:0 1rem;
  border-bottom:1px solid var(--border);background:var(--card);z-index:100}
.header-brand{display:flex;align-items:center;gap:0.6rem;flex-shrink:0}
.header-logo{width:28px;height:28px;background:linear-gradient(135deg,var(--blue),var(--purple));
  border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center;
  font-size:0.85rem;font-weight:800;color:#fff}
.header h1{font-size:0.95rem;font-weight:700;letter-spacing:-0.3px;white-space:nowrap}
.header-stats{font-family:var(--mono);font-size:0.72rem;color:var(--muted);display:flex;align-items:center;gap:0.6rem}
.header-actions{margin-left:auto;display:flex;align-items:center;gap:0.4rem}
.header-btn{padding:0.3rem 0.6rem;border-radius:var(--radius-sm);font-size:0.75rem;cursor:pointer;
  background:transparent;border:1px solid var(--border);color:var(--muted);transition:var(--transition);
  display:flex;align-items:center;gap:0.35rem;white-space:nowrap}
.header-btn:hover{border-color:var(--blue);color:var(--text);background:var(--blue-dim)}
.header-btn.active{background:var(--blue-dim);border-color:var(--blue);color:var(--blue)}
.header-divider{width:1px;height:24px;background:var(--border);margin:0 0.3rem}
.kbd{font-family:var(--mono);font-size:0.6rem;padding:0.1rem 0.3rem;border-radius:3px;
  background:var(--bg);border:1px solid var(--border);color:var(--muted);line-height:1}

/* Sidebar */
.sidebar{border-right:1px solid var(--border);background:var(--card);overflow-y:auto;overflow-x:hidden;
  padding:0.75rem;transition:var(--transition);scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.sidebar::-webkit-scrollbar{width:5px}
.sidebar::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.sidebar.collapsed{width:0;padding:0;border:none;overflow:hidden}

.search-box{width:100%;padding:0.5rem 0.7rem 0.5rem 2rem;background:var(--bg);border:1px solid var(--border);
  border-radius:var(--radius);color:var(--text);font-family:var(--sans);font-size:0.8rem;outline:none;
  margin-bottom:0.75rem;transition:var(--transition)}
.search-box:focus{border-color:var(--blue);box-shadow:0 0 0 3px var(--blue-glow)}
.search-box::placeholder{color:var(--muted)}
.search-wrapper{position:relative}
.search-icon{position:absolute;left:0.7rem;top:50%;transform:translateY(-50%);color:var(--muted);font-size:0.8rem;pointer-events:none}
.search-clear{position:absolute;right:0.5rem;top:50%;transform:translateY(-50%);color:var(--muted);
  cursor:pointer;font-size:0.9rem;line-height:1;display:none}
.search-clear.visible{display:block}

.section-title{font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;
  color:var(--muted);margin:1rem 0 0.5rem;display:flex;align-items:center;justify-content:space-between}
.section-title:first-child{margin-top:0}
.section-badge{font-family:var(--mono);font-size:0.6rem;padding:0.1rem 0.4rem;
  background:var(--bg);border-radius:10px;color:var(--muted-light)}

.filter-chips{display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.5rem}
.chip{padding:0.2rem 0.5rem;border-radius:var(--radius-sm);font-size:0.68rem;cursor:pointer;
  border:1px solid var(--border);color:var(--muted);transition:var(--transition);user-select:none}
.chip:hover{border-color:var(--blue);color:var(--text);background:var(--blue-dim)}
.chip.active{background:var(--blue-dim);border-color:var(--blue);color:var(--blue);font-weight:500}

.node-list{display:flex;flex-direction:column;gap:2px}
.node-item{padding:0.35rem 0.5rem;border-radius:var(--radius-sm);font-size:0.75rem;cursor:pointer;
  display:flex;align-items:center;gap:0.5rem;border:1px solid transparent;transition:var(--transition)}
.node-item:hover{background:var(--blue-dim);border-color:var(--border)}
.node-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.node-name{font-family:var(--mono);font-size:0.72rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.node-type-tag{font-size:0.6rem;color:var(--muted);flex-shrink:0;font-family:var(--mono)}
.node-item-skeleton{height:28px;background:linear-gradient(90deg,var(--bg) 25%,var(--border) 50%,var(--bg) 75%);
  background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:var(--radius-sm);margin-bottom:2px}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

.pathway-btn{width:100%;padding:0.45rem 0.6rem;border-radius:var(--radius-sm);font-size:0.75rem;cursor:pointer;
  background:transparent;border:1px solid var(--border);color:var(--text);text-align:left;margin-bottom:0.3rem;
  transition:var(--transition);display:flex;align-items:center;gap:0.5rem}
.pathway-btn:hover{background:var(--blue-dim);border-color:var(--blue)}
.pathway-btn.active{background:var(--blue-dim);border-color:var(--blue);color:var(--blue)}
.pathway-icon{font-size:0.85rem}

/* Detail panel */
.detail-panel{border-left:1px solid var(--border);background:var(--card);overflow-y:auto;overflow-x:hidden;
  padding:0.75rem;transition:var(--transition);scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.detail-panel::-webkit-scrollbar{width:5px}
.detail-panel::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.detail-panel.collapsed{width:0;padding:0;border:none;overflow:hidden}

.detail-title{font-size:0.9rem;font-weight:700;font-family:var(--mono);margin-bottom:0.6rem;
  display:flex;align-items:center;gap:0.5rem;word-break:break-all}
.detail-row{display:flex;justify-content:space-between;font-size:0.72rem;padding:0.3rem 0;
  border-bottom:1px solid rgba(30,41,59,0.3);gap:0.5rem}
.detail-label{color:var(--muted);flex-shrink:0}
.detail-value{font-family:var(--mono);color:var(--text);text-align:right;word-break:break-all}
.neighbor-list{max-height:280px;overflow-y:auto}

/* Tabs for detail panel */
.tab-bar{display:flex;border-bottom:1px solid var(--border);margin-bottom:0.6rem;gap:0}
.tab-btn{padding:0.4rem 0.7rem;font-size:0.72rem;cursor:pointer;background:transparent;border:none;
  color:var(--muted);border-bottom:2px solid transparent;transition:var(--transition);white-space:nowrap}
.tab-btn:hover{color:var(--text)}
.tab-btn.active{color:var(--blue);border-bottom-color:var(--blue)}
.tab-content{display:none}
.tab-content.active{display:block}

/* Graph area */
.graph-area{position:relative;overflow:hidden;background:var(--bg)}
.graph-area svg{width:100%;height:100%;display:block}
.graph-bg-pattern{fill:var(--bg)}

/* Graph overlays */
.zoom-controls{position:absolute;top:12px;right:12px;display:flex;flex-direction:column;gap:4px;z-index:10}
.zoom-btn{width:34px;height:34px;background:var(--card);border:1px solid var(--border);
  border-radius:var(--radius-sm);color:var(--text);font-size:1rem;cursor:pointer;display:flex;
  align-items:center;justify-content:center;transition:var(--transition)}
.zoom-btn:hover{background:var(--blue-dim);border-color:var(--blue);color:var(--blue)}
.zoom-btn[title]::after{content:attr(title);position:absolute;right:calc(100% + 6px);
  font-size:0.65rem;white-space:nowrap;display:none;background:var(--card);padding:0.2rem 0.4rem;
  border-radius:3px;border:1px solid var(--border);color:var(--muted)}
.zoom-btn:hover[title]::after{display:block}

.legend{position:absolute;bottom:12px;left:12px;background:rgba(17,24,39,0.92);backdrop-filter:blur(8px);
  border:1px solid var(--border);border-radius:var(--radius);padding:0.6rem 0.8rem;font-size:0.68rem;z-index:10;
  max-height:200px;overflow-y:auto;transition:var(--transition)}
[data-theme="light"] .legend{background:rgba(255,255,255,0.92)}
.legend-title{font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:var(--muted);margin-bottom:0.4rem}
.legend-item{display:flex;align-items:center;gap:0.4rem;margin-bottom:0.15rem;padding:0.1rem 0}
.legend-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.legend-count{color:var(--muted);font-family:var(--mono);font-size:0.6rem;margin-left:auto}
.legend-toggle{position:absolute;top:4px;right:6px;cursor:pointer;color:var(--muted);font-size:0.75rem}

/* Tooltip */
.tooltip{position:fixed;background:var(--card);border:1px solid var(--border);padding:0.6rem 0.8rem;
  border-radius:var(--radius);font-size:0.75rem;pointer-events:none;z-index:1000;
  box-shadow:var(--shadow);max-width:280px;transition:opacity 0.15s ease}
.tooltip.hidden{opacity:0}
.tt-title{font-weight:700;font-family:var(--mono);margin-bottom:0.25rem;font-size:0.8rem}
.tt-type{color:var(--muted);font-size:0.68rem;display:flex;align-items:center;gap:0.3rem}
.tt-type .tt-dot{width:6px;height:6px;border-radius:50%;display:inline-block}
.tt-stats{margin-top:0.3rem;padding-top:0.3rem;border-top:1px solid var(--border);font-size:0.65rem;color:var(--muted)}
.tt-edge{font-size:0.7rem;color:var(--text-secondary)}

/* Minimap */
.minimap{position:absolute;bottom:12px;right:12px;width:160px;height:120px;background:rgba(17,24,39,0.92);
  backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;z-index:10;
  cursor:pointer;transition:var(--transition)}
[data-theme="light"] .minimap{background:rgba(255,255,255,0.92)}
.minimap.hidden{opacity:0;pointer-events:none;transform:scale(0.8)}
.minimap canvas{width:100%;height:100%}
.minimap-viewport{position:absolute;border:1.5px solid var(--blue);background:rgba(59,130,246,0.08);
  pointer-events:none;transition:none}

/* Keyboard shortcut help */
.shortcut-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);
  z-index:20000;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;
  transition:opacity 0.2s ease}
.shortcut-overlay.visible{opacity:1;pointer-events:auto}
.shortcut-panel{background:var(--card);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:1.5rem;max-width:480px;width:90%;box-shadow:var(--shadow)}
.shortcut-panel h2{font-size:1rem;margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem}
.shortcut-grid{display:grid;grid-template-columns:1fr 1fr;gap:0.4rem 1.5rem}
.shortcut-row{display:flex;justify-content:space-between;align-items:center;font-size:0.78rem;
  padding:0.3rem 0;border-bottom:1px solid var(--border)}
.shortcut-key{font-family:var(--mono);background:var(--bg);padding:0.15rem 0.5rem;border-radius:4px;
  border:1px solid var(--border);font-size:0.7rem;color:var(--muted-light)}

/* Modal panels (risk calc, stats, comparison, patient risk) */
.modal-panel{position:absolute;top:var(--header-h);right:var(--detail-w);width:380px;
  max-height:calc(100vh - var(--header-h));background:var(--card);border-left:1px solid var(--border);
  border-bottom:1px solid var(--border);border-radius:0 0 0 var(--radius-lg);overflow-y:auto;z-index:50;
  box-shadow:var(--shadow);transform:translateX(100%);transition:transform 0.3s ease;padding:1rem;
  scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.modal-panel.visible{transform:translateX(0)}
.modal-title{font-size:0.9rem;font-weight:700;margin-bottom:0.75rem;display:flex;align-items:center;
  justify-content:space-between}
.modal-close{cursor:pointer;color:var(--muted);font-size:1.1rem;transition:var(--transition);
  width:24px;height:24px;display:flex;align-items:center;justify-content:center;border-radius:var(--radius-sm)}
.modal-close:hover{color:var(--text);background:var(--bg)}

/* Form inputs */
.form-group{margin-bottom:0.6rem}
.form-label{font-size:0.68rem;font-weight:600;color:var(--muted);margin-bottom:0.25rem;display:block;
  text-transform:uppercase;letter-spacing:0.5px}
.form-input{width:100%;padding:0.4rem 0.6rem;background:var(--bg);border:1px solid var(--border);
  border-radius:var(--radius-sm);color:var(--text);font-family:var(--mono);font-size:0.78rem;
  outline:none;transition:var(--transition)}
.form-input:focus{border-color:var(--blue);box-shadow:0 0 0 3px var(--blue-glow)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:0.5rem}
.form-hint{font-size:0.6rem;color:var(--muted);margin-top:0.15rem}

/* Risk score results */
.risk-result{padding:0.6rem;border-radius:var(--radius);margin-top:0.5rem;text-align:center}
.risk-result.low{background:var(--green-dim);border:1px solid var(--green)}
.risk-result.medium{background:var(--amber-dim);border:1px solid var(--amber)}
.risk-result.high{background:var(--red-dim);border:1px solid var(--red)}
.risk-score-value{font-size:1.8rem;font-weight:800;font-family:var(--mono)}
.risk-score-label{font-size:0.7rem;color:var(--muted);margin-top:0.2rem}
.risk-score-interp{font-size:0.75rem;font-weight:600;margin-top:0.3rem}

/* Stats cards */
.stat-card{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:0.6rem;
  margin-bottom:0.4rem}
.stat-card-value{font-size:1.4rem;font-weight:800;font-family:var(--mono);color:var(--blue)}
.stat-card-label{font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px}
.stat-bar{height:6px;background:var(--border);border-radius:3px;margin-top:0.3rem;overflow:hidden}
.stat-bar-fill{height:100%;border-radius:3px;transition:width 0.6s ease}

/* Animation controls */
.anim-controls{display:flex;align-items:center;gap:0.4rem;margin-top:0.5rem}
.anim-btn{padding:0.3rem 0.6rem;border-radius:var(--radius-sm);font-size:0.72rem;cursor:pointer;
  background:var(--bg);border:1px solid var(--border);color:var(--text);transition:var(--transition)}
.anim-btn:hover{border-color:var(--blue);background:var(--blue-dim)}
.anim-btn.playing{background:var(--blue-dim);border-color:var(--blue);color:var(--blue)}
.anim-progress{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden}
.anim-progress-fill{height:100%;background:var(--blue);border-radius:2px;transition:width 0.3s ease;width:0%}
.anim-step-label{font-size:0.7rem;color:var(--muted);font-family:var(--mono)}

/* Comparison panel */
.compare-node{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:0.5rem;
  margin-bottom:0.4rem;position:relative}
.compare-node-title{font-family:var(--mono);font-weight:600;font-size:0.78rem;margin-bottom:0.3rem}
.compare-remove{position:absolute;top:0.3rem;right:0.3rem;cursor:pointer;color:var(--muted);font-size:0.8rem}
.compare-shared{background:var(--blue-dim);border:1px solid var(--blue);border-radius:var(--radius);
  padding:0.5rem;margin-top:0.5rem}
.compare-shared-title{font-size:0.72rem;font-weight:600;color:var(--blue);margin-bottom:0.3rem}

/* Empty state */
.empty-state{color:var(--muted);font-size:0.8rem;text-align:center;padding:2rem 0.5rem}
.empty-state-icon{font-size:2rem;margin-bottom:0.5rem;opacity:0.4}

/* Scrollbar for detail panel */
.neighbor-list::-webkit-scrollbar{width:4px}
.neighbor-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

/* Responsive - tablet */
@media(max-width:1200px){
  :root{--sidebar-w:240px;--detail-w:260px}
}
@media(max-width:1024px){
  .app{grid-template-columns:0px 1fr 0px}
  .sidebar,.detail-panel{position:fixed;top:var(--header-h);bottom:0;z-index:200;
    transform:translateX(-100%);transition:transform 0.3s ease}
  .sidebar{left:0;width:280px}
  .sidebar.mobile-open{transform:translateX(0)}
  .detail-panel{right:0;left:auto;width:300px;transform:translateX(100%)}
  .detail-panel.mobile-open{transform:translateX(0)}
  .mobile-toggle{display:flex!important}
  .header h1{font-size:0.85rem}
  .modal-panel{right:0;width:100%;max-width:380px;border-radius:0}
}

/* Touch support */
@media(pointer:coarse){
  .node-item{padding:0.5rem 0.6rem}
  .chip{padding:0.3rem 0.6rem}
  .zoom-btn{width:40px;height:40px;font-size:1.2rem}
}

/* Accessibility: focus visible */
:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
  clip:rect(0,0,0,0);white-space:nowrap;border:0}

/* Graph node/edge styles */
.link{stroke:rgba(100,116,139,0.25);stroke-width:0.8;transition:stroke 0.3s,stroke-width 0.3s,opacity 0.3s}
.link.highlighted{stroke:var(--amber);stroke-width:2;opacity:1}
.link.pathway{stroke:var(--red);stroke-width:2.5;opacity:1;stroke-dasharray:6 3}
.link.pathway-animated{animation:dashFlow 1s linear infinite}
@keyframes dashFlow{to{stroke-dashoffset:-12}}
.link.dimmed{opacity:0.06}
.link.compare-highlight{stroke:var(--cyan);stroke-width:2;opacity:0.8}

.node-circle{transition:r 0.3s ease,opacity 0.3s ease,stroke 0.3s ease}
.node-circle.dimmed{opacity:0.15}
.node-circle.selected{stroke:#fff;stroke-width:2.5}
.node-circle.compare-selected{stroke:var(--cyan);stroke-width:2.5;stroke-dasharray:3 2}
.node-circle.pathway-active{filter:drop-shadow(0 0 6px currentColor)}

.node-label{font-size:9px;fill:var(--text);font-family:var(--mono);pointer-events:none;
  text-anchor:middle;dominant-baseline:central;opacity:0;transition:opacity 0.3s ease}
.node-label.visible{opacity:0.85}
.node-label.focus{font-weight:700;opacity:1;font-size:10px}
.node-label.always-visible{opacity:0.85}

/* ARIA live region */
#aria-live{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}

/* Print */
@media print{.header,.sidebar,.detail-panel,.zoom-controls,.legend,.minimap,.modal-panel{display:none!important}
  .graph-area{position:static;height:auto}.app{display:block}}
</style>
</head>

<body>
<!-- Loading overlay -->
<div class="loading-overlay" id="loading-overlay" role="status" aria-live="polite">
  <div class="loading-spinner" aria-hidden="true"></div>
  <div class="loading-text" id="loading-text">Initializing Graph Explorer...</div>
  <div class="loading-progress"><div class="loading-progress-bar" id="loading-bar"></div></div>
</div>

<!-- Toast container -->
<div class="toast-container" id="toast-container" aria-live="polite"></div>

<!-- ARIA live region for screen reader announcements -->
<div id="aria-live" aria-live="polite" aria-atomic="true"></div>

<!-- Keyboard shortcut overlay -->
<div class="shortcut-overlay" id="shortcut-overlay" role="dialog" aria-label="Keyboard shortcuts">
  <div class="shortcut-panel">
    <h2>Keyboard Shortcuts <span class="modal-close" onclick="toggleShortcuts()">&times;</span></h2>
    <div class="shortcut-grid">
      <div class="shortcut-row"><span>Pause simulation</span><span class="shortcut-key">Space</span></div>
      <div class="shortcut-row"><span>Fullscreen</span><span class="shortcut-key">F</span></div>
      <div class="shortcut-row"><span>Reset view</span><span class="shortcut-key">R</span></div>
      <div class="shortcut-row"><span>Focus search</span><span class="shortcut-key">S</span></div>
      <div class="shortcut-row"><span>Deselect all</span><span class="shortcut-key">Esc</span></div>
      <div class="shortcut-row"><span>Toggle theme</span><span class="shortcut-key">T</span></div>
      <div class="shortcut-row"><span>Toggle minimap</span><span class="shortcut-key">M</span></div>
      <div class="shortcut-row"><span>Show shortcuts</span><span class="shortcut-key">?</span></div>
      <div class="shortcut-row"><span>Export PNG</span><span class="shortcut-key">Ctrl+E</span></div>
      <div class="shortcut-row"><span>Toggle sidebar</span><span class="shortcut-key">[</span></div>
      <div class="shortcut-row"><span>Toggle details</span><span class="shortcut-key">]</span></div>
      <div class="shortcut-row"><span>Compare mode</span><span class="shortcut-key">C</span></div>
    </div>
  </div>
</div>

<div class="app" id="app">
  <!-- Header -->
  <header class="header" role="banner">
    <button class="header-btn mobile-toggle" style="display:none" onclick="toggleMobileSidebar()" aria-label="Toggle sidebar">&#9776;</button>
    <div class="header-brand">
      <div class="header-logo" aria-hidden="true">KG</div>
      <h1>Biomedical Knowledge Graph Explorer</h1>
    </div>
    <div class="header-stats">
      <span class="conn-indicator loading" id="conn-indicator" title="Connection status"></span>
      <span id="stats-text">Loading...</span>
    </div>
    <div class="header-actions">
      <button class="header-btn" id="btn-theme" onclick="toggleTheme()" aria-label="Toggle theme" title="Toggle dark/light theme">
        <span id="theme-icon">&#9789;</span> Theme
      </button>
      <div class="header-divider"></div>
      <button class="header-btn" id="btn-stats" onclick="togglePanel('stats')" title="Graph statistics">Stats</button>
      <button class="header-btn" id="btn-risk-calc" onclick="togglePanel('risk-calc')" title="Risk score calculator">Risk Calc</button>
      <button class="header-btn" id="btn-patient" onclick="togglePanel('patient')" title="Patient risk overlay">Patient</button>
      <button class="header-btn" id="btn-compare" onclick="toggleCompareMode()" title="Compare nodes [C]">Compare</button>
      <div class="header-divider"></div>
      <button class="header-btn" id="btn-export-png" onclick="exportPNG()" title="Export PNG [Ctrl+E]">PNG</button>
      <button class="header-btn" id="btn-export-svg" onclick="exportSVG()" title="Export SVG">SVG</button>
      <button class="header-btn" onclick="shareState()" title="Copy link to clipboard">Share</button>
      <div class="header-divider"></div>
      <button class="header-btn" onclick="toggleShortcuts()" title="Keyboard shortcuts [?]"><span class="kbd">?</span></button>
      <button class="header-btn mobile-toggle" style="display:none" onclick="toggleMobileDetail()" aria-label="Toggle details">Details</button>
    </div>
  </header>

  <!-- Sidebar -->
  <div class="sidebar" id="sidebar" role="navigation" aria-label="Graph navigation">
    <div class="search-wrapper">
      <span class="search-icon" aria-hidden="true">&#128269;</span>
      <input type="text" class="search-box" id="search" placeholder="Search nodes... (S)" autocomplete="off" aria-label="Search nodes" role="searchbox">
      <span class="search-clear" id="search-clear" onclick="clearSearch()" aria-label="Clear search">&times;</span>
    </div>

    <div class="section-title">Node Types <span class="section-badge" id="type-count"></span></div>
    <div class="filter-chips" id="type-filters" role="group" aria-label="Filter by node type"></div>

    <div class="section-title">Pathways</div>
    <button class="pathway-btn" data-pathway="crs" onclick="loadPathway('crs',this)"><span class="pathway-icon">&#9888;</span> CRS Cascade</button>
    <button class="pathway-btn" data-pathway="icans" onclick="loadPathway('icans',this)"><span class="pathway-icon">&#129504;</span> ICANS / Neurotoxicity</button>
    <button class="pathway-btn" data-pathway="hlh" onclick="loadPathway('hlh',this)"><span class="pathway-icon">&#128293;</span> HLH / MAS</button>
    <button class="pathway-btn" data-pathway="il6_cascade" onclick="loadPathway('il6_cascade',this)"><span class="pathway-icon">&#127981;</span> IL-6 Signaling</button>
    <button class="pathway-btn" data-pathway="tocilizumab" onclick="loadPathway('tocilizumab',this)"><span class="pathway-icon">&#128138;</span> Tocilizumab MOA</button>

    <div class="section-title">Animation</div>
    <div class="anim-controls">
      <button class="anim-btn" id="anim-play" onclick="toggleAnimation()" title="Animate pathway">&#9654; Play</button>
      <button class="anim-btn" id="anim-step" onclick="stepAnimation()" title="Step forward">&#9197;</button>
      <button class="anim-btn" id="anim-reset" onclick="resetAnimation()" title="Reset">&#8634;</button>
    </div>
    <div style="display:flex;align-items:center;gap:0.4rem;margin-top:0.3rem">
      <div class="anim-progress"><div class="anim-progress-fill" id="anim-progress-fill"></div></div>
      <span class="anim-step-label" id="anim-step-label">0/0</span>
    </div>

    <div class="section-title">Top Nodes <span class="section-badge">by PageRank</span></div>
    <div class="node-list" id="top-nodes" role="list" aria-label="Top nodes">
      <div class="node-item-skeleton"></div><div class="node-item-skeleton"></div>
      <div class="node-item-skeleton"></div><div class="node-item-skeleton"></div>
      <div class="node-item-skeleton"></div>
    </div>
  </div>

  <!-- Graph canvas -->
  <div class="graph-area" id="graph-area" role="img" aria-label="Knowledge graph visualization">
    <svg id="graph-svg" aria-hidden="true"></svg>
    <div class="zoom-controls" role="toolbar" aria-label="Zoom controls">
      <button class="zoom-btn" onclick="zoomIn()" aria-label="Zoom in" title="Zoom in">+</button>
      <button class="zoom-btn" onclick="zoomOut()" aria-label="Zoom out" title="Zoom out">&minus;</button>
      <button class="zoom-btn" onclick="zoomFit()" aria-label="Fit to view" title="Fit to view">&#8689;</button>
      <button class="zoom-btn" onclick="toggleSimulation()" aria-label="Pause simulation" title="Pause/Resume [Space]" id="btn-sim">&#10074;&#10074;</button>
      <button class="zoom-btn" onclick="toggleMinimap()" aria-label="Toggle minimap" title="Minimap [M]" id="btn-minimap">&#9635;</button>
    </div>
    <div class="legend" id="legend"><div class="legend-title">Node Types</div></div>
    <div class="tooltip hidden" id="tooltip"></div>
    <div class="minimap" id="minimap"><canvas id="minimap-canvas" width="320" height="240"></canvas>
      <div class="minimap-viewport" id="minimap-viewport"></div></div>
  </div>

  <!-- Detail panel -->
  <div class="detail-panel" id="detail-panel" role="complementary" aria-label="Node details">
    <div class="tab-bar" role="tablist">
      <button class="tab-btn active" data-tab="details" onclick="switchTab('details',this)" role="tab" aria-selected="true">Details</button>
      <button class="tab-btn" data-tab="neighbors" onclick="switchTab('neighbors',this)" role="tab">Neighbors</button>
      <button class="tab-btn" data-tab="compare" onclick="switchTab('compare',this)" role="tab" id="tab-compare" style="display:none">Compare</button>
    </div>
    <div class="tab-content active" id="tc-details" role="tabpanel">
      <div id="node-detail"><div class="empty-state"><div class="empty-state-icon">&#128300;</div>Click a node to see details</div></div>
    </div>
    <div class="tab-content" id="tc-neighbors" role="tabpanel">
      <div class="neighbor-list" id="neighbor-list"><div class="empty-state">Select a node</div></div>
    </div>
    <div class="tab-content" id="tc-compare" role="tabpanel">
      <div id="compare-panel"><div class="empty-state">Click nodes while in compare mode</div></div>
    </div>
  </div>
</div>

<!-- Stats panel (floating) -->
<div class="modal-panel" id="panel-stats">
  <div class="modal-title">Graph Statistics <span class="modal-close" onclick="togglePanel('stats')">&times;</span></div>
  <div id="stats-content"></div>
</div>

<!-- Risk Calculator panel -->
<div class="modal-panel" id="panel-risk-calc">
  <div class="modal-title">Risk Score Calculator <span class="modal-close" onclick="togglePanel('risk-calc')">&times;</span></div>
  <div class="tab-bar" role="tablist">
    <button class="tab-btn active" onclick="switchRiskTab('easix',this)" role="tab">EASIX</button>
    <button class="tab-btn" onclick="switchRiskTab('hscore',this)" role="tab">HScore</button>
    <button class="tab-btn" onclick="switchRiskTab('hematotox',this)" role="tab">CAR-HEMATOTOX</button>
  </div>
  <div id="risk-tab-easix" class="tab-content active">
    <div class="form-group"><label class="form-label">LDH (U/L)</label><input class="form-input" id="easix-ldh" type="number" placeholder="250" oninput="calcEASIX()"></div>
    <div class="form-group"><label class="form-label">Creatinine (mg/dL)</label><input class="form-input" id="easix-creat" type="number" step="0.1" placeholder="1.0" oninput="calcEASIX()"></div>
    <div class="form-group"><label class="form-label">Platelets (x10^9/L)</label><input class="form-input" id="easix-plt" type="number" placeholder="150" oninput="calcEASIX()"></div>
    <div id="easix-result"></div>
    <div class="form-hint" style="margin-top:0.5rem">EASIX = (LDH x Creatinine) / Platelets. Higher values predict severe CRS/endothelial dysfunction.</div>
  </div>
  <div id="risk-tab-hscore" class="tab-content">
    <div class="form-group"><label class="form-label">Temperature (&deg;C)</label>
      <select class="form-input" id="hs-temp" onchange="calcHScore()"><option value="0">&lt;38.4</option><option value="33">38.4-39.4</option><option value="49">&gt;39.4</option></select></div>
    <div class="form-group"><label class="form-label">Organomegaly</label>
      <select class="form-input" id="hs-organo" onchange="calcHScore()"><option value="0">None</option><option value="23">Hepato- or Splenomegaly</option><option value="38">Both</option></select></div>
    <div class="form-group"><label class="form-label">Cytopenias</label>
      <select class="form-input" id="hs-cyto" onchange="calcHScore()"><option value="0">1 lineage</option><option value="24">2 lineages</option><option value="34">3 lineages</option></select></div>
    <div class="form-group"><label class="form-label">Ferritin (ng/mL)</label><input class="form-input" id="hs-ferr" type="number" placeholder="500" oninput="calcHScore()"></div>
    <div class="form-group"><label class="form-label">Triglycerides (mg/dL)</label>
      <select class="form-input" id="hs-trig" onchange="calcHScore()"><option value="0">&lt;132</option><option value="44">132-354</option><option value="64">&gt;354</option></select></div>
    <div class="form-group"><label class="form-label">Fibrinogen (mg/dL)</label>
      <select class="form-input" id="hs-fib" onchange="calcHScore()"><option value="0">&gt;250</option><option value="30">&le;250</option></select></div>
    <div class="form-group"><label class="form-label">AST (U/L)</label>
      <select class="form-input" id="hs-ast" onchange="calcHScore()"><option value="0">&lt;30</option><option value="19">&ge;30</option></select></div>
    <div class="form-group"><label class="form-label">Hemophagocytosis on BM biopsy</label>
      <select class="form-input" id="hs-hemo" onchange="calcHScore()"><option value="0">No</option><option value="35">Yes</option></select></div>
    <div class="form-group"><label class="form-label">Known immunosuppression</label>
      <select class="form-input" id="hs-immuno" onchange="calcHScore()"><option value="0">No</option><option value="18">Yes</option></select></div>
    <div id="hscore-result"></div>
  </div>
  <div id="risk-tab-hematotox" class="tab-content">
    <div class="form-group"><label class="form-label">Pre-lymphodepletion ANC (x10^9/L)</label><input class="form-input" id="ht-anc" type="number" step="0.1" placeholder="1.5" oninput="calcHematotox()"></div>
    <div class="form-group"><label class="form-label">Pre-lymphodepletion Hb (g/dL)</label><input class="form-input" id="ht-hb" type="number" step="0.1" placeholder="10" oninput="calcHematotox()"></div>
    <div class="form-group"><label class="form-label">Pre-lymphodepletion Platelets (x10^9/L)</label><input class="form-input" id="ht-plt" type="number" placeholder="100" oninput="calcHematotox()"></div>
    <div class="form-group"><label class="form-label">CRP (mg/L)</label><input class="form-input" id="ht-crp" type="number" step="0.1" placeholder="5" oninput="calcHematotox()"></div>
    <div class="form-group"><label class="form-label">Ferritin (ng/mL)</label><input class="form-input" id="ht-ferr" type="number" placeholder="500" oninput="calcHematotox()"></div>
    <div id="hematotox-result"></div>
    <div class="form-hint" style="margin-top:0.5rem">CAR-HEMATOTOX model: scores 0-2 per variable. Total 0-10.</div>
  </div>
</div>

<!-- Patient Risk Overlay panel -->
<div class="modal-panel" id="panel-patient">
  <div class="modal-title">Patient Risk Overlay <span class="modal-close" onclick="togglePanel('patient')">&times;</span></div>
  <p style="font-size:0.72rem;color:var(--muted);margin-bottom:0.6rem">Enter lab values to highlight relevant pathways on the graph. Abnormal values will light up associated nodes.</p>
  <div class="form-row">
    <div class="form-group"><label class="form-label">IL-6 (pg/mL)</label><input class="form-input patient-lab" id="pt-il6" type="number" placeholder="&lt;7"></div>
    <div class="form-group"><label class="form-label">Ferritin (ng/mL)</label><input class="form-input patient-lab" id="pt-ferr" type="number" placeholder="&lt;300"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label class="form-label">CRP (mg/L)</label><input class="form-input patient-lab" id="pt-crp" type="number" placeholder="&lt;10"></div>
    <div class="form-group"><label class="form-label">LDH (U/L)</label><input class="form-input patient-lab" id="pt-ldh" type="number" placeholder="&lt;250"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label class="form-label">D-dimer (mg/L)</label><input class="form-input patient-lab" id="pt-ddimer" type="number" step="0.1" placeholder="&lt;0.5"></div>
    <div class="form-group"><label class="form-label">Fibrinogen (mg/dL)</label><input class="form-input patient-lab" id="pt-fib" type="number" placeholder="200-400"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label class="form-label">Platelets (x10^9/L)</label><input class="form-input patient-lab" id="pt-plt" type="number" placeholder="150-400"></div>
    <div class="form-group"><label class="form-label">ANC (x10^9/L)</label><input class="form-input patient-lab" id="pt-anc" type="number" step="0.1" placeholder="&gt;1.5"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label class="form-label">IFN-gamma (pg/mL)</label><input class="form-input patient-lab" id="pt-ifng" type="number" placeholder="&lt;15"></div>
    <div class="form-group"><label class="form-label">TNF-alpha (pg/mL)</label><input class="form-input patient-lab" id="pt-tnf" type="number" placeholder="&lt;8"></div>
  </div>
  <div style="display:flex;gap:0.4rem;margin-top:0.6rem">
    <button class="anim-btn" style="flex:1" onclick="applyPatientOverlay()">Apply Overlay</button>
    <button class="anim-btn" onclick="clearPatientOverlay()">Clear</button>
  </div>
  <div id="patient-results" style="margin-top:0.6rem"></div>
</div>

<script>
/* =====================================================
   CONSTANTS & STATE
   ===================================================== */
const API = '';
const typeColors = {
  Protein:'#3b82f6', Cytokine:'#f59e0b', Gene:'#06b6d4', Drug:'#10b981',
  Pathway:'#8b5cf6', Disease:'#ef4444', Adverse_Event:'#ef4444', Cell_Type:'#ec4899',
  BiologicalProcess:'#6366f1', Biomarker:'#14b8a6', Chemical:'#f97316', Unknown:'#64748b'
};

const state = {
  simulation: null, svg: null, g: null, linkG: null, nodeG: null, labelG: null, zoom: null,
  currentNodes: [], currentEdges: [], selectedNode: null, hoveredNode: null,
  compareMode: false, compareNodes: [], animating: false, animStep: 0, animPath: [],
  animTimer: null, simPaused: false, minimapVisible: true, activePanel: null,
  activePathway: null, graphStats: null, node_index_local: {}, searchDebounce: null,
  retryCount: 0, maxRetries: 3, width: 0, height: 0
};

/* =====================================================
   UTILITY FUNCTIONS
   ===================================================== */
function toast(msg, type='info', duration=4000) {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${msg}</span><span class="toast-close" onclick="this.parentElement.remove()">&times;</span>`;
  c.appendChild(t);
  setTimeout(() => { if (t.parentElement) { t.style.opacity = '0'; t.style.transform = 'translateX(100%)'; setTimeout(() => t.remove(), 300); } }, duration);
}

function announce(msg) {
  const el = document.getElementById('aria-live');
  el.textContent = '';
  setTimeout(() => { el.textContent = msg; }, 50);
}

function setLoading(text, progress) {
  const el = document.getElementById('loading-text');
  const bar = document.getElementById('loading-bar');
  if (el) el.textContent = text;
  if (bar) bar.style.width = progress + '%';
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.add('hidden');
  setTimeout(() => overlay.style.display = 'none', 500);
}

async function apiFetch(url, retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const resp = await fetch(API + url);
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${resp.status}`);
      }
      return await resp.json();
    } catch (err) {
      if (attempt === retries - 1) {
        toast(`API Error: ${err.message}`, 'error');
        throw err;
      }
      await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
    }
  }
}

function debounce(fn, ms) {
  let t;
  return function(...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
}

function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function truncate(s, n=18) { return s.length > n ? s.slice(0, n) + '...' : s; }

/* =====================================================
   INITIALIZATION
   ===================================================== */
async function init() {
  try {
    setLoading('Connecting to graph server...', 10);
    const stats = await apiFetch('/api/stats');
    state.graphStats = stats;

    document.getElementById('conn-indicator').className = 'conn-indicator connected';
    document.getElementById('stats-text').textContent =
      `${stats.nodes.toLocaleString()} nodes | ${stats.edges.toLocaleString()} edges`;
    setLoading('Building interface...', 40);

    // Type filter chips
    const filters = document.getElementById('type-filters');
    const types = Object.entries(stats.node_types || {}).sort((a,b) => b[1]-a[1]);
    document.getElementById('type-count').textContent = types.length;
    types.forEach(([type, count]) => {
      const chip = document.createElement('div');
      chip.className = 'chip';
      chip.textContent = `${type} (${count.toLocaleString()})`;
      chip.dataset.type = type;
      chip.setAttribute('role', 'checkbox');
      chip.setAttribute('aria-checked', 'false');
      chip.style.borderColor = typeColors[type] || '#64748b';
      chip.onclick = () => {
        chip.classList.toggle('active');
        chip.setAttribute('aria-checked', chip.classList.contains('active'));
        filterByType(type);
      };
      filters.appendChild(chip);
    });

    // Legend
    buildLegend(stats.node_types || {});

    setLoading('Setting up graph renderer...', 60);
    setupGraph();

    setLoading('Loading initial pathway...', 80);
    await loadPathway('crs');

    // Search with debounce
    document.getElementById('search').addEventListener('input', debounce((e) => {
      const v = e.target.value;
      document.getElementById('search-clear').classList.toggle('visible', v.length > 0);
      searchNodes(v);
    }, 300));

    setLoading('Loading top nodes...', 90);
    await loadTopNodes();

    // Restore state from URL hash
    restoreState();

    setLoading('Ready', 100);
    setTimeout(hideLoading, 300);
    announce('Graph Explorer loaded successfully');

  } catch (err) {
    document.getElementById('conn-indicator').className = 'conn-indicator disconnected';
    setLoading(`Error: ${err.message}. Retrying...`, 0);
    if (state.retryCount < state.maxRetries) {
      state.retryCount++;
      setTimeout(init, 3000);
    } else {
      document.getElementById('loading-text').textContent = 'Failed to connect. Please check that the server is running on port 5002.';
      toast('Failed to connect to graph server after multiple attempts', 'error', 10000);
    }
  }
}

function buildLegend(nodeTypes) {
  const legend = document.getElementById('legend');
  let html = '<div class="legend-title">Node Types</div>';
  for (const [t, c] of Object.entries(typeColors)) {
    if (t === 'Unknown') continue;
    const count = nodeTypes[t] || 0;
    html += `<div class="legend-item"><div class="legend-dot" style="background:${c}"></div><span>${t.replace(/_/g,' ')}</span><span class="legend-count">${count ? count.toLocaleString() : ''}</span></div>`;
  }
  legend.innerHTML = html;
}

/* =====================================================
   GRAPH SETUP & RENDERING
   ===================================================== */
function setupGraph() {
  const area = document.getElementById('graph-area');
  state.width = area.clientWidth;
  state.height = area.clientHeight;

  state.svg = d3.select('#graph-svg');
  state.svg.attr('viewBox', [0, 0, state.width, state.height]);

  // Background pattern (subtle grid)
  const defs = state.svg.append('defs');
  const pat = defs.append('pattern').attr('id','grid').attr('width',40).attr('height',40).attr('patternUnits','userSpaceOnUse');
  pat.append('circle').attr('cx',20).attr('cy',20).attr('r',0.5).attr('fill','rgba(100,116,139,0.15)');
  state.svg.append('rect').attr('width','100%').attr('height','100%').attr('fill','url(#grid)');

  // Arrow markers
  defs.append('marker').attr('id','arrow').attr('viewBox','0 -5 10 10').attr('refX',20).attr('refY',0)
    .attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto')
    .append('path').attr('d','M0,-3L8,0L0,3').attr('fill','rgba(100,116,139,0.4)');
  defs.append('marker').attr('id','arrow-highlight').attr('viewBox','0 -5 10 10').attr('refX',20).attr('refY',0)
    .attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto')
    .append('path').attr('d','M0,-3L8,0L0,3').attr('fill','var(--amber)');
  defs.append('marker').attr('id','arrow-pathway').attr('viewBox','0 -5 10 10').attr('refX',20).attr('refY',0)
    .attr('markerWidth',7).attr('markerHeight',7).attr('orient','auto')
    .append('path').attr('d','M0,-3L8,0L0,3').attr('fill','var(--red)');

  // Glow filter
  const glow = defs.append('filter').attr('id','glow');
  glow.append('feGaussianBlur').attr('stdDeviation','3').attr('result','coloredBlur');
  const fm = glow.append('feMerge');
  fm.append('feMergeNode').attr('in','coloredBlur');
  fm.append('feMergeNode').attr('in','SourceGraphic');

  state.zoom = d3.zoom()
    .scaleExtent([0.05, 15])
    .on('zoom', (event) => {
      state.g.attr('transform', event.transform);
      updateLabelsVisibility(event.transform.k);
      updateMinimap();
    });
  state.svg.call(state.zoom);

  // Touch support
  state.svg.on('touchstart.zoom', null);

  state.g = state.svg.append('g').attr('class', 'graph-container');

  state.simulation = d3.forceSimulation()
    .force('link', d3.forceLink().id(d => d.id).distance(80).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-250).distanceMax(400))
    .force('center', d3.forceCenter(state.width / 2, state.height / 2))
    .force('collision', d3.forceCollide().radius(20))
    .force('x', d3.forceX(state.width / 2).strength(0.03))
    .force('y', d3.forceY(state.height / 2).strength(0.03));

  // Resize observer
  const ro = new ResizeObserver(debounce(() => {
    const w = area.clientWidth, h = area.clientHeight;
    state.width = w; state.height = h;
    state.svg.attr('viewBox', [0, 0, w, h]);
    state.simulation.force('center', d3.forceCenter(w/2, h/2));
    state.simulation.force('x', d3.forceX(w/2).strength(0.03));
    state.simulation.force('y', d3.forceY(h/2).strength(0.03));
    state.simulation.alpha(0.3).restart();
  }, 200));
  ro.observe(area);
}

function renderGraph(nodes, edges) {
  state.currentNodes = nodes;
  state.currentEdges = edges;
  state.g.selectAll('.link-group,.node-group,.label-group').remove();

  // Links
  state.linkG = state.g.append('g').attr('class', 'link-group');
  const link = state.linkG.selectAll('line').data(edges).join('line')
    .attr('class', d => `link ${d.on_pathway ? 'pathway' : ''}`)
    .attr('marker-end', d => d.on_pathway ? 'url(#arrow-pathway)' : 'url(#arrow)')
    .attr('stroke', d => d.on_pathway ? 'var(--red)' : 'rgba(100,116,139,0.25)')
    .on('mouseover', showEdgeTooltip)
    .on('mouseout', hideTooltip);

  // Nodes
  state.nodeG = state.g.append('g').attr('class', 'node-group');
  const nodeCircles = state.nodeG.selectAll('circle').data(nodes).join('circle')
    .attr('class', d => {
      let cls = 'node-circle';
      if (d.is_center) cls += ' selected';
      if (d.on_pathway) cls += ' pathway-active';
      if (state.compareNodes.includes(d.id)) cls += ' compare-selected';
      return cls;
    })
    .attr('r', d => d.is_center ? 14 : d.is_focus ? 9 : 6)
    .attr('fill', d => typeColors[d.type] || '#64748b')
    .attr('stroke', d => d.is_center ? '#fff' : d.is_focus ? 'rgba(255,255,255,0.3)' : 'none')
    .attr('stroke-width', d => d.is_center ? 2.5 : 1)
    .attr('cursor', 'pointer')
    .attr('tabindex', '0')
    .attr('role', 'button')
    .attr('aria-label', d => `${d.id}, type: ${d.type}`)
    .on('click', (event, d) => {
      event.stopPropagation();
      if (state.compareMode) { toggleCompareNode(d.id); }
      else { selectNodeById(d.id); }
    })
    .on('mouseover', showNodeTooltip)
    .on('mouseout', hideTooltip)
    .on('keydown', (event, d) => { if (event.key === 'Enter') selectNodeById(d.id); })
    .call(d3.drag()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded));

  // Labels
  state.labelG = state.g.append('g').attr('class', 'label-group');
  const labels = state.labelG.selectAll('text').data(nodes).join('text')
    .attr('class', d => {
      let cls = 'node-label';
      if (d.is_focus || d.is_center) cls += ' focus always-visible';
      else if (nodes.length < 30) cls += ' always-visible';
      return cls;
    })
    .attr('dy', d => d.is_center ? 20 : 16)
    .text(d => truncate(d.id, d.is_center ? 25 : 16));

  // Click on background to deselect
  state.svg.on('click', () => {
    if (!state.compareMode) deselectAll();
  });

  state.simulation.nodes(nodes).on('tick', () => {
    link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    nodeCircles.attr('cx', d => d.x).attr('cy', d => d.y);
    labels.attr('x', d => d.x).attr('y', d => d.y);
    updateMinimap();
  });
  state.simulation.force('link').links(edges);
  state.simulation.alpha(1).restart();
  state.simPaused = false;
  document.getElementById('btn-sim').innerHTML = '&#10074;&#10074;';

  announce(`Graph loaded with ${nodes.length} nodes and ${edges.length} edges`);
  saveState();
}

function updateLabelsVisibility(zoomLevel) {
  if (!state.labelG) return;
  state.labelG.selectAll('.node-label:not(.always-visible)')
    .classed('visible', zoomLevel > 1.5);
}

/* =====================================================
   DRAG HANDLERS
   ===================================================== */
function dragStarted(event) {
  if (!event.active) state.simulation.alphaTarget(0.3).restart();
  event.subject.fx = event.subject.x;
  event.subject.fy = event.subject.y;
}
function dragged(event) {
  event.subject.fx = event.x;
  event.subject.fy = event.y;
}
function dragEnded(event) {
  if (!event.active) state.simulation.alphaTarget(0);
  event.subject.fx = null;
  event.subject.fy = null;
}

/* =====================================================
   TOOLTIPS
   ===================================================== */
function showNodeTooltip(event, d) {
  const tt = document.getElementById('tooltip');
  tt.classList.remove('hidden');
  const color = typeColors[d.type] || '#64748b';
  tt.innerHTML = `<div class="tt-title">${escapeHtml(d.id)}</div>
    <div class="tt-type"><span class="tt-dot" style="background:${color}"></span>${d.type.replace(/_/g,' ')}${d.is_focus ? ' &middot; CRS-relevant' : ''}</div>
    ${d.pagerank ? `<div class="tt-stats">PageRank: ${Number(d.pagerank).toExponential(2)}${d.degree_centrality ? ` | Degree: ${Number(d.degree_centrality).toFixed(4)}` : ''}</div>` : ''}`;
  positionTooltip(event, tt);
  state.hoveredNode = d.id;

  // Highlight connected edges
  if (state.linkG) {
    state.linkG.selectAll('line')
      .classed('highlighted', l => l.source.id === d.id || l.target.id === d.id)
      .classed('dimmed', l => l.source.id !== d.id && l.target.id !== d.id);
    state.nodeG.selectAll('circle')
      .classed('dimmed', n => {
        if (n.id === d.id) return false;
        return !state.currentEdges.some(e =>
          (e.source.id === d.id && e.target.id === n.id) ||
          (e.target.id === d.id && e.source.id === n.id));
      });
  }
}

function showEdgeTooltip(event, d) {
  const tt = document.getElementById('tooltip');
  tt.classList.remove('hidden');
  tt.innerHTML = `<div class="tt-edge"><strong>${escapeHtml(typeof d.source === 'object' ? d.source.id : d.source)}</strong> &rarr; <strong>${escapeHtml(typeof d.target === 'object' ? d.target.id : d.target)}</strong></div>
    <div class="tt-type">${d.type.replace(/_/g,' ')}</div>`;
  positionTooltip(event, tt);
}

function hideTooltip() {
  document.getElementById('tooltip').classList.add('hidden');
  state.hoveredNode = null;
  if (state.linkG) {
    state.linkG.selectAll('line').classed('highlighted', false).classed('dimmed', false);
    state.nodeG.selectAll('circle').classed('dimmed', false);
  }
}

function positionTooltip(event, tt) {
  const pad = 12;
  let x = event.clientX + pad, y = event.clientY - pad;
  const rect = tt.getBoundingClientRect();
  if (x + 280 > window.innerWidth) x = event.clientX - 280 - pad;
  if (y + 100 > window.innerHeight) y = event.clientY - 100;
  tt.style.left = x + 'px';
  tt.style.top = y + 'px';
}

function deselectAll() {
  state.selectedNode = null;
  if (state.nodeG) {
    state.nodeG.selectAll('circle').attr('opacity', 1).classed('selected', d => d.is_center);
    state.linkG.selectAll('line').attr('opacity', 1);
  }
  document.getElementById('node-detail').innerHTML = '<div class="empty-state"><div class="empty-state-icon">&#128300;</div>Click a node to see details</div>';
  document.getElementById('neighbor-list').innerHTML = '<div class="empty-state">Select a node</div>';
  announce('Selection cleared');
}
</script>

<script>
/* =====================================================
   API CALLS
   ===================================================== */
async function loadSubgraph(center, depth = 2) {
  try {
    toast(`Loading neighborhood: ${center}...`, 'info', 2000);
    const data = await apiFetch(`/api/subgraph?center=${encodeURIComponent(center)}&depth=${depth}&max_nodes=150`);
    if (data.error) { toast(data.error, 'error'); return; }
    if (data.nodes.length === 0) { toast('No nodes found for this query', 'warning'); return; }
    renderGraph(data.nodes, data.edges);
    document.querySelectorAll('.pathway-btn').forEach(b => b.classList.remove('active'));
    state.activePathway = null;
    announce(`Loaded neighborhood of ${center} with ${data.nodes.length} nodes`);
  } catch (e) { /* toast already shown by apiFetch */ }
}

async function loadPathway(name, btnEl) {
  try {
    const data = await apiFetch(`/api/pathway/${name}`);
    if (data.error) { toast(data.error, 'error'); return; }
    renderGraph(data.nodes, data.edges);
    state.activePathway = name;
    state.animPath = data.nodes.map(n => n.id);
    state.animStep = 0;
    updateAnimUI();

    // Highlight active button
    document.querySelectorAll('.pathway-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');
    else document.querySelector(`.pathway-btn[data-pathway="${name}"]`)?.classList.add('active');

    announce(`Loaded pathway: ${name.toUpperCase()}`);
  } catch (e) { /* handled */ }
}

async function selectNodeById(id) {
  state.selectedNode = id;
  try {
    const data = await apiFetch(`/api/node/${encodeURIComponent(id)}`);
    if (data.error) { toast(data.error, 'error'); return; }

    // Highlight in graph
    if (state.nodeG) {
      state.nodeG.selectAll('circle')
        .classed('selected', d => d.id === id)
        .transition().duration(300)
        .attr('opacity', d => d.id === id ? 1 : 0.35);
      state.linkG.selectAll('line')
        .transition().duration(300)
        .attr('opacity', d => {
          const sid = typeof d.source === 'object' ? d.source.id : d.source;
          const tid = typeof d.target === 'object' ? d.target.id : d.target;
          return sid === id || tid === id ? 1 : 0.08;
        });
      setTimeout(() => {
        if (state.selectedNode === id) {
          state.nodeG.selectAll('circle').transition().duration(500).attr('opacity', 1);
          state.linkG.selectAll('line').transition().duration(500).attr('opacity', 1);
        }
      }, 3000);
    }

    // Detail panel
    const n = data.node;
    const color = typeColors[n.type] || '#64748b';
    let html = `<div class="detail-title"><span style="color:${color}">${escapeHtml(n.id)}</span></div>`;
    const importantKeys = ['type', 'is_focus', 'pagerank', 'degree_centrality', 'betweenness_centrality', 'community'];
    const otherKeys = Object.keys(n).filter(k => k !== 'id' && !importantKeys.includes(k));
    for (const key of [...importantKeys, ...otherKeys]) {
      if (n[key] === undefined || key === 'id') continue;
      let val = n[key];
      if (typeof val === 'number' && !Number.isInteger(val)) val = val.toExponential(3);
      if (typeof val === 'boolean') val = val ? 'Yes' : 'No';
      html += `<div class="detail-row"><span class="detail-label">${escapeHtml(key.replace(/_/g,' '))}</span><span class="detail-value">${escapeHtml(String(val))}</span></div>`;
    }
    html += `<div class="detail-row"><span class="detail-label">degree</span><span class="detail-value">${data.degree}</span></div>`;
    if (data.tsne) html += `<div class="detail-row"><span class="detail-label">t-SNE</span><span class="detail-value">(${data.tsne[0].toFixed(1)}, ${data.tsne[1].toFixed(1)})</span></div>`;
    html += `<div style="display:flex;gap:0.3rem;margin-top:0.6rem;flex-wrap:wrap">`;
    html += `<button class="pathway-btn" style="flex:1;min-width:120px" onclick="loadSubgraph('${escapeHtml(id)}')">Explore Neighborhood</button>`;
    html += `<button class="pathway-btn" style="flex:1;min-width:100px" onclick="loadSubgraph('${escapeHtml(id)}',3)">Depth 3</button>`;
    html += `</div>`;
    document.getElementById('node-detail').innerHTML = html;

    // Neighbors
    const nlist = document.getElementById('neighbor-list');
    if (data.neighbors.length === 0) {
      nlist.innerHTML = '<div class="empty-state">No neighbors found</div>';
    } else {
      nlist.innerHTML = data.neighbors.slice(0, 60).map(nb => {
        const nbType = state.node_index_local[nb.target] || 'Unknown';
        const nbColor = typeColors[nbType] || '#64748b';
        return `<div class="node-item" onclick="selectNodeById('${escapeHtml(nb.target)}')" role="listitem" tabindex="0">
          <div class="node-dot" style="background:${nbColor}"></div>
          <span class="node-name">${escapeHtml(nb.target)}</span>
          <span class="node-type-tag">${escapeHtml(nb.type)}</span>
        </div>`;
      }).join('');
    }
    switchTab('details', document.querySelector('.tab-btn[data-tab="details"]'));
    announce(`Selected node: ${id}, ${data.degree} connections`);
    saveState();

  } catch (e) { /* handled */ }
}

async function loadTopNodes() {
  try {
    const data = await apiFetch('/api/search?limit=30');
    const container = document.getElementById('top-nodes');
    container.innerHTML = data.map(n => {
      state.node_index_local[n.id] = n.type;
      return `<div class="node-item" onclick="loadSubgraph('${escapeHtml(n.id)}')" role="listitem" tabindex="0">
        <div class="node-dot" style="background:${typeColors[n.type]||'#64748b'}"></div>
        <span class="node-name">${escapeHtml(n.id)}</span>
        <span class="node-type-tag">${escapeHtml(n.type)}</span>
      </div>`;
    }).join('');
    if (data.length === 0) container.innerHTML = '<div class="empty-state">No nodes found</div>';
  } catch (e) {
    document.getElementById('top-nodes').innerHTML = '<div class="empty-state">Failed to load nodes</div>';
  }
}

async function searchNodes(query) {
  if (!query) { loadTopNodes(); return; }
  try {
    const data = await apiFetch(`/api/search?q=${encodeURIComponent(query)}&limit=30`);
    const container = document.getElementById('top-nodes');
    if (data.length === 0) {
      container.innerHTML = '<div class="empty-state">No matching nodes found</div>';
      return;
    }
    container.innerHTML = data.map(n => {
      state.node_index_local[n.id] = n.type;
      return `<div class="node-item" onclick="loadSubgraph('${escapeHtml(n.id)}')" role="listitem" tabindex="0">
        <div class="node-dot" style="background:${typeColors[n.type]||'#64748b'}"></div>
        <span class="node-name">${escapeHtml(n.id)}</span>
        <span class="node-type-tag">${n.degree} edges</span>
      </div>`;
    }).join('');
  } catch (e) {
    document.getElementById('top-nodes').innerHTML = '<div class="empty-state">Search failed</div>';
  }
}

function clearSearch() {
  document.getElementById('search').value = '';
  document.getElementById('search-clear').classList.remove('visible');
  loadTopNodes();
}

function filterByType(type) {
  const chip = document.querySelector(`.chip[data-type="${type}"]`);
  const active = chip?.classList.contains('active');
  if (active && state.selectedNode) {
    loadSubgraph(state.selectedNode);
  }
}

/* =====================================================
   ZOOM & CONTROLS
   ===================================================== */
function zoomIn() { state.svg.transition().duration(300).call(state.zoom.scaleBy, 1.5); }
function zoomOut() { state.svg.transition().duration(300).call(state.zoom.scaleBy, 0.67); }
function zoomFit() { state.svg.transition().duration(500).call(state.zoom.transform, d3.zoomIdentity); }

function toggleSimulation() {
  state.simPaused = !state.simPaused;
  if (state.simPaused) { state.simulation.stop(); }
  else { state.simulation.alpha(0.3).restart(); }
  document.getElementById('btn-sim').innerHTML = state.simPaused ? '&#9654;' : '&#10074;&#10074;';
  announce(state.simPaused ? 'Simulation paused' : 'Simulation resumed');
}

/* =====================================================
   MINIMAP
   ===================================================== */
function toggleMinimap() {
  state.minimapVisible = !state.minimapVisible;
  document.getElementById('minimap').classList.toggle('hidden', !state.minimapVisible);
}

function updateMinimap() {
  if (!state.minimapVisible || !state.currentNodes.length) return;
  const canvas = document.getElementById('minimap-canvas');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  // Find bounds
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  state.currentNodes.forEach(n => {
    if (n.x !== undefined) {
      minX = Math.min(minX, n.x); maxX = Math.max(maxX, n.x);
      minY = Math.min(minY, n.y); maxY = Math.max(maxY, n.y);
    }
  });
  if (!isFinite(minX)) return;

  const pad = 20;
  const rangeX = (maxX - minX) || 1, rangeY = (maxY - minY) || 1;
  const scale = Math.min((w - pad*2) / rangeX, (h - pad*2) / rangeY);

  // Draw edges
  ctx.strokeStyle = 'rgba(100,116,139,0.15)';
  ctx.lineWidth = 0.5;
  state.currentEdges.forEach(e => {
    const s = typeof e.source === 'object' ? e.source : state.currentNodes.find(n => n.id === e.source);
    const t = typeof e.target === 'object' ? e.target : state.currentNodes.find(n => n.id === e.target);
    if (s && t && s.x !== undefined && t.x !== undefined) {
      ctx.beginPath();
      ctx.moveTo(pad + (s.x - minX) * scale, pad + (s.y - minY) * scale);
      ctx.lineTo(pad + (t.x - minX) * scale, pad + (t.y - minY) * scale);
      ctx.stroke();
    }
  });

  // Draw nodes
  state.currentNodes.forEach(n => {
    if (n.x === undefined) return;
    const x = pad + (n.x - minX) * scale;
    const y = pad + (n.y - minY) * scale;
    ctx.fillStyle = typeColors[n.type] || '#64748b';
    ctx.beginPath();
    ctx.arc(x, y, n.is_center ? 3 : 1.5, 0, Math.PI * 2);
    ctx.fill();
  });

  // Viewport indicator
  const transform = d3.zoomTransform(state.svg.node());
  const vp = document.getElementById('minimap-viewport');
  const vpX = (-transform.x / transform.k - minX) * scale + pad;
  const vpY = (-transform.y / transform.k - minY) * scale + pad;
  const vpW = (state.width / transform.k) * scale;
  const vpH = (state.height / transform.k) * scale;
  vp.style.left = Math.max(0, vpX) + 'px';
  vp.style.top = Math.max(0, vpY) + 'px';
  vp.style.width = Math.min(w, vpW) + 'px';
  vp.style.height = Math.min(h, vpH) + 'px';
}

/* =====================================================
   PATHWAY ANIMATION
   ===================================================== */
function updateAnimUI() {
  const total = state.animPath.length;
  document.getElementById('anim-step-label').textContent = `${state.animStep}/${total}`;
  document.getElementById('anim-progress-fill').style.width = total ? `${(state.animStep / total) * 100}%` : '0%';
}

function toggleAnimation() {
  if (state.animPath.length === 0) { toast('Load a pathway first', 'warning'); return; }
  state.animating = !state.animating;
  document.getElementById('anim-play').classList.toggle('playing', state.animating);
  document.getElementById('anim-play').innerHTML = state.animating ? '&#10074;&#10074; Pause' : '&#9654; Play';
  if (state.animating) runAnimation();
  else clearTimeout(state.animTimer);
}

function runAnimation() {
  if (!state.animating || state.animStep >= state.animPath.length) {
    state.animating = false;
    document.getElementById('anim-play').classList.remove('playing');
    document.getElementById('anim-play').innerHTML = '&#9654; Play';
    return;
  }
  highlightAnimStep(state.animStep);
  state.animStep++;
  updateAnimUI();
  state.animTimer = setTimeout(runAnimation, 1200);
}

function stepAnimation() {
  if (state.animPath.length === 0) { toast('Load a pathway first', 'warning'); return; }
  if (state.animStep >= state.animPath.length) state.animStep = 0;
  highlightAnimStep(state.animStep);
  state.animStep++;
  updateAnimUI();
}

function resetAnimation() {
  state.animating = false;
  state.animStep = 0;
  clearTimeout(state.animTimer);
  document.getElementById('anim-play').classList.remove('playing');
  document.getElementById('anim-play').innerHTML = '&#9654; Play';
  updateAnimUI();
  // Reset visuals
  if (state.nodeG) {
    state.nodeG.selectAll('circle').attr('opacity', 1).attr('r', d => d.is_center ? 14 : d.is_focus ? 9 : 6);
    state.linkG.selectAll('line').attr('opacity', 1).classed('pathway-animated', false);
  }
}

function highlightAnimStep(step) {
  const nodeId = state.animPath[step];
  if (!state.nodeG) return;

  // Dim everything first
  state.nodeG.selectAll('circle').transition().duration(300).attr('opacity', 0.15);
  state.linkG.selectAll('line').transition().duration(300).attr('opacity', 0.05);

  // Light up nodes up to this step
  const activeIds = new Set(state.animPath.slice(0, step + 1));
  state.nodeG.selectAll('circle')
    .filter(d => activeIds.has(d.id))
    .transition().duration(400)
    .attr('opacity', 1)
    .attr('r', d => d.id === nodeId ? 16 : (d.is_center ? 14 : 9));

  // Light up edges between active nodes
  state.linkG.selectAll('line')
    .filter(d => {
      const sid = typeof d.source === 'object' ? d.source.id : d.source;
      const tid = typeof d.target === 'object' ? d.target.id : d.target;
      return activeIds.has(sid) && activeIds.has(tid);
    })
    .transition().duration(400)
    .attr('opacity', 1);

  announce(`Animation step ${step + 1}: ${nodeId}`);
}

/* =====================================================
   COMPARE MODE
   ===================================================== */
function toggleCompareMode() {
  state.compareMode = !state.compareMode;
  document.getElementById('btn-compare').classList.toggle('active', state.compareMode);
  document.getElementById('tab-compare').style.display = state.compareMode ? '' : 'none';
  if (state.compareMode) {
    state.compareNodes = [];
    toast('Compare mode ON - click nodes to select', 'info');
    switchTab('compare', document.getElementById('tab-compare'));
    announce('Compare mode enabled');
  } else {
    state.compareNodes = [];
    if (state.nodeG) state.nodeG.selectAll('circle').classed('compare-selected', false);
    announce('Compare mode disabled');
  }
  updateComparePanel();
}

function toggleCompareNode(id) {
  const idx = state.compareNodes.indexOf(id);
  if (idx >= 0) state.compareNodes.splice(idx, 1);
  else if (state.compareNodes.length < 5) state.compareNodes.push(id);
  else { toast('Maximum 5 nodes for comparison', 'warning'); return; }

  if (state.nodeG) {
    state.nodeG.selectAll('circle').classed('compare-selected', d => state.compareNodes.includes(d.id));
  }
  updateComparePanel();
}

async function updateComparePanel() {
  const panel = document.getElementById('compare-panel');
  if (state.compareNodes.length === 0) {
    panel.innerHTML = '<div class="empty-state">Click nodes while in compare mode<br><small>(max 5 nodes)</small></div>';
    return;
  }

  let html = '';
  const allNeighborSets = {};

  for (const id of state.compareNodes) {
    try {
      const data = await apiFetch(`/api/node/${encodeURIComponent(id)}`);
      const n = data.node;
      const color = typeColors[n.type] || '#64748b';
      const neighborIds = new Set(data.neighbors.map(nb => nb.target));
      allNeighborSets[id] = neighborIds;

      html += `<div class="compare-node">
        <span class="compare-remove" onclick="toggleCompareNode('${escapeHtml(id)}')">&times;</span>
        <div class="compare-node-title" style="color:${color}">${escapeHtml(id)}</div>
        <div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">${n.type}</span></div>
        <div class="detail-row"><span class="detail-label">Degree</span><span class="detail-value">${data.degree}</span></div>
        ${n.pagerank ? `<div class="detail-row"><span class="detail-label">PageRank</span><span class="detail-value">${Number(n.pagerank).toExponential(2)}</span></div>` : ''}
      </div>`;
    } catch (e) { /* skip */ }
  }

  // Find shared neighbors
  if (state.compareNodes.length >= 2) {
    const sets = Object.values(allNeighborSets);
    let shared = new Set(sets[0]);
    for (let i = 1; i < sets.length; i++) {
      shared = new Set([...shared].filter(x => sets[i].has(x)));
    }
    // Remove the compare nodes themselves
    state.compareNodes.forEach(id => shared.delete(id));

    if (shared.size > 0) {
      html += `<div class="compare-shared"><div class="compare-shared-title">Shared Connections (${shared.size})</div>`;
      [...shared].slice(0, 20).forEach(id => {
        const t = state.node_index_local[id] || 'Unknown';
        html += `<div class="node-item" onclick="selectNodeById('${escapeHtml(id)}')">
          <div class="node-dot" style="background:${typeColors[t]||'#64748b'}"></div>
          <span class="node-name">${escapeHtml(id)}</span></div>`;
      });
      html += '</div>';
    } else {
      html += '<div class="empty-state" style="padding:0.5rem">No shared neighbors</div>';
    }
  }

  panel.innerHTML = html;
}

/* =====================================================
   RISK CALCULATORS
   ===================================================== */
function calcEASIX() {
  const ldh = parseFloat(document.getElementById('easix-ldh').value);
  const creat = parseFloat(document.getElementById('easix-creat').value);
  const plt = parseFloat(document.getElementById('easix-plt').value);
  if (!ldh || !creat || !plt || plt === 0) { document.getElementById('easix-result').innerHTML = ''; return; }

  const score = (ldh * creat) / plt;
  let risk = 'low', label = 'Low Risk', color = 'var(--green)';
  if (score > 10) { risk = 'high'; label = 'High Risk - Severe CRS likely'; color = 'var(--red)'; }
  else if (score > 3.2) { risk = 'medium'; label = 'Moderate Risk'; color = 'var(--amber)'; }

  document.getElementById('easix-result').innerHTML = `
    <div class="risk-result ${risk}">
      <div class="risk-score-value" style="color:${color}">${score.toFixed(2)}</div>
      <div class="risk-score-label">EASIX Score</div>
      <div class="risk-score-interp" style="color:${color}">${label}</div>
    </div>`;
}

function calcHScore() {
  const vals = ['hs-temp','hs-organo','hs-cyto','hs-trig','hs-fib','hs-ast','hs-hemo','hs-immuno']
    .map(id => parseInt(document.getElementById(id).value) || 0);
  const ferr = parseFloat(document.getElementById('hs-ferr').value) || 0;
  let ferrScore = 0;
  if (ferr >= 6000) ferrScore = 50;
  else if (ferr >= 2000) ferrScore = 35;
  else if (ferr >= 500) ferrScore = 0; // already 0

  const total = vals.reduce((a, b) => a + b, 0) + ferrScore;
  let risk = 'low', label = 'HLH unlikely (<1% probability)', color = 'var(--green)';
  if (total >= 230) { risk = 'high'; label = 'HLH highly likely (>98%)'; color = 'var(--red)'; }
  else if (total >= 169) { risk = 'medium'; label = 'HLH probable (>54%)'; color = 'var(--amber)'; }

  document.getElementById('hscore-result').innerHTML = `
    <div class="risk-result ${risk}">
      <div class="risk-score-value" style="color:${color}">${total}</div>
      <div class="risk-score-label">HScore</div>
      <div class="risk-score-interp" style="color:${color}">${label}</div>
    </div>`;
}

function calcHematotox() {
  const anc = parseFloat(document.getElementById('ht-anc').value);
  const hb = parseFloat(document.getElementById('ht-hb').value);
  const plt = parseFloat(document.getElementById('ht-plt').value);
  const crp = parseFloat(document.getElementById('ht-crp').value);
  const ferr = parseFloat(document.getElementById('ht-ferr').value);
  if ([anc,hb,plt,crp,ferr].some(v => isNaN(v))) { document.getElementById('hematotox-result').innerHTML = ''; return; }

  let score = 0;
  score += anc < 0.5 ? 2 : anc < 1.0 ? 1 : 0;
  score += hb < 8 ? 2 : hb < 10 ? 1 : 0;
  score += plt < 50 ? 2 : plt < 100 ? 1 : 0;
  score += crp > 50 ? 2 : crp > 10 ? 1 : 0;
  score += ferr > 2000 ? 2 : ferr > 500 ? 1 : 0;

  let risk = 'low', label = 'Low hematotoxicity risk', color = 'var(--green)';
  if (score >= 7) { risk = 'high'; label = 'High risk - prolonged cytopenia expected'; color = 'var(--red)'; }
  else if (score >= 4) { risk = 'medium'; label = 'Moderate hematotoxicity risk'; color = 'var(--amber)'; }

  document.getElementById('hematotox-result').innerHTML = `
    <div class="risk-result ${risk}">
      <div class="risk-score-value" style="color:${color}">${score}/10</div>
      <div class="risk-score-label">CAR-HEMATOTOX</div>
      <div class="risk-score-interp" style="color:${color}">${label}</div>
    </div>`;
}

function switchRiskTab(name, btn) {
  document.querySelectorAll('#panel-risk-calc .tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('#panel-risk-calc .tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`risk-tab-${name}`).classList.add('active');
  if (btn) btn.classList.add('active');
}

/* =====================================================
   PATIENT RISK OVERLAY
   ===================================================== */
function applyPatientOverlay() {
  const labMappings = {
    'pt-il6': { threshold: 7, high: true, nodes: ['IL6', 'IL6R', 'IL6ST', 'JAK1', 'STAT3'] },
    'pt-ferr': { threshold: 300, high: true, nodes: ['Hyperferritinemia', 'HLH_MAS', 'Macrophage'] },
    'pt-crp': { threshold: 10, high: true, nodes: ['CRS_Grade_3', 'Endothelial_Cell', 'IL6'] },
    'pt-ldh': { threshold: 250, high: true, nodes: ['Endothelial_Cell', 'ANGPT2', 'VWF'] },
    'pt-ddimer': { threshold: 0.5, high: true, nodes: ['VWF', 'Endothelial_Cell', 'CRS_Grade_3'] },
    'pt-fib': { threshold: 200, high: false, nodes: ['HLH_MAS', 'Pancytopenia'] },
    'pt-plt': { threshold: 150, high: false, nodes: ['Pancytopenia', 'HLH_MAS', 'CRS_Grade_3'] },
    'pt-anc': { threshold: 1.5, high: false, nodes: ['Pancytopenia'] },
    'pt-ifng': { threshold: 15, high: true, nodes: ['IFNG', 'Macrophage', 'CAR-T_Cell'] },
    'pt-tnf': { threshold: 8, high: true, nodes: ['TNF', 'IL1B', 'Blood_Brain_Barrier', 'ICANS_Grade_3'] },
  };

  const alertNodes = new Set();
  const alerts = [];

  for (const [inputId, mapping] of Object.entries(labMappings)) {
    const val = parseFloat(document.getElementById(inputId).value);
    if (isNaN(val)) continue;
    const abnormal = mapping.high ? val > mapping.threshold : val < mapping.threshold;
    if (abnormal) {
      mapping.nodes.forEach(n => alertNodes.add(n));
      const label = document.querySelector(`label[for="${inputId}"]`)?.textContent ||
                    document.getElementById(inputId).parentElement.querySelector('.form-label')?.textContent || inputId;
      alerts.push(`<span style="color:var(--red)">${label}: ${val}</span> (threshold: ${mapping.high ? '>' : '<'}${mapping.threshold})`);
    }
  }

  // Apply overlay to graph
  if (state.nodeG && alertNodes.size > 0) {
    state.nodeG.selectAll('circle')
      .transition().duration(500)
      .attr('opacity', d => alertNodes.has(d.id) ? 1 : 0.15)
      .attr('r', d => alertNodes.has(d.id) ? 14 : (d.is_center ? 12 : 5));
    state.linkG.selectAll('line')
      .transition().duration(500)
      .attr('opacity', d => {
        const sid = typeof d.source === 'object' ? d.source.id : d.source;
        const tid = typeof d.target === 'object' ? d.target.id : d.target;
        return alertNodes.has(sid) && alertNodes.has(tid) ? 0.8 : 0.03;
      });

    const results = document.getElementById('patient-results');
    results.innerHTML = `<div style="font-size:0.72rem;margin-bottom:0.3rem;font-weight:600;color:var(--red)">Abnormal Values (${alerts.length}):</div>` +
      alerts.map(a => `<div style="font-size:0.68rem;margin-bottom:0.15rem">${a}</div>`).join('') +
      `<div style="font-size:0.68rem;margin-top:0.3rem;color:var(--muted)">${alertNodes.size} nodes highlighted on graph</div>`;
    toast(`Patient overlay: ${alertNodes.size} pathway nodes highlighted`, 'warning');
  } else if (alertNodes.size === 0) {
    toast('All values within normal range', 'success');
    document.getElementById('patient-results').innerHTML = '<div style="font-size:0.72rem;color:var(--green)">All values within normal range.</div>';
  }
}

function clearPatientOverlay() {
  document.querySelectorAll('.patient-lab').forEach(el => el.value = '');
  document.getElementById('patient-results').innerHTML = '';
  if (state.nodeG) {
    state.nodeG.selectAll('circle').transition().duration(400).attr('opacity', 1)
      .attr('r', d => d.is_center ? 14 : d.is_focus ? 9 : 6);
    state.linkG.selectAll('line').transition().duration(400).attr('opacity', 1);
  }
  toast('Patient overlay cleared', 'info');
}
</script>

<script>
/* =====================================================
   PANELS & TABS
   ===================================================== */
function togglePanel(name) {
  const panel = document.getElementById(`panel-${name}`);
  const btn = document.getElementById(`btn-${name === 'risk-calc' ? 'risk-calc' : name}`);
  const isVis = panel.classList.contains('visible');

  // Close all panels first
  document.querySelectorAll('.modal-panel').forEach(p => p.classList.remove('visible'));
  document.querySelectorAll('.header-btn').forEach(b => {
    if (['btn-stats','btn-risk-calc','btn-patient'].includes(b.id)) b.classList.remove('active');
  });

  if (!isVis) {
    panel.classList.add('visible');
    if (btn) btn.classList.add('active');
    state.activePanel = name;
    if (name === 'stats') populateStats();
  } else {
    state.activePanel = null;
  }
}

function switchTab(name, btn) {
  const panel = btn?.closest('.detail-panel') || document.getElementById('detail-panel');
  panel.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  panel.querySelectorAll('.tab-btn').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected','false'); });
  document.getElementById(`tc-${name}`).classList.add('active');
  if (btn) { btn.classList.add('active'); btn.setAttribute('aria-selected','true'); }
}

async function populateStats() {
  const el = document.getElementById('stats-content');
  if (!state.graphStats) { el.innerHTML = '<div class="empty-state">Loading...</div>'; return; }
  const s = state.graphStats;

  const nodeTotal = s.nodes;
  const edgeTotal = s.edges;
  const density = nodeTotal > 1 ? (2 * edgeTotal) / (nodeTotal * (nodeTotal - 1)) : 0;
  const avgDegree = nodeTotal > 0 ? (2 * edgeTotal / nodeTotal) : 0;

  let html = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;margin-bottom:0.6rem">
    <div class="stat-card"><div class="stat-card-value">${nodeTotal.toLocaleString()}</div><div class="stat-card-label">Total Nodes</div></div>
    <div class="stat-card"><div class="stat-card-value">${edgeTotal.toLocaleString()}</div><div class="stat-card-label">Total Edges</div></div>
    <div class="stat-card"><div class="stat-card-value">${density.toExponential(2)}</div><div class="stat-card-label">Graph Density</div></div>
    <div class="stat-card"><div class="stat-card-value">${avgDegree.toFixed(1)}</div><div class="stat-card-label">Avg Degree</div></div>
  </div>`;

  // Node type breakdown
  html += '<div class="section-title" style="margin-top:0.6rem">Node Types</div>';
  const types = Object.entries(s.node_types || {}).sort((a,b) => b[1]-a[1]);
  types.forEach(([type, count]) => {
    const pct = ((count / nodeTotal) * 100).toFixed(1);
    const color = typeColors[type] || '#64748b';
    html += `<div style="margin-bottom:0.4rem">
      <div style="display:flex;justify-content:space-between;font-size:0.72rem;margin-bottom:0.15rem">
        <span style="color:${color};font-weight:600">${type.replace(/_/g,' ')}</span>
        <span style="font-family:var(--mono);color:var(--muted)">${count.toLocaleString()} (${pct}%)</span>
      </div>
      <div class="stat-bar"><div class="stat-bar-fill" style="width:${pct}%;background:${color}"></div></div>
    </div>`;
  });

  // Edge type breakdown
  html += '<div class="section-title" style="margin-top:0.8rem">Edge Types</div>';
  const etypes = Object.entries(s.edge_types || {}).sort((a,b) => b[1]-a[1]);
  etypes.forEach(([type, count]) => {
    const pct = ((count / edgeTotal) * 100).toFixed(1);
    html += `<div style="margin-bottom:0.3rem">
      <div style="display:flex;justify-content:space-between;font-size:0.72rem">
        <span>${type.replace(/_/g,' ')}</span>
        <span style="font-family:var(--mono);color:var(--muted)">${count.toLocaleString()} (${pct}%)</span>
      </div>
      <div class="stat-bar"><div class="stat-bar-fill" style="width:${pct}%;background:var(--muted)"></div></div>
    </div>`;
  });

  // Current view stats
  html += '<div class="section-title" style="margin-top:0.8rem">Current View</div>';
  html += `<div class="stat-card"><div class="stat-card-value">${state.currentNodes.length}</div><div class="stat-card-label">Visible Nodes</div></div>`;
  html += `<div class="stat-card"><div class="stat-card-value">${state.currentEdges.length}</div><div class="stat-card-label">Visible Edges</div></div>`;
  html += `<div style="font-size:0.65rem;color:var(--muted);margin-top:0.3rem">t-SNE embeddings: ${s.has_tsne ? 'Available' : 'Not computed'}</div>`;

  el.innerHTML = html;
}

/* =====================================================
   THEME
   ===================================================== */
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('theme-icon').textContent = next === 'dark' ? '\u263D' : '\u2600';
  localStorage.setItem('graph-theme', next);
  announce(`Theme changed to ${next}`);
}

function loadTheme() {
  const saved = localStorage.getItem('graph-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    document.getElementById('theme-icon').textContent = saved === 'dark' ? '\u263D' : '\u2600';
  }
}

/* =====================================================
   EXPORT
   ===================================================== */
function exportSVG() {
  const svgEl = document.getElementById('graph-svg');
  const clone = svgEl.cloneNode(true);
  // Add styles inline
  const style = document.createElement('style');
  style.textContent = '.link{stroke:rgba(100,116,139,0.25);stroke-width:0.8}.link.pathway{stroke:#ef4444;stroke-width:2.5;stroke-dasharray:6 3}.node-label{font-size:9px;fill:#f1f5f9;font-family:monospace;text-anchor:middle}';
  clone.prepend(style);
  const blob = new Blob([new XMLSerializer().serializeToString(clone)], {type: 'image/svg+xml'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `kg-export-${Date.now()}.svg`;
  a.click(); URL.revokeObjectURL(url);
  toast('SVG exported', 'success');
}

function exportPNG() {
  const svgEl = document.getElementById('graph-svg');
  const clone = svgEl.cloneNode(true);
  const style = document.createElement('style');
  style.textContent = '.link{stroke:rgba(100,116,139,0.25);stroke-width:0.8}.link.pathway{stroke:#ef4444;stroke-width:2.5}.node-label{font-size:9px;fill:#f1f5f9;font-family:monospace;text-anchor:middle}';
  clone.prepend(style);
  const svgData = new XMLSerializer().serializeToString(clone);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = state.width * 2;
  canvas.height = state.height * 2;
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const img = new Image();
  img.onload = function() {
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `kg-export-${Date.now()}.png`;
      a.click(); URL.revokeObjectURL(url);
      toast('PNG exported', 'success');
    });
  };
  img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
}

/* =====================================================
   BOOKMARK / STATE PERSISTENCE
   ===================================================== */
function saveState() {
  const s = {};
  if (state.selectedNode) s.n = state.selectedNode;
  if (state.activePathway) s.p = state.activePathway;
  const transform = state.svg ? d3.zoomTransform(state.svg.node()) : null;
  if (transform && (transform.k !== 1 || transform.x !== 0 || transform.y !== 0)) {
    s.z = `${transform.k.toFixed(2)},${transform.x.toFixed(0)},${transform.y.toFixed(0)}`;
  }
  if (Object.keys(s).length > 0) {
    history.replaceState(null, '', '#' + new URLSearchParams(s).toString());
  }
}

function restoreState() {
  const hash = window.location.hash.slice(1);
  if (!hash) return;
  try {
    const params = new URLSearchParams(hash);
    if (params.get('p')) {
      loadPathway(params.get('p'));
    }
    if (params.get('n')) {
      setTimeout(() => selectNodeById(params.get('n')), 1000);
    }
    if (params.get('z')) {
      const [k, x, y] = params.get('z').split(',').map(Number);
      if (!isNaN(k)) {
        setTimeout(() => {
          state.svg.call(state.zoom.transform, d3.zoomIdentity.translate(x, y).scale(k));
        }, 500);
      }
    }
  } catch (e) { /* ignore bad hash */ }
}

function shareState() {
  saveState();
  const url = window.location.href;
  navigator.clipboard.writeText(url).then(() => {
    toast('Link copied to clipboard', 'success');
  }).catch(() => {
    toast('Could not copy link', 'warning');
  });
}

/* =====================================================
   KEYBOARD SHORTCUTS
   ===================================================== */
function toggleShortcuts() {
  document.getElementById('shortcut-overlay').classList.toggle('visible');
}

document.addEventListener('keydown', (e) => {
  // Don't trigger if typing in input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
    if (e.key === 'Escape') e.target.blur();
    return;
  }

  switch (e.key) {
    case ' ':
      e.preventDefault();
      toggleSimulation();
      break;
    case 'f': case 'F':
      if (!e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        const area = document.getElementById('graph-area');
        if (document.fullscreenElement) document.exitFullscreen();
        else area.requestFullscreen?.();
      }
      break;
    case 'r': case 'R':
      if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); zoomFit(); }
      break;
    case 's': case 'S':
      if (!e.ctrlKey && !e.metaKey) { e.preventDefault(); document.getElementById('search').focus(); }
      break;
    case 'Escape':
      if (document.getElementById('shortcut-overlay').classList.contains('visible')) {
        toggleShortcuts();
      } else if (state.activePanel) {
        togglePanel(state.activePanel);
      } else {
        deselectAll();
      }
      break;
    case 't': case 'T':
      if (!e.ctrlKey && !e.metaKey) toggleTheme();
      break;
    case 'm': case 'M':
      if (!e.ctrlKey && !e.metaKey) toggleMinimap();
      break;
    case '?':
      toggleShortcuts();
      break;
    case 'e': case 'E':
      if (e.ctrlKey || e.metaKey) { e.preventDefault(); exportPNG(); }
      break;
    case '[':
      toggleSidebar();
      break;
    case ']':
      toggleDetailPanel();
      break;
    case 'c': case 'C':
      if (!e.ctrlKey && !e.metaKey) toggleCompareMode();
      break;
  }
});

/* =====================================================
   RESPONSIVE / MOBILE
   ===================================================== */
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed');
  document.getElementById('app').classList.toggle('sidebar-collapsed');
  setTimeout(() => {
    state.width = document.getElementById('graph-area').clientWidth;
    state.height = document.getElementById('graph-area').clientHeight;
    state.svg.attr('viewBox', [0, 0, state.width, state.height]);
  }, 350);
}

function toggleDetailPanel() {
  document.getElementById('detail-panel').classList.toggle('collapsed');
  document.getElementById('app').classList.toggle('detail-collapsed');
  setTimeout(() => {
    state.width = document.getElementById('graph-area').clientWidth;
    state.height = document.getElementById('graph-area').clientHeight;
    state.svg.attr('viewBox', [0, 0, state.width, state.height]);
  }, 350);
}

function toggleMobileSidebar() {
  document.getElementById('sidebar').classList.toggle('mobile-open');
  document.getElementById('detail-panel').classList.remove('mobile-open');
}

function toggleMobileDetail() {
  document.getElementById('detail-panel').classList.toggle('mobile-open');
  document.getElementById('sidebar').classList.remove('mobile-open');
}

/* =====================================================
   INITIALIZATION
   ===================================================== */
loadTheme();
init();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    if load_graph():
        log.info(f"\nStarting Biomedical Graph Explorer on port {PORT}...")
        log.info(f"Open http://192.168.1.100:{PORT} in your browser")
        app.run(host="0.0.0.0", port=PORT, debug=False)
    else:
        log.error("Failed to load graph data. Run Task 1 first.")
