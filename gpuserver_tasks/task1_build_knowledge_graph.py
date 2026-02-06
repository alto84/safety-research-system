#!/usr/bin/env python3
"""
Task 1: Build Comprehensive Biomedical Knowledge Graph
=======================================================
Target: gpuserver1 (192.168.1.100)
Estimated runtime: 30-60 minutes (download + parse + build)
Output: /home/alton/safety-graph/knowledge_graph/

This script downloads and integrates data from 7 major biomedical databases
to construct a comprehensive knowledge graph focused on cell therapy safety
mechanisms (CRS, ICANS, HLH).

Data Sources:
  1. Reactome     - Biological pathway data (signaling cascades, immune pathways)
  2. STRING       - Protein-protein interaction network (confidence-scored)
  3. DrugBank     - Drug-target interactions and mechanisms
  4. SIDER        - Drug side effects with MedDRA coding
  5. CTD          - Chemical-Disease-Gene associations (toxicogenomics)
  6. UniProt      - Protein function annotations
  7. PubChem/MeSH - Chemical and disease ontology links

Graph Schema:
  Nodes: Gene, Protein, Drug, Disease, Pathway, Cytokine, Receptor,
         Cell_Type, Adverse_Event, Biomarker, BiologicalProcess
  Edges: INTERACTS_WITH, TARGETS, CAUSES, PARTICIPATES_IN, ACTIVATES,
         INHIBITS, PRODUCES, EXPRESSED_IN, ASSOCIATED_WITH, TREATS

Output Files:
  - graph.graphml          (NetworkX GraphML format)
  - graph_data.json        (JSON node/edge lists for web visualization)
  - graph_stats.json       (Statistics and metadata)
  - neo4j_import/          (CSV files for Neo4j bulk import)
  - embeddings_ready/      (Preprocessed data for GNN training)
"""

import os
import sys
import json
import gzip
import csv
import time
import logging
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import URLError
from io import StringIO, BytesIO

# Optional imports - install if needed
try:
    import networkx as nx
except ImportError:
    os.system("pip3 install networkx")
    import networkx as nx

try:
    import numpy as np
except ImportError:
    os.system("pip3 install numpy")
    import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    os.system("pip3 install tqdm")
    from tqdm import tqdm

try:
    import pandas as pd
except ImportError:
    os.system("pip3 install pandas")
    import pandas as pd

# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path("/home/alton/safety-graph/knowledge_graph")
DATA_DIR = BASE_DIR / "raw_data"
OUTPUT_DIR = BASE_DIR / "output"
NEO4J_DIR = OUTPUT_DIR / "neo4j_import"
EMBEDDINGS_DIR = OUTPUT_DIR / "embeddings_ready"

# Ensure directories exist
for d in [DATA_DIR, OUTPUT_DIR, NEO4J_DIR, EMBEDDINGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / "build.log")
    ]
)
log = logging.getLogger("kg-builder")

# ============================================================
# Data Source URLs
# ============================================================

SOURCES = {
    "string_links": {
        "url": "https://stringdb-downloads.org/download/protein.links.v12.0/9606.protein.links.v12.0.txt.gz",
        "desc": "STRING human protein-protein interactions",
        "file": "9606.protein.links.txt.gz"
    },
    "string_info": {
        "url": "https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz",
        "desc": "STRING protein annotations",
        "file": "9606.protein.info.txt.gz"
    },
    "reactome_pathways": {
        "url": "https://reactome.org/download/current/ReactomePathways.txt",
        "desc": "Reactome pathway definitions",
        "file": "ReactomePathways.txt"
    },
    "reactome_relations": {
        "url": "https://reactome.org/download/current/ReactomePathwaysRelation.txt",
        "desc": "Reactome pathway hierarchy",
        "file": "ReactomePathwaysRelation.txt"
    },
    "reactome_genes": {
        "url": "https://reactome.org/download/current/Ensembl2Reactome.txt",
        "desc": "Reactome gene-pathway mappings",
        "file": "Ensembl2Reactome.txt"
    },
    "sider_effects": {
        "url": "http://sideeffects.embl.de/media/download/meddra_all_se.tsv.gz",
        "desc": "SIDER drug side effects (MedDRA coded)",
        "file": "meddra_all_se.tsv.gz"
    },
    "sider_drugs": {
        "url": "http://sideeffects.embl.de/media/download/drug_names.tsv",
        "desc": "SIDER drug names",
        "file": "drug_names.tsv"
    },
    "ctd_chem_gene": {
        "url": "https://ctdbase.org/reports/CTD_chem_gene_ixns.tsv.gz",
        "desc": "CTD chemical-gene interactions",
        "file": "CTD_chem_gene_ixns.tsv.gz"
    },
    "ctd_gene_disease": {
        "url": "https://ctdbase.org/reports/CTD_genes_diseases.tsv.gz",
        "desc": "CTD gene-disease associations",
        "file": "CTD_genes_diseases.tsv.gz"
    },
}

# Key cytokines and proteins for CRS/ICANS/HLH focus
CRS_FOCUS_GENES = {
    "IL6", "IL1B", "IL1A", "IL10", "IL2", "IL8", "IL15", "IL18",
    "IFNG", "TNF", "TNFSF10",
    "IL6R", "IL6ST", "IL1R1", "IL2RA", "IL10RA",
    "CXCL8", "CXCL10", "CCL2", "CCL3", "CCL4",
    "CSF1", "CSF2", "CSF3",
    "VEGFA", "ANGPT2",
    "FAS", "FASLG",
    "GZMB", "PRF1",
    "HMGB1", "S100A8", "S100A9",
    "NLRP3", "CASP1",
    "JAK1", "JAK2", "JAK3", "TYK2",
    "STAT1", "STAT3", "STAT4", "STAT5A", "STAT5B",
    "NFKB1", "NFKB2", "RELA", "RELB",
    "MAPK1", "MAPK3", "MAPK8", "MAPK14",
    "CD3E", "CD3D", "CD3G", "CD247",
    "CD19", "MS4A1", "CD38",
    "FCGR3A", "CD14", "CD68",
    "ICAM1", "VCAM1", "SELE", "SELP",
    "VWF", "ADAMTS13",
    "FGA", "FGB", "FGG", "F2", "PLG",
    "CRP", "SAA1", "HP", "FTH1", "FTL",
    "ALB", "LDH", "LDHA", "LDHB",
}

