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
BASE_DIR = Path("/home/alton/safety-graph")
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
# Main HTML Template
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Biomedical Graph Explorer</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0a0e17;--card:#111827;--border:#1e293b;--text:#f1f5f9;
    --muted:#64748b;--blue:#3b82f6;--cyan:#06b6d4;--green:#10b981;
    --amber:#f59e0b;--red:#ef4444;--purple:#8b5cf6;
    --mono:'JetBrains Mono',monospace;--sans:'Inter',sans-serif;
  }
  html{font-size:14px}
  body{font-family:var(--sans);background:var(--bg);color:var(--text);overflow:hidden;height:100vh}

  .app{display:grid;grid-template-columns:280px 1fr 300px;grid-template-rows:50px 1fr;height:100vh}

  .header{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;
    padding:0 1rem;border-bottom:1px solid var(--border);background:var(--card)}
  .header h1{font-size:1rem;font-weight:700;letter-spacing:-0.3px}
  .header .stats{font-family:var(--mono);font-size:0.75rem;color:var(--muted)}

  .sidebar{border-right:1px solid var(--border);background:var(--card);overflow-y:auto;padding:0.8rem}
  .detail-panel{border-left:1px solid var(--border);background:var(--card);overflow-y:auto;padding:0.8rem}

  .graph-area{position:relative;overflow:hidden;background:var(--bg)}
  .graph-area svg{width:100%;height:100%}

  .search-box{width:100%;padding:0.5rem 0.7rem;background:var(--bg);border:1px solid var(--border);
    border-radius:6px;color:var(--text);font-family:var(--sans);font-size:0.8rem;outline:none;margin-bottom:0.8rem}
  .search-box:focus{border-color:var(--blue)}

  .section-title{font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;
    color:var(--muted);margin:0.8rem 0 0.4rem}

  .filter-chips{display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.6rem}
  .chip{padding:0.2rem 0.5rem;border-radius:4px;font-size:0.7rem;cursor:pointer;
    border:1px solid var(--border);color:var(--muted);transition:all 0.15s}
  .chip:hover{border-color:var(--blue);color:var(--text)}
  .chip.active{background:rgba(59,130,246,0.15);border-color:var(--blue);color:var(--blue)}

  .node-list{display:flex;flex-direction:column;gap:0.25rem}
  .node-item{padding:0.4rem 0.5rem;border-radius:4px;font-size:0.75rem;cursor:pointer;
    display:flex;align-items:center;gap:0.5rem;border:1px solid transparent}
  .node-item:hover{background:rgba(255,255,255,0.03);border-color:var(--border)}
  .node-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
  .node-name{font-family:var(--mono);font-size:0.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .node-type-tag{font-size:0.6rem;color:var(--muted);margin-left:auto}

  .pathway-btn{width:100%;padding:0.4rem;border-radius:4px;font-size:0.75rem;cursor:pointer;
    background:transparent;border:1px solid var(--border);color:var(--text);text-align:left;margin-bottom:0.3rem}
  .pathway-btn:hover{background:rgba(59,130,246,0.1);border-color:var(--blue)}

  .detail-title{font-size:0.9rem;font-weight:700;font-family:var(--mono);margin-bottom:0.5rem}
  .detail-row{display:flex;justify-content:space-between;font-size:0.75rem;padding:0.25rem 0;
    border-bottom:1px solid rgba(30,41,59,0.5)}
  .detail-label{color:var(--muted)}
  .detail-value{font-family:var(--mono);color:var(--text)}

  .neighbor-list{max-height:300px;overflow-y:auto}

  /* Graph node colors */
  .type-Protein{fill:var(--blue)}
  .type-Cytokine{fill:var(--amber)}
  .type-Gene{fill:var(--cyan)}
  .type-Drug{fill:var(--green)}
  .type-Pathway{fill:var(--purple)}
  .type-Disease{fill:var(--red)}
  .type-Adverse_Event{fill:var(--red)}
  .type-Cell_Type{fill:#ec4899}
  .type-BiologicalProcess{fill:#6366f1}
  .type-Biomarker{fill:#14b8a6}
  .type-Chemical{fill:#f97316}

  .link{stroke:rgba(100,116,139,0.3);stroke-width:1}
  .link.highlighted{stroke:var(--amber);stroke-width:2;opacity:1}
  .link.pathway{stroke:var(--red);stroke-width:2.5;opacity:1;stroke-dasharray:6 3}

  .node-label{font-size:9px;fill:var(--text);font-family:var(--mono);pointer-events:none;
    text-anchor:middle;dominant-baseline:central;opacity:0.8}
  .node-label.focus{font-weight:700;opacity:1;font-size:10px}

  .tooltip{position:absolute;background:var(--card);border:1px solid var(--border);
    padding:0.5rem 0.7rem;border-radius:6px;font-size:0.75rem;pointer-events:none;
    z-index:100;box-shadow:0 4px 12px rgba(0,0,0,0.3);max-width:250px}
  .tooltip .tt-title{font-weight:600;font-family:var(--mono);margin-bottom:0.2rem}
  .tooltip .tt-type{color:var(--muted);font-size:0.7rem}

  .legend{position:absolute;bottom:10px;left:10px;background:rgba(17,24,39,0.9);
    border:1px solid var(--border);border-radius:6px;padding:0.5rem 0.7rem;font-size:0.7rem}
  .legend-item{display:flex;align-items:center;gap:0.4rem;margin-bottom:0.2rem}
  .legend-dot{width:8px;height:8px;border-radius:50%}

  .zoom-controls{position:absolute;top:10px;right:10px;display:flex;flex-direction:column;gap:0.3rem}
  .zoom-btn{width:32px;height:32px;background:var(--card);border:1px solid var(--border);
    border-radius:4px;color:var(--text);font-size:1rem;cursor:pointer;display:flex;
    align-items:center;justify-content:center}
  .zoom-btn:hover{background:rgba(59,130,246,0.1);border-color:var(--blue)}

  .empty-state{color:var(--muted);font-size:0.8rem;text-align:center;padding:2rem 0}
</style>
</head>
<body>
<div class="app">
  <header class="header">
    <div style="display:flex;align-items:center;gap:0.8rem">
      <h1>Biomedical Graph Explorer</h1>
      <span class="stats" id="stats">Loading...</span>
    </div>
    <div class="stats">
      <span id="view-info">Force Layout</span>
    </div>
  </header>

  <div class="sidebar">
    <input type="text" class="search-box" id="search" placeholder="Search nodes..." autocomplete="off">

    <div class="section-title">Node Types</div>
    <div class="filter-chips" id="type-filters"></div>

    <div class="section-title">Pathways</div>
    <button class="pathway-btn" onclick="loadPathway('crs')">CRS Cascade</button>
    <button class="pathway-btn" onclick="loadPathway('icans')">ICANS / Neurotoxicity</button>
    <button class="pathway-btn" onclick="loadPathway('hlh')">HLH / MAS</button>
    <button class="pathway-btn" onclick="loadPathway('il6_cascade')">IL-6 Signaling</button>
    <button class="pathway-btn" onclick="loadPathway('tocilizumab')">Tocilizumab MOA</button>

    <div class="section-title">Top Nodes (by PageRank)</div>
    <div class="node-list" id="top-nodes"></div>
  </div>

  <div class="graph-area" id="graph-area">
    <svg id="graph-svg"></svg>
    <div class="zoom-controls">
      <button class="zoom-btn" onclick="zoomIn()">+</button>
      <button class="zoom-btn" onclick="zoomOut()">-</button>
      <button class="zoom-btn" onclick="zoomFit()">&#8689;</button>
    </div>
    <div class="legend" id="legend"></div>
    <div class="tooltip" id="tooltip" style="display:none"></div>
  </div>

  <div class="detail-panel">
    <div class="section-title">Node Details</div>
    <div id="node-detail"><div class="empty-state">Click a node to see details</div></div>

    <div class="section-title" style="margin-top:1rem">Neighbors</div>
    <div class="neighbor-list" id="neighbor-list"><div class="empty-state">Select a node</div></div>
  </div>
</div>

<script>
const API = '';
const typeColors = {
  Protein: '#3b82f6', Cytokine: '#f59e0b', Gene: '#06b6d4',
  Drug: '#10b981', Pathway: '#8b5cf6', Disease: '#ef4444',
  Adverse_Event: '#ef4444', Cell_Type: '#ec4899',
  BiologicalProcess: '#6366f1', Biomarker: '#14b8a6',
  Chemical: '#f97316', Unknown: '#64748b'
};

let simulation, svg, g, link, node, label, zoom;
let currentNodes = [], currentEdges = [];
let selectedNode = null;

// Initialize
async function init() {
  const stats = await fetch(API + '/api/stats').then(r => r.json());
  document.getElementById('stats').textContent =
    `${stats.nodes.toLocaleString()} nodes | ${stats.edges.toLocaleString()} edges`;

  // Type filter chips
  const filters = document.getElementById('type-filters');
  for (const [type, count] of Object.entries(stats.node_types || {}).sort((a,b) => b[1]-a[1])) {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.textContent = `${type} (${count})`;
    chip.dataset.type = type;
    chip.style.borderColor = typeColors[type] || '#64748b';
    chip.onclick = () => filterByType(type);
    filters.appendChild(chip);
  }

  // Legend
  const legend = document.getElementById('legend');
  legend.innerHTML = Object.entries(typeColors).slice(0, 8).map(([t, c]) =>
    `<div class="legend-item"><div class="legend-dot" style="background:${c}"></div>${t}</div>`
  ).join('');

  // Setup SVG
  setupGraph();

  // Load initial view (CRS pathway)
  loadPathway('crs');

  // Search
  let searchTimeout;
  document.getElementById('search').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => searchNodes(e.target.value), 300);
  });

  // Load top nodes
  loadTopNodes();
}

function setupGraph() {
  const area = document.getElementById('graph-area');
  svg = d3.select('#graph-svg');
  const width = area.clientWidth;
  const height = area.clientHeight;
  svg.attr('viewBox', [0, 0, width, height]);

  zoom = d3.zoom()
    .scaleExtent([0.1, 10])
    .on('zoom', (event) => g.attr('transform', event.transform));
  svg.call(zoom);

  g = svg.append('g');

  // Arrow markers
  svg.append('defs').append('marker')
    .attr('id', 'arrow').attr('viewBox', '0 -5 10 10')
    .attr('refX', 20).attr('refY', 0)
    .attr('markerWidth', 6).attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path').attr('d', 'M0,-3L8,0L0,3').attr('fill', '#64748b');

  simulation = d3.forceSimulation()
    .force('link', d3.forceLink().id(d => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(25));
}

function renderGraph(nodes, edges) {
  currentNodes = nodes;
  currentEdges = edges;

  g.selectAll('*').remove();

  link = g.append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('class', d => `link ${d.on_pathway ? 'pathway' : ''}`)
    .attr('marker-end', 'url(#arrow)');

  node = g.append('g')
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', d => d.is_center ? 12 : d.is_focus ? 8 : 6)
    .attr('fill', d => typeColors[d.type] || '#64748b')
    .attr('stroke', d => d.is_center ? '#fff' : d.is_focus ? 'rgba(255,255,255,0.3)' : 'none')
    .attr('stroke-width', d => d.is_center ? 2 : 1)
    .attr('cursor', 'pointer')
    .on('click', (event, d) => selectNodeById(d.id))
    .on('mouseover', showTooltip)
    .on('mouseout', hideTooltip)
    .call(d3.drag()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded));

  label = g.append('g')
    .selectAll('text')
    .data(nodes.filter(d => d.is_focus || d.is_center || nodes.length < 30))
    .join('text')
    .attr('class', d => `node-label ${d.is_focus ? 'focus' : ''}`)
    .attr('dy', d => (d.is_center ? 18 : 14))
    .text(d => d.id.length > 15 ? d.id.slice(0, 15) + '...' : d.id);

  simulation.nodes(nodes).on('tick', ticked);
  simulation.force('link').links(edges);
  simulation.alpha(1).restart();
}

function ticked() {
  link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  node.attr('cx', d => d.x).attr('cy', d => d.y);
  label.attr('x', d => d.x).attr('y', d => d.y);
}

function dragStarted(event) { if (!event.active) simulation.alphaTarget(0.3).restart(); event.subject.fx = event.subject.x; event.subject.fy = event.subject.y; }
function dragged(event) { event.subject.fx = event.x; event.subject.fy = event.y; }
function dragEnded(event) { if (!event.active) simulation.alphaTarget(0); event.subject.fx = null; event.subject.fy = null; }

function showTooltip(event, d) {
  const tt = document.getElementById('tooltip');
  tt.style.display = 'block';
  tt.style.left = (event.pageX + 10) + 'px';
  tt.style.top = (event.pageY - 10) + 'px';
  tt.innerHTML = `<div class="tt-title">${d.id}</div><div class="tt-type">${d.type}${d.is_focus ? ' (CRS-relevant)' : ''}</div>`;
}
function hideTooltip() { document.getElementById('tooltip').style.display = 'none'; }

// API calls
async function loadSubgraph(center, depth = 2) {
  const data = await fetch(`${API}/api/subgraph?center=${encodeURIComponent(center)}&depth=${depth}&max_nodes=150`).then(r => r.json());
  if (data.error) { console.error(data.error); return; }
  renderGraph(data.nodes, data.edges);
  document.getElementById('view-info').textContent = `Neighborhood: ${center} (depth ${depth})`;
}

async function loadPathway(name) {
  const data = await fetch(`${API}/api/pathway/${name}`).then(r => r.json());
  if (data.error) return;
  renderGraph(data.nodes, data.edges);
  document.getElementById('view-info').textContent = `Pathway: ${name.toUpperCase()}`;
}

async function selectNodeById(id) {
  selectedNode = id;
  const data = await fetch(`${API}/api/node/${encodeURIComponent(id)}`).then(r => r.json());
  if (data.error) return;

  // Highlight in graph
  node.attr('opacity', d => d.id === id ? 1 : 0.4);
  link.attr('opacity', d => d.source.id === id || d.target.id === id ? 1 : 0.15);
  setTimeout(() => { node.attr('opacity', 1); link.attr('opacity', 1); }, 2000);

  // Detail panel
  const detail = document.getElementById('node-detail');
  const n = data.node;
  let html = `<div class="detail-title" style="color:${typeColors[n.type]||'#fff'}">${n.id}</div>`;
  for (const [key, val] of Object.entries(n)) {
    if (key === 'id') continue;
    html += `<div class="detail-row"><span class="detail-label">${key}</span><span class="detail-value">${val}</span></div>`;
  }
  html += `<div class="detail-row"><span class="detail-label">degree</span><span class="detail-value">${data.degree}</span></div>`;
  html += `<button class="pathway-btn" style="margin-top:0.5rem" onclick="loadSubgraph('${id}')">Explore neighborhood</button>`;
  detail.innerHTML = html;

  // Neighbors
  const nlist = document.getElementById('neighbor-list');
  nlist.innerHTML = data.neighbors.slice(0, 50).map(nb =>
    `<div class="node-item" onclick="selectNodeById('${nb.target}')">
      <div class="node-dot" style="background:${typeColors[node_index_local[nb.target]||'Unknown']||'#64748b'}"></div>
      <span class="node-name">${nb.target}</span>
      <span class="node-type-tag">${nb.type}</span>
    </div>`
  ).join('');
}

const node_index_local = {};
async function loadTopNodes() {
  const data = await fetch(`${API}/api/search?limit=30`).then(r => r.json());
  const container = document.getElementById('top-nodes');
  container.innerHTML = data.map(n => {
    node_index_local[n.id] = n.type;
    return `<div class="node-item" onclick="loadSubgraph('${n.id}')">
      <div class="node-dot" style="background:${typeColors[n.type]||'#64748b'}"></div>
      <span class="node-name">${n.id}</span>
      <span class="node-type-tag">${n.type}</span>
    </div>`;
  }).join('');
}

async function searchNodes(query) {
  if (!query) { loadTopNodes(); return; }
  const data = await fetch(`${API}/api/search?q=${encodeURIComponent(query)}&limit=30`).then(r => r.json());
  const container = document.getElementById('top-nodes');
  container.innerHTML = data.map(n =>
    `<div class="node-item" onclick="loadSubgraph('${n.id}')">
      <div class="node-dot" style="background:${typeColors[n.type]||'#64748b'}"></div>
      <span class="node-name">${n.id}</span>
      <span class="node-type-tag">${n.degree} edges</span>
    </div>`
  ).join('');
}

function filterByType(type) {
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('active', c.dataset.type === type));
  // Reload subgraph filtered
  if (selectedNode) loadSubgraph(selectedNode);
}

function zoomIn() { svg.transition().duration(300).call(zoom.scaleBy, 1.5); }
function zoomOut() { svg.transition().duration(300).call(zoom.scaleBy, 0.67); }
function zoomFit() { svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity); }

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