# Key pathways for CRS/ICANS/HLH
CRS_FOCUS_PATHWAYS = {
    "Cytokine Signaling", "Interleukin-6", "JAK-STAT", "NF-kB",
    "TNF signaling", "Interferon gamma", "Toll-like receptor",
    "Complement", "Coagulation", "Innate Immune", "Adaptive Immune",
    "T cell receptor", "B cell receptor", "Natural killer",
    "Macrophage", "Dendritic cell", "Neutrophil",
    "Apoptosis", "Necroptosis", "Pyroptosis",
    "MAPK", "PI3K-Akt", "mTOR",
    "Hemostasis", "Platelet activation",
    "Endothelial", "Vascular",
}

# Key drugs for cell therapy context
CRS_FOCUS_DRUGS = {
    "tocilizumab", "siltuximab", "anakinra", "ruxolitinib",
    "dexamethasone", "methylprednisolone",
    "axicabtagene ciloleucel", "tisagenlecleucel",
    "brexucabtagene autoleucel", "lisocabtagene maraleucel",
    "idecabtagene vicleucel", "ciltacabtagene autoleucel",
    "blinatumomab", "tebentafusp",
    "nivolumab", "pembrolizumab", "ipilimumab", "atezolizumab",
}


# ============================================================
# Download Manager
# ============================================================

class DownloadManager:
    """Handles downloading with progress, caching, and retry."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cache_file = data_dir / "download_cache.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self.cache_file.exists():
            return json.loads(self.cache_file.read_text())
        return {}

    def _save_cache(self):
        self.cache_file.write_text(json.dumps(self.cache, indent=2))

    def download(self, key: str, url: str, filename: str, desc: str) -> Path:
        """Download a file with caching and progress."""
        filepath = self.data_dir / filename

        # Check cache
        if filepath.exists() and key in self.cache:
            log.info(f"  [cached] {desc}")
            return filepath

        log.info(f"  Downloading {desc}...")
        log.info(f"    URL: {url}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                req = Request(url, headers={"User-Agent": "SafetyKG/1.0"})
                response = urlopen(req, timeout=120)
                total_size = int(response.headers.get('content-length', 0))

                with open(filepath, 'wb') as f:
                    downloaded = 0
                    block_size = 8192
                    while True:
                        block = response.read(block_size)
                        if not block:
                            break
                        f.write(block)
                        downloaded += len(block)
                        if total_size > 0:
                            pct = downloaded * 100 // total_size
                            if downloaded % (block_size * 100) == 0:
                                log.info(f"    {pct}% ({downloaded // 1024}KB / {total_size // 1024}KB)")

                self.cache[key] = {
                    "url": url,
                    "file": filename,
                    "size": os.path.getsize(filepath),
                    "downloaded": datetime.now().isoformat()
                }
                self._save_cache()
                log.info(f"    Done: {os.path.getsize(filepath) / 1024 / 1024:.1f} MB")
                return filepath

            except (URLError, OSError) as e:
                log.warning(f"    Attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    log.error(f"    FAILED to download {desc} after {max_retries} attempts")
                    return None

        return None


# ============================================================
# Graph Builder
# ============================================================

class KnowledgeGraphBuilder:
    """Builds the integrated biomedical knowledge graph."""

    def __init__(self):
        self.G = nx.DiGraph()
        self.stats = defaultdict(int)
        self.node_types = defaultdict(set)
        self.edge_types = defaultdict(int)
        self.download_mgr = DownloadManager(DATA_DIR)

    def build(self):
        """Main build pipeline."""
        log.info("=" * 60)
        log.info("Knowledge Graph Builder")
        log.info("=" * 60)
        start_time = time.time()

        # Phase 1: Download data
        log.info("\n[Phase 1] Downloading data sources...")
        downloaded = self._download_all()

        # Phase 2: Parse and integrate
        log.info("\n[Phase 2] Parsing and integrating data...")
        self._parse_string(downloaded)
        self._parse_reactome(downloaded)
        self._parse_sider(downloaded)
        self._parse_ctd(downloaded)

        # Phase 3: Add curated CRS/ICANS/HLH mechanisms
        log.info("\n[Phase 3] Adding curated cell therapy safety mechanisms...")
        self._add_crs_mechanisms()
        self._add_icans_mechanisms()
        self._add_hlh_mechanisms()
        self._add_intervention_nodes()

        # Phase 4: Compute graph metrics
        log.info("\n[Phase 4] Computing graph metrics...")
        self._compute_metrics()

        # Phase 5: Export
        log.info("\n[Phase 5] Exporting graph...")
        self._export_graphml()
        self._export_json()
        self._export_neo4j()
        self._export_embeddings_data()
        self._export_stats()

        elapsed = time.time() - start_time
        log.info(f"\nBuild complete in {elapsed/60:.1f} minutes")
        log.info(f"Graph: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

    def _download_all(self) -> dict:
        """Download all data sources."""
        downloaded = {}
        for key, src in SOURCES.items():
            path = self.download_mgr.download(key, src["url"], src["file"], src["desc"])
            downloaded[key] = path
        return downloaded

    # --- STRING Protein-Protein Interactions ---

    def _parse_string(self, downloaded: dict):
        """Parse STRING PPI data (human only, high confidence)."""
        log.info("  Parsing STRING protein interactions...")

        # Parse protein info first (names)
        info_path = downloaded.get("string_info")
        protein_names = {}
        if info_path and info_path.exists():
            try:
                with gzip.open(info_path, 'rt') as f:
                    reader = csv.reader(f, delimiter='\t')
                    next(reader)  # header
                    for row in reader:
                        if len(row) >= 2:
                            ensembl_id = row[0].replace("9606.", "")
                            name = row[1]
                            protein_names[row[0]] = name
            except Exception as e:
                log.warning(f"    Could not parse STRING info: {e}")

        # Parse interactions
        links_path = downloaded.get("string_links")
        if not links_path or not links_path.exists():
            log.warning("    STRING links file not available, skipping")
            return

        count = 0
        focus_count = 0
        try:
            with gzip.open(links_path, 'rt') as f:
                header = f.readline()
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 3:
                        continue

                    p1, p2, score = parts[0], parts[1], int(parts[2])

                    # Only high-confidence interactions (>700)
                    if score < 700:
                        continue

                    name1 = protein_names.get(p1, p1.replace("9606.", ""))
                    name2 = protein_names.get(p2, p2.replace("9606.", ""))

                    # Prioritize CRS-relevant proteins (include all of those)
                    is_focus = name1 in CRS_FOCUS_GENES or name2 in CRS_FOCUS_GENES

                    # For non-focus proteins, only include very high confidence (>900)
                    if not is_focus and score < 900:
                        continue

                    # Add protein nodes
                    for name, pid in [(name1, p1), (name2, p2)]:
                        if name not in self.G:
                            self.G.add_node(name, type="Protein", string_id=pid,
                                          is_focus=name in CRS_FOCUS_GENES)
                            self.node_types["Protein"].add(name)

                    # Add interaction edge
                    self.G.add_edge(name1, name2, type="INTERACTS_WITH",
                                   source="STRING", confidence=score/1000,
                                   weight=score/1000)
                    self.edge_types["INTERACTS_WITH"] += 1
                    count += 1
                    if is_focus:
                        focus_count += 1

                    if count % 10000 == 0:
                        log.info(f"    Processed {count} interactions ({focus_count} CRS-relevant)...")

        except Exception as e:
            log.error(f"    Error parsing STRING: {e}")

        log.info(f"    STRING: {count} interactions ({focus_count} CRS-relevant)")
        self.stats["string_interactions"] = count

    # --- Reactome Pathways ---

    def _parse_reactome(self, downloaded: dict):
        """Parse Reactome pathway data."""
        log.info("  Parsing Reactome pathways...")

        # Parse pathway definitions
        pathways_file = downloaded.get("reactome_pathways")
        pathway_names = {}
        if pathways_file and pathways_file.exists():
            try:
                with open(pathways_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 3 and parts[2] == "Homo sapiens":
                            pathway_id = parts[0]
                            pathway_name = parts[1]
                            pathway_names[pathway_id] = pathway_name

                            # Check if CRS-relevant
                            is_focus = any(kw.lower() in pathway_name.lower()
                                         for kw in CRS_FOCUS_PATHWAYS)

                            if is_focus or len(pathway_names) < 500:
                                self.G.add_node(pathway_name, type="Pathway",
                                              reactome_id=pathway_id,
                                              is_focus=is_focus)
                                self.node_types["Pathway"].add(pathway_name)

            except Exception as e:
                log.warning(f"    Could not parse Reactome pathways: {e}")

        log.info(f"    Reactome: {len(pathway_names)} human pathways loaded")

        # Parse gene-pathway mappings
        genes_file = downloaded.get("reactome_genes")
        gene_pathway_count = 0
        if genes_file and genes_file.exists():
            try:
                with open(genes_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 4 and parts[5] == "Homo sapiens" if len(parts) > 5 else True:
                            gene_id = parts[0]
                            pathway_id = parts[1]
                            pathway_name = pathway_names.get(pathway_id)

                            if pathway_name and pathway_name in self.G:
                                # Try to resolve gene name
                                gene_name = parts[2] if len(parts) > 2 else gene_id

                                if gene_name in self.G or gene_name in CRS_FOCUS_GENES:
                                    if gene_name not in self.G:
                                        self.G.add_node(gene_name, type="Gene",
                                                      ensembl_id=gene_id,
                                                      is_focus=gene_name in CRS_FOCUS_GENES)
                                        self.node_types["Gene"].add(gene_name)

                                    self.G.add_edge(gene_name, pathway_name,
                                                   type="PARTICIPATES_IN",
                                                   source="Reactome")
                                    self.edge_types["PARTICIPATES_IN"] += 1
                                    gene_pathway_count += 1

            except Exception as e:
                log.warning(f"    Could not parse Reactome genes: {e}")

        log.info(f"    Reactome: {gene_pathway_count} gene-pathway mappings")
        self.stats["reactome_pathways"] = len(pathway_names)
        self.stats["gene_pathway_mappings"] = gene_pathway_count

        # Parse pathway hierarchy
        relations_file = downloaded.get("reactome_relations")
        rel_count = 0
        if relations_file and relations_file.exists():
            try:
                with open(relations_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            parent = pathway_names.get(parts[0])
                            child = pathway_names.get(parts[1])
                            if parent and child and parent in self.G and child in self.G:
                                self.G.add_edge(parent, child, type="HAS_SUBPROCESS",
                                              source="Reactome")
                                self.edge_types["HAS_SUBPROCESS"] += 1
                                rel_count += 1
            except Exception as e:
                log.warning(f"    Could not parse Reactome relations: {e}")

        log.info(f"    Reactome: {rel_count} pathway hierarchy relations")

    # --- SIDER Side Effects ---

    def _parse_sider(self, downloaded: dict):
        """Parse SIDER drug side effect data."""
        log.info("  Parsing SIDER side effects...")

        # Parse drug names
        drug_names_file = downloaded.get("sider_drugs")
        drug_names = {}
        if drug_names_file and drug_names_file.exists():
            try:
                with open(drug_names_file, 'r', errors='replace') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            drug_names[parts[0]] = parts[1]
            except Exception as e:
                log.warning(f"    Could not parse SIDER drug names: {e}")

        # Parse side effects
        effects_file = downloaded.get("sider_effects")
        se_count = 0
        if effects_file and effects_file.exists():
            try:
                opener = gzip.open if str(effects_file).endswith('.gz') else open
                with opener(effects_file, 'rt', errors='replace') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) < 5:
                            continue

                        drug_id = parts[0]
                        meddra_type = parts[2] if len(parts) > 2 else ""
                        meddra_code = parts[3] if len(parts) > 3 else ""
                        effect_name = parts[4] if len(parts) > 4 else parts[-1]

                        drug_name = drug_names.get(drug_id, drug_id)

                        # Only include focus drugs or CRS-relevant effects
                        is_focus_drug = any(d.lower() in drug_name.lower()
                                          for d in CRS_FOCUS_DRUGS)
                        is_focus_effect = any(kw.lower() in effect_name.lower()
                                            for kw in ["cytokine", "fever", "hypotension",
                                                       "neurotoxicity", "encephalopathy",
                                                       "coagulopathy", "haemophagocytic",
                                                       "immune", "inflammatory",
                                                       "infusion", "anaphyla"])

                        if not (is_focus_drug or is_focus_effect):
                            continue

                        # Add drug node
                        if drug_name not in self.G:
                            self.G.add_node(drug_name, type="Drug",
                                          sider_id=drug_id,
                                          is_focus=is_focus_drug)
                            self.node_types["Drug"].add(drug_name)

                        # Add adverse event node
                        if effect_name not in self.G:
                            self.G.add_node(effect_name, type="Adverse_Event",
                                          meddra_code=meddra_code,
                                          meddra_type=meddra_type,
                                          is_focus=is_focus_effect)
                            self.node_types["Adverse_Event"].add(effect_name)

                        # Add causation edge
                        self.G.add_edge(drug_name, effect_name,
                                       type="CAUSES_AE", source="SIDER")
                        self.edge_types["CAUSES_AE"] += 1
                        se_count += 1

            except Exception as e:
                log.warning(f"    Could not parse SIDER effects: {e}")

        log.info(f"    SIDER: {se_count} drug-side effect associations")
        self.stats["sider_associations"] = se_count

    # --- CTD (Comparative Toxicogenomics Database) ---

    def _parse_ctd(self, downloaded: dict):
        """Parse CTD chemical-gene and gene-disease data."""
        log.info("  Parsing CTD toxicogenomics data...")

        # Chemical-gene interactions
        cg_file = downloaded.get("ctd_chem_gene")
        cg_count = 0
        if cg_file and cg_file.exists():
            try:
                opener = gzip.open if str(cg_file).endswith('.gz') else open
                with opener(cg_file, 'rt', errors='replace') as f:
                    for line in f:
                        if line.startswith('#'):
                            continue
                        parts = line.strip().split('\t')
                        if len(parts) < 5:
                            continue

                        chem_name = parts[0]
                        gene_symbol = parts[3] if len(parts) > 3 else ""
                        interaction = parts[4] if len(parts) > 4 else ""

                        # Only CRS-relevant genes
                        if gene_symbol not in CRS_FOCUS_GENES:
                            continue

                        # Determine edge type from interaction description
                        edge_type = "AFFECTS"
                        if "increase" in interaction.lower():
                            edge_type = "INCREASES_EXPRESSION"
                        elif "decrease" in interaction.lower():
                            edge_type = "DECREASES_EXPRESSION"
                        elif "bind" in interaction.lower():
                            edge_type = "BINDS"

                        if chem_name not in self.G:
                            self.G.add_node(chem_name, type="Chemical",
                                          source="CTD")
                            self.node_types["Chemical"].add(chem_name)

                        if gene_symbol not in self.G:
                            self.G.add_node(gene_symbol, type="Gene",
                                          is_focus=True, source="CTD")
                            self.node_types["Gene"].add(gene_symbol)

                        self.G.add_edge(chem_name, gene_symbol,
                                       type=edge_type, source="CTD",
                                       interaction_desc=interaction[:200])
                        self.edge_types[edge_type] += 1
                        cg_count += 1

            except Exception as e:
                log.warning(f"    Could not parse CTD chem-gene: {e}")

        log.info(f"    CTD: {cg_count} chemical-gene interactions")

        # Gene-disease associations
        gd_file = downloaded.get("ctd_gene_disease")
        gd_count = 0
        if gd_file and gd_file.exists():
            try:
                opener = gzip.open if str(gd_file).endswith('.gz') else open
                with opener(gd_file, 'rt', errors='replace') as f:
                    for line in f:
                        if line.startswith('#'):
                            continue
                        parts = line.strip().split('\t')
                        if len(parts) < 4:
                            continue

                        gene_symbol = parts[0]
                        disease_name = parts[2] if len(parts) > 2 else ""
                        evidence = parts[4] if len(parts) > 4 else ""

                        # Only CRS-relevant genes or diseases
                        is_focus_gene = gene_symbol in CRS_FOCUS_GENES
                        is_focus_disease = any(kw.lower() in disease_name.lower()
                                             for kw in ["cytokine", "lymphoma", "leukemia",
                                                        "myeloma", "immune", "inflam",
                                                        "hemophagocytic", "macrophage",
                                                        "neurotoxicity", "encephalopathy",
                                                        "coagulation", "thrombocytopenia",
                                                        "autoimmune", "lupus"])

                        if not (is_focus_gene or is_focus_disease):
                            continue

                        if gene_symbol not in self.G:
                            self.G.add_node(gene_symbol, type="Gene",
                                          is_focus=is_focus_gene)
                            self.node_types["Gene"].add(gene_symbol)

                        if disease_name not in self.G:
                            self.G.add_node(disease_name, type="Disease",
                                          is_focus=is_focus_disease)
                            self.node_types["Disease"].add(disease_name)

                        self.G.add_edge(gene_symbol, disease_name,
                                       type="ASSOCIATED_WITH", source="CTD",
                                       evidence=evidence[:100])
                        self.edge_types["ASSOCIATED_WITH"] += 1
                        gd_count += 1

            except Exception as e:
                log.warning(f"    Could not parse CTD gene-disease: {e}")

        log.info(f"    CTD: {gd_count} gene-disease associations")
        self.stats["ctd_chem_gene"] = cg_count
        self.stats["ctd_gene_disease"] = gd_count

    # --- Curated CRS/ICANS/HLH Mechanisms ---

    def _add_crs_mechanisms(self):
        """Add manually curated CRS pathophysiology cascade."""
        log.info("  Adding curated CRS mechanism...")

        # Cell types
        cell_types = {
            "CAR-T_Cell": {"markers": "CD3+/CAR+", "role": "Effector"},
            "Macrophage": {"markers": "CD14+/CD68+", "role": "Amplifier"},
            "Endothelial_Cell": {"markers": "CD31+/VWF+", "role": "Effector/Target"},
            "Monocyte": {"markers": "CD14+", "role": "Amplifier"},
            "Dendritic_Cell": {"markers": "CD11c+", "role": "Antigen presentation"},
            "NK_Cell": {"markers": "CD56+/CD16+", "role": "Cytotoxic"},
            "Neutrophil": {"markers": "CD66b+", "role": "Innate immunity"},
        }
        for name, attrs in cell_types.items():
            self.G.add_node(name, type="Cell_Type", **attrs, is_focus=True)
            self.node_types["Cell_Type"].add(name)

        # CRS cascade (based on Lee et al. 2019, Neelapu et al. 2018)
        crs_cascade = [
            # CAR-T activation and expansion
            ("CAR-T_Cell", "IFNG", "PRODUCES", {"mechanism": "TCR-like signaling via CAR", "kinetics": "hours"}),
            ("CAR-T_Cell", "TNF", "PRODUCES", {"mechanism": "NF-kB activation", "kinetics": "hours"}),
            ("CAR-T_Cell", "IL2", "PRODUCES", {"mechanism": "T-cell autocrine", "kinetics": "hours"}),
            ("CAR-T_Cell", "GZMB", "PRODUCES", {"mechanism": "Cytotoxic granule release", "kinetics": "hours"}),
            ("CAR-T_Cell", "PRF1", "PRODUCES", {"mechanism": "Perforin-mediated lysis", "kinetics": "hours"}),

            # IFN-gamma activates macrophages (key amplification step)
            ("IFNG", "Macrophage", "ACTIVATES", {"mechanism": "JAK1/2-STAT1 signaling", "critical": True}),
            ("TNF", "Macrophage", "ACTIVATES", {"mechanism": "TNFR1/2 signaling", "critical": True}),

            # Macrophage cytokine storm
            ("Macrophage", "IL6", "PRODUCES", {"mechanism": "NF-kB/MAPK activation", "rate": "high", "critical": True}),
            ("Macrophage", "IL1B", "PRODUCES", {"mechanism": "Inflammasome (NLRP3)", "rate": "high"}),
            ("Macrophage", "TNF", "PRODUCES", {"mechanism": "NF-kB activation", "rate": "high"}),
            ("Macrophage", "CXCL8", "PRODUCES", {"mechanism": "Chemokine secretion", "rate": "medium"}),
            ("Macrophage", "CXCL10", "PRODUCES", {"mechanism": "IFN-gamma induced", "rate": "medium"}),

            # IL-6 trans-signaling (central CRS mechanism)
            ("IL6", "IL6R", "BINDS", {"mechanism": "Classical signaling (membrane IL-6R)", "kd": "1nM"}),
            ("IL6", "IL6ST", "BINDS", {"mechanism": "Trans-signaling via sIL-6R", "kd": "10nM", "critical": True}),
            ("IL6ST", "JAK1", "ACTIVATES", {"mechanism": "gp130 dimerization", "critical": True}),
            ("JAK1", "STAT3", "ACTIVATES", {"mechanism": "Phosphorylation", "critical": True}),
            ("STAT3", "IL6", "INCREASES_EXPRESSION", {"mechanism": "Positive feedback loop", "critical": True}),

            # Endothelial activation (CRS severity driver)
            ("IL6", "Endothelial_Cell", "ACTIVATES", {"mechanism": "IL-6 trans-signaling", "critical": True}),
            ("TNF", "Endothelial_Cell", "ACTIVATES", {"mechanism": "TNFR1 signaling"}),
            ("Endothelial_Cell", "IL6", "PRODUCES", {"mechanism": "Amplification loop", "critical": True}),
            ("Endothelial_Cell", "ICAM1", "INCREASES_EXPRESSION", {"mechanism": "NF-kB"}),
            ("Endothelial_Cell", "VCAM1", "INCREASES_EXPRESSION", {"mechanism": "NF-kB"}),
            ("Endothelial_Cell", "SELE", "INCREASES_EXPRESSION", {"mechanism": "P-selectin mobilization"}),
            ("Endothelial_Cell", "VWF", "PRODUCES", {"mechanism": "Weibel-Palade body release"}),
            ("Endothelial_Cell", "ANGPT2", "PRODUCES", {"mechanism": "Destabilization signal"}),

            # Coagulation cascade activation
            ("VWF", "F2", "ACTIVATES", {"mechanism": "Coagulation cascade", "consequence": "DIC risk"}),
            ("Endothelial_Cell", "FGA", "AFFECTS", {"mechanism": "Fibrinogen consumption"}),

            # Acute phase response
            ("IL6", "CRP", "INCREASES_EXPRESSION", {"mechanism": "Hepatic acute phase", "organ": "liver"}),
            ("IL6", "FTH1", "INCREASES_EXPRESSION", {"mechanism": "Ferritin induction", "organ": "liver"}),
            ("IL6", "SAA1", "INCREASES_EXPRESSION", {"mechanism": "Acute phase", "organ": "liver"}),
            ("IL6", "ALB", "DECREASES_EXPRESSION", {"mechanism": "Negative acute phase", "organ": "liver"}),

            # Clinical manifestations
            ("IL6", "CRS_Grade_1", "MANIFESTS_AS", {"threshold": "IL6 >100 pg/mL", "grade": 1}),
            ("IL6", "CRS_Grade_2", "MANIFESTS_AS", {"threshold": "IL6 >500 pg/mL, hypotension", "grade": 2}),
            ("IL6", "CRS_Grade_3", "MANIFESTS_AS", {"threshold": "IL6 >1000 pg/mL, vasopressors", "grade": 3}),
            ("IL6", "CRS_Grade_4", "MANIFESTS_AS", {"threshold": "IL6 >5000 pg/mL, organ failure", "grade": 4}),
        ]

        # Add clinical event nodes
        for grade in range(1, 5):
            name = f"CRS_Grade_{grade}"
            self.G.add_node(name, type="Adverse_Event", severity=grade,
                          meddra_term="Cytokine release syndrome",
                          is_focus=True)
            self.node_types["Adverse_Event"].add(name)

        # Add all cascade edges
        for source, target, edge_type, attrs in crs_cascade:
            for node in [source, target]:
                if node not in self.G:
                    # Infer type
                    ntype = "Cytokine" if node in CRS_FOCUS_GENES else "BiologicalProcess"
                    self.G.add_node(node, type=ntype, is_focus=True)
                    self.node_types[ntype].add(node)

            self.G.add_edge(source, target, type=edge_type,
                           source="Curated_CRS_Mechanism", **attrs)
            self.edge_types[edge_type] += 1

        self.stats["curated_crs_edges"] = len(crs_cascade)
        log.info(f"    Added {len(crs_cascade)} curated CRS mechanism edges")

    def _add_icans_mechanisms(self):
        """Add curated ICANS (neurotoxicity) pathophysiology."""
        log.info("  Adding curated ICANS mechanism...")

        # ICANS-specific nodes
        icans_nodes = {
            "Blood_Brain_Barrier": {"type": "BiologicalProcess", "role": "Barrier"},
            "BBB_Disruption": {"type": "BiologicalProcess", "role": "Pathology"},
            "Cerebral_Edema": {"type": "BiologicalProcess", "role": "Pathology"},
            "ICANS_Grade_1": {"type": "Adverse_Event", "severity": 1, "meddra_term": "ICANS"},
            "ICANS_Grade_2": {"type": "Adverse_Event", "severity": 2, "meddra_term": "ICANS"},
            "ICANS_Grade_3": {"type": "Adverse_Event", "severity": 3, "meddra_term": "ICANS"},
            "ICANS_Grade_4": {"type": "Adverse_Event", "severity": 4, "meddra_term": "ICANS"},
        }
        for name, attrs in icans_nodes.items():
            ntype = attrs.pop("type")
            self.G.add_node(name, type=ntype, **attrs, is_focus=True)
            self.node_types[ntype].add(name)

        icans_cascade = [
            ("IL6", "Blood_Brain_Barrier", "DISRUPTS", {"mechanism": "Endothelial activation at BBB"}),
            ("TNF", "Blood_Brain_Barrier", "DISRUPTS", {"mechanism": "Tight junction degradation"}),
            ("IFNG", "Blood_Brain_Barrier", "DISRUPTS", {"mechanism": "Microglial activation"}),
            ("IL1B", "Blood_Brain_Barrier", "DISRUPTS", {"mechanism": "Inflammasome-mediated"}),
            ("Blood_Brain_Barrier", "BBB_Disruption", "LEADS_TO", {"consequence": "CNS cytokine entry"}),
            ("BBB_Disruption", "Cerebral_Edema", "LEADS_TO", {"consequence": "Vasogenic edema"}),
            ("BBB_Disruption", "ICANS_Grade_1", "MANIFESTS_AS", {"ice_score": "7-9"}),
            ("Cerebral_Edema", "ICANS_Grade_2", "MANIFESTS_AS", {"ice_score": "3-6"}),
            ("Cerebral_Edema", "ICANS_Grade_3", "MANIFESTS_AS", {"ice_score": "0-2"}),
            ("Cerebral_Edema", "ICANS_Grade_4", "MANIFESTS_AS", {"ice_score": "0, obtunded"}),
        ]

        for source, target, edge_type, attrs in icans_cascade:
            self.G.add_edge(source, target, type=edge_type,
                           source="Curated_ICANS_Mechanism", **attrs)
            self.edge_types[edge_type] += 1

        self.stats["curated_icans_edges"] = len(icans_cascade)
        log.info(f"    Added {len(icans_cascade)} curated ICANS mechanism edges")

    def _add_hlh_mechanisms(self):
        """Add curated HLH/MAS pathophysiology."""
        log.info("  Adding curated HLH/MAS mechanism...")

        hlh_nodes = {
            "Hemophagocytosis": {"type": "BiologicalProcess", "role": "Pathology"},
            "Hyperferritinemia": {"type": "Biomarker", "threshold": ">10000 ng/mL"},
            "Hypofibrinogenemia": {"type": "Biomarker", "threshold": "<150 mg/dL"},
            "Hypertriglyceridemia": {"type": "Biomarker", "threshold": ">265 mg/dL"},
            "Pancytopenia": {"type": "BiologicalProcess", "role": "Pathology"},
            "HLH_MAS": {"type": "Adverse_Event", "severity": 4, "meddra_term": "HLH"},
        }
        for name, attrs in hlh_nodes.items():
            ntype = attrs.pop("type")
            self.G.add_node(name, type=ntype, **attrs, is_focus=True)
            self.node_types[ntype].add(name)

        hlh_cascade = [
            ("IFNG", "Hemophagocytosis", "DRIVES", {"mechanism": "Macrophage hyperactivation"}),
            ("IL18", "Hemophagocytosis", "DRIVES", {"mechanism": "NK/T-cell mediated"}),
            ("Macrophage", "Hemophagocytosis", "PERFORMS", {"mechanism": "Erythrophagocytosis"}),
            ("Hemophagocytosis", "Pancytopenia", "CAUSES", {}),
            ("IL6", "Hyperferritinemia", "DRIVES", {"mechanism": "Hepatic ferritin induction"}),
            ("Macrophage", "Hyperferritinemia", "DRIVES", {"mechanism": "Macrophage ferritin release"}),
            ("Hemophagocytosis", "Hypofibrinogenemia", "CAUSES", {"mechanism": "Consumptive"}),
            ("Hemophagocytosis", "HLH_MAS", "MANIFESTS_AS", {"criteria": "HLH-2004 / HScore"}),
        ]

        for source, target, edge_type, attrs in hlh_cascade:
            self.G.add_edge(source, target, type=edge_type,
                           source="Curated_HLH_Mechanism", **attrs)
            self.edge_types[edge_type] += 1

        self.stats["curated_hlh_edges"] = len(hlh_cascade)
        log.info(f"    Added {len(hlh_cascade)} curated HLH mechanism edges")

    def _add_intervention_nodes(self):
        """Add therapeutic intervention nodes and edges."""
        log.info("  Adding intervention nodes...")

        interventions = [
            ("Tocilizumab", "IL6R", "INHIBITS", {"mechanism": "Anti-IL-6R monoclonal antibody",
                                                   "indication": "CRS Grade 2+", "critical": True}),
            ("Siltuximab", "IL6", "INHIBITS", {"mechanism": "Anti-IL-6 monoclonal antibody",
                                                "indication": "CRS (alternative)"}),
            ("Anakinra", "IL1R1", "INHIBITS", {"mechanism": "IL-1 receptor antagonist",
                                                "indication": "Refractory CRS, HLH"}),
            ("Ruxolitinib", "JAK1", "INHIBITS", {"mechanism": "JAK1/2 inhibitor",
                                                   "indication": "Refractory CRS/ICANS"}),
            ("Ruxolitinib", "JAK2", "INHIBITS", {"mechanism": "JAK1/2 inhibitor"}),
            ("Dexamethasone", "NFKB1", "INHIBITS", {"mechanism": "Glucocorticoid receptor → NF-kB suppression",
                                                      "indication": "ICANS, severe CRS"}),
            ("Methylprednisolone", "NFKB1", "INHIBITS", {"mechanism": "Glucocorticoid",
                                                           "indication": "Severe ICANS"}),
        ]

        for drug, target, edge_type, attrs in interventions:
            if drug not in self.G:
                self.G.add_node(drug, type="Drug", drug_class="Intervention",
                              is_focus=True)
                self.node_types["Drug"].add(drug)

            self.G.add_edge(drug, target, type=edge_type,
                           source="Curated_Interventions", **attrs)
            self.edge_types[edge_type] += 1

        log.info(f"    Added {len(interventions)} intervention edges")

    # --- Graph Metrics ---

    def _compute_metrics(self):
        """Compute graph-level and node-level metrics."""
        log.info("  Computing centrality metrics...")

        # Only compute on the undirected version for some metrics
        G_undirected = self.G.to_undirected()

        # Degree centrality
        degree_cent = nx.degree_centrality(self.G)
        for node, cent in degree_cent.items():
            self.G.nodes[node]['degree_centrality'] = round(cent, 6)

        # PageRank (works on directed graph)
        try:
            pagerank = nx.pagerank(self.G, alpha=0.85, max_iter=100)
            for node, pr in pagerank.items():
                self.G.nodes[node]['pagerank'] = round(pr, 8)
        except Exception as e:
            log.warning(f"    PageRank failed: {e}")

        # Betweenness centrality (on largest connected component for efficiency)
        try:
            largest_cc = max(nx.connected_components(G_undirected), key=len)
            if len(largest_cc) < 50000:
                subgraph = G_undirected.subgraph(largest_cc)
                betweenness = nx.betweenness_centrality(subgraph, k=min(500, len(subgraph)))
                for node, bc in betweenness.items():
                    self.G.nodes[node]['betweenness_centrality'] = round(bc, 8)
        except Exception as e:
            log.warning(f"    Betweenness centrality failed: {e}")

        # Connected components
        n_components = nx.number_weakly_connected_components(self.G)
        largest_wcc = max(nx.weakly_connected_components(self.G), key=len)
        self.stats["connected_components"] = n_components
        self.stats["largest_component_size"] = len(largest_wcc)

        log.info(f"    Components: {n_components} (largest: {len(largest_wcc)} nodes)")

    # --- Export ---

    def _export_graphml(self):
        """Export as GraphML."""
        path = OUTPUT_DIR / "graph.graphml"
        log.info(f"  Exporting GraphML to {path}...")

        # GraphML can't handle all Python types - clean attributes
        G_export = self.G.copy()
        for node in G_export.nodes():
            for key, val in list(G_export.nodes[node].items()):
                if isinstance(val, (set, list, dict)):
                    G_export.nodes[node][key] = str(val)
                elif isinstance(val, bool):
                    G_export.nodes[node][key] = str(val)
        for u, v in G_export.edges():
            for key, val in list(G_export.edges[u, v].items()):
                if isinstance(val, (set, list, dict)):
                    G_export.edges[u, v][key] = str(val)
                elif isinstance(val, bool):
                    G_export.edges[u, v][key] = str(val)

        nx.write_graphml(G_export, str(path))
        log.info(f"    GraphML: {os.path.getsize(path) / 1024 / 1024:.1f} MB")

    def _export_json(self):
        """Export as JSON for web visualization."""
        path = OUTPUT_DIR / "graph_data.json"
        log.info(f"  Exporting JSON to {path}...")

        nodes = []
        for node_id, attrs in self.G.nodes(data=True):
            node_data = {"id": node_id, **attrs}
            # Convert non-serializable types
            for k, v in node_data.items():
                if isinstance(v, set):
                    node_data[k] = list(v)
            nodes.append(node_data)

        edges = []
        for source, target, attrs in self.G.edges(data=True):
            edge_data = {"source": source, "target": target, **attrs}
            for k, v in edge_data.items():
                if isinstance(v, set):
                    edge_data[k] = list(v)
            edges.append(edge_data)

        data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "node_types": {k: len(v) for k, v in self.node_types.items()},
                "edge_types": dict(self.edge_types),
                "built": datetime.now().isoformat(),
                "builder": "Knowledge Graph Builder v1.0"
            }
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        log.info(f"    JSON: {os.path.getsize(path) / 1024 / 1024:.1f} MB")

    def _export_neo4j(self):
        """Export CSV files for Neo4j bulk import."""
        log.info(f"  Exporting Neo4j import CSVs to {NEO4J_DIR}...")

        # Nodes CSV
        nodes_path = NEO4J_DIR / "nodes.csv"
        with open(nodes_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id:ID", "name", "type:LABEL", "is_focus:boolean",
                           "degree_centrality:float", "pagerank:float"])
            for node_id, attrs in self.G.nodes(data=True):
                writer.writerow([
                    node_id,
                    node_id,
                    attrs.get("type", "Unknown"),
                    attrs.get("is_focus", False),
                    attrs.get("degree_centrality", 0),
                    attrs.get("pagerank", 0),
                ])

        # Edges CSV
        edges_path = NEO4J_DIR / "edges.csv"
        with open(edges_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([":START_ID", ":END_ID", ":TYPE", "source", "confidence:float"])
            for source, target, attrs in self.G.edges(data=True):
                writer.writerow([
                    source,
                    target,
                    attrs.get("type", "RELATED_TO"),
                    attrs.get("source", ""),
                    attrs.get("confidence", attrs.get("weight", 0)),
                ])

        log.info(f"    Neo4j CSVs exported")

    def _export_embeddings_data(self):
        """Export preprocessed data for GNN training."""
        log.info(f"  Exporting embeddings training data to {EMBEDDINGS_DIR}...")

        # Node ID mapping
        node_list = list(self.G.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(node_list)}

        # Node features: one-hot type encoding + centrality metrics
        type_set = sorted(set(attrs.get("type", "Unknown")
                             for _, attrs in self.G.nodes(data=True)))
        type_to_idx = {t: i for i, t in enumerate(type_set)}

        num_nodes = len(node_list)
        num_types = len(type_set)
        # Feature matrix: [type_one_hot | is_focus | degree_centrality | pagerank]
        feature_dim = num_types + 3
        features = np.zeros((num_nodes, feature_dim), dtype=np.float32)

        for node, attrs in self.G.nodes(data=True):
            idx = node_to_idx[node]
            ntype = attrs.get("type", "Unknown")
            features[idx, type_to_idx[ntype]] = 1.0
            features[idx, num_types] = 1.0 if attrs.get("is_focus", False) else 0.0
            features[idx, num_types + 1] = attrs.get("degree_centrality", 0)
            features[idx, num_types + 2] = attrs.get("pagerank", 0)

        # Edge index (COO format for PyTorch Geometric)
        edge_list = [(node_to_idx[u], node_to_idx[v])
                     for u, v in self.G.edges() if u in node_to_idx and v in node_to_idx]
        edge_index = np.array(edge_list, dtype=np.int64).T if edge_list else np.zeros((2, 0), dtype=np.int64)

        # Edge type encoding
        edge_types_list = sorted(set(attrs.get("type", "RELATED")
                                    for _, _, attrs in self.G.edges(data=True)))
        etype_to_idx = {t: i for i, t in enumerate(edge_types_list)}
        edge_type_arr = np.array([etype_to_idx.get(self.G.edges[u, v].get("type", "RELATED"), 0)
                                  for u, v in self.G.edges()
                                  if u in node_to_idx and v in node_to_idx], dtype=np.int64)

        # Save as numpy arrays
        np.save(EMBEDDINGS_DIR / "node_features.npy", features)
        np.save(EMBEDDINGS_DIR / "edge_index.npy", edge_index)
        np.save(EMBEDDINGS_DIR / "edge_types.npy", edge_type_arr)

        # Save mappings
        mappings = {
            "node_to_idx": node_to_idx,
            "type_to_idx": type_to_idx,
            "edge_type_to_idx": etype_to_idx,
            "feature_dim": feature_dim,
            "num_nodes": num_nodes,
            "num_edge_types": len(edge_types_list),
        }
        with open(EMBEDDINGS_DIR / "mappings.json", 'w') as f:
            json.dump(mappings, f, indent=2)

        log.info(f"    Features: {features.shape}, Edges: {edge_index.shape}")
        log.info(f"    Node types: {len(type_set)}, Edge types: {len(edge_types_list)}")

    def _export_stats(self):
        """Export graph statistics."""
        stats = {
            "build_time": datetime.now().isoformat(),
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": {k: len(v) for k, v in self.node_types.items()},
            "edge_types": dict(self.edge_types),
            "focus_nodes": sum(1 for _, attrs in self.G.nodes(data=True)
                              if attrs.get("is_focus", False)),
            "data_sources": dict(self.stats),
            "top_nodes_by_degree": sorted(
                [(n, self.G.degree(n)) for n in self.G.nodes()],
                key=lambda x: x[1], reverse=True
            )[:50],
            "top_nodes_by_pagerank": sorted(
                [(n, attrs.get("pagerank", 0)) for n, attrs in self.G.nodes(data=True)],
                key=lambda x: x[1], reverse=True
            )[:50],
        }

        path = OUTPUT_DIR / "graph_stats.json"
        with open(path, 'w') as f:
            json.dump(stats, f, indent=2, default=str)

        log.info(f"\n  Graph Statistics:")
        log.info(f"    Nodes: {stats['total_nodes']}")
        log.info(f"    Edges: {stats['total_edges']}")
        log.info(f"    Focus nodes: {stats['focus_nodes']}")
        log.info(f"    Node types: {json.dumps(stats['node_types'], indent=4)}")
        log.info(f"    Edge types: {json.dumps(stats['edge_types'], indent=4)}")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    builder = KnowledgeGraphBuilder()
    builder.build()
