#!/usr/bin/env python3
"""Hypnosis Theory Citation Graph Builder.

Builds a citation graph / concept map of major hypnosis theories using networkx.
Covers State Theory (Hypnotizability, Suggestibility, Dissociation, Altered
Consciousness) and Non-State Theory (Neurological, Cognitive, Information
Processing, Neuroplasticity) with theoretical relationships and citations.

Supports output as:
  - html/d3: Standalone HTML with embedded D3.js force-directed graph
  - graphml:  NetworkX graph exported to .graphml format

Usage:
    python hypnosis_theory_graph.py --output-format d3 --include-theories all
    python hypnosis_theory_graph.py --output-format graphml --include-theories state
    python hypnosis_theory_graph.py --output-format html --include-theories non-state --include-citations
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import networkx as nx
except ImportError:
    print("Error: networkx is required. Install with: pip install networkx", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Theory & citation data
# ---------------------------------------------------------------------------

STATE_NODES = [
    {
        "id": "state_theory",
        "label": "State Theory",
        "type": "paradigm",
        "description": "Hypnosis involves a distinct altered state of consciousness",
    },
    {
        "id": "hypnotizability",
        "label": "Hypnotizability",
        "type": "construct",
        "description": "Stable trait measuring individual capacity for hypnotic response",
        "key_authors": "Hilgard (1965); Weitzenhoffer & Hilgard (1962)",
    },
    {
        "id": "suggestibility",
        "label": "Suggestibility",
        "type": "construct",
        "description": "Degree of responsiveness to hypnotic suggestions",
        "key_authors": "Bernheim (1884); Hull (1933)",
    },
    {
        "id": "dissociation",
        "label": "Dissociation",
        "type": "construct",
        "description": "Neodissociation theory - parallel cognitive streams",
        "key_authors": "Hilgard (1977); Janet (1889)",
    },
    {
        "id": "altered_consciousness",
        "label": "Altered Consciousness",
        "type": "construct",
        "description": "Hypnosis as a qualitatively different conscious state",
        "key_authors": "Tart (1969); Fromm (1979)",
    },
]

NON_STATE_NODES = [
    {
        "id": "non_state_theory",
        "label": "Non-State Theory",
        "type": "paradigm",
        "description": "Hypnotic phenomena explained without invoking a special state",
    },
    {
        "id": "neurological",
        "label": "Neurological Approach",
        "type": "construct",
        "description": "Neural correlates of hypnosis - fMRI, EEG, connectivity studies",
        "key_authors": "Rainville et al. (1999); Raz (2005)",
    },
    {
        "id": "cognitive",
        "label": "Cognitive Approach",
        "type": "construct",
        "description": "Social-cognitive / response-expectancy models",
        "key_authors": "Barber (1969); Spanos (1986); Kirsch (1991)",
    },
    {
        "id": "information_processing",
        "label": "Information Processing",
        "type": "construct",
        "description": "Hypnosis as altered attentional filtering and executive control",
        "key_authors": "Woody & Bowers (1994); Gruzelier (1998)",
    },
    {
        "id": "neuroplasticity",
        "label": "Neuroplasticity",
        "type": "construct",
        "description": "Hypnosis-driven changes in neural pathways and cortical plasticity",
        "key_authors": "Oakley & Halligan (2013); Landry et al. (2017)",
    },
]

# Directed edges: (source, target, relationship, optional citation)
STATE_EDGES = [
    ("state_theory", "hypnotizability", "encompasses", "Hilgard, 1965"),
    ("state_theory", "suggestibility", "encompasses", "Hull, 1933"),
    ("state_theory", "dissociation", "encompasses", "Hilgard, 1977"),
    ("state_theory", "altered_consciousness", "encompasses", "Tart, 1969"),
    ("hypnotizability", "suggestibility", "predicts", "Weitzenhoffer & Hilgard, 1962"),
    ("dissociation", "altered_consciousness", "implies", "Hilgard, 1977"),
    ("hypnotizability", "dissociation", "correlates_with", "Hilgard, 1965"),
]

NON_STATE_EDGES = [
    ("non_state_theory", "neurological", "encompasses", "Raz, 2005"),
    ("non_state_theory", "cognitive", "encompasses", "Barber, 1969"),
    ("non_state_theory", "information_processing", "encompasses", "Woody & Bowers, 1994"),
    ("non_state_theory", "neuroplasticity", "encompasses", "Oakley & Halligan, 2013"),
    ("cognitive", "information_processing", "informs", "Spanos, 1986"),
    ("neurological", "neuroplasticity", "supports", "Landry et al., 2017"),
    ("information_processing", "neurological", "validated_by", "Gruzelier, 1998"),
]

CROSS_EDGES = [
    ("state_theory", "non_state_theory", "debates", "Kirsch & Lynn, 1995"),
    ("dissociation", "cognitive", "challenged_by", "Spanos, 1986"),
    ("altered_consciousness", "neurological", "investigated_by", "Rainville et al., 1999"),
    ("suggestibility", "cognitive", "reinterpreted_by", "Kirsch, 1991"),
    ("hypnotizability", "neurological", "neural_correlates", "Hoeft et al., 2012"),
    ("neuroplasticity", "dissociation", "reconceptualizes", "Oakley & Halligan, 2013"),
]

CITATION_NODES = [
    {"id": "hilgard_1965", "label": "Hilgard (1965)", "type": "citation",
     "title": "Hypnotic Susceptibility"},
    {"id": "hilgard_1977", "label": "Hilgard (1977)", "type": "citation",
     "title": "Divided Consciousness"},
    {"id": "barber_1969", "label": "Barber (1969)", "type": "citation",
     "title": "Hypnosis: A Scientific Approach"},
    {"id": "spanos_1986", "label": "Spanos (1986)", "type": "citation",
     "title": "Hypnotic behavior: A social-psychological interpretation"},
    {"id": "kirsch_1991", "label": "Kirsch (1991)", "type": "citation",
     "title": "The Social Learning Theory of Hypnosis"},
    {"id": "rainville_1999", "label": "Rainville et al. (1999)", "type": "citation",
     "title": "Brain mechanisms of hypnosis and hypnotic analgesia"},
    {"id": "oakley_2013", "label": "Oakley & Halligan (2013)", "type": "citation",
     "title": "Hypnotic suggestion and cognitive neuroscience"},
    {"id": "landry_2017", "label": "Landry et al. (2017)", "type": "citation",
     "title": "Hypnosis and neuroplasticity review"},
    {"id": "tart_1969", "label": "Tart (1969)", "type": "citation",
     "title": "Altered States of Consciousness"},
    {"id": "gruzelier_1998", "label": "Gruzelier (1998)", "type": "citation",
     "title": "A working model of the neurophysiology of hypnosis"},
    {"id": "woody_bowers_1994", "label": "Woody & Bowers (1994)", "type": "citation",
     "title": "A frontal assault on dissociated control"},
    {"id": "hull_1933", "label": "Hull (1933)", "type": "citation",
     "title": "Hypnosis and Suggestibility"},
]

CITATION_EDGES = [
    ("hilgard_1965", "hypnotizability", "foundational_for"),
    ("hilgard_1977", "dissociation", "foundational_for"),
    ("barber_1969", "cognitive", "foundational_for"),
    ("spanos_1986", "cognitive", "supports"),
    ("kirsch_1991", "cognitive", "extends"),
    ("rainville_1999", "neurological", "foundational_for"),
    ("oakley_2013", "neuroplasticity", "foundational_for"),
    ("landry_2017", "neuroplasticity", "supports"),
    ("tart_1969", "altered_consciousness", "foundational_for"),
    ("gruzelier_1998", "information_processing", "foundational_for"),
    ("woody_bowers_1994", "information_processing", "foundational_for"),
    ("hull_1933", "suggestibility", "foundational_for"),
    ("hilgard_1977", "hilgard_1965", "builds_on"),
    ("spanos_1986", "barber_1969", "builds_on"),
    ("oakley_2013", "rainville_1999", "builds_on"),
    ("landry_2017", "oakley_2013", "builds_on"),
]


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(include_theories: str, include_citations: bool) -> nx.DiGraph:
    """Build the networkx directed graph from the theory data."""
    G = nx.DiGraph()

    nodes_to_add = []
    edges_to_add = []

    if include_theories in ("state", "all"):
        nodes_to_add.extend(STATE_NODES)
        edges_to_add.extend(STATE_EDGES)

    if include_theories in ("non-state", "all"):
        nodes_to_add.extend(NON_STATE_NODES)
        edges_to_add.extend(NON_STATE_EDGES)

    if include_theories == "all":
        edges_to_add.extend(CROSS_EDGES)

    # Add theory nodes
    for node in nodes_to_add:
        nid = node["id"]
        G.add_node(nid, **{k: v for k, v in node.items() if k != "id"})

    # Add theory edges
    for edge in edges_to_add:
        src, tgt, rel = edge[0], edge[1], edge[2]
        attrs = {"relationship": rel}
        if len(edge) > 3:
            attrs["citation"] = edge[3]
        if src in G and tgt in G:
            G.add_edge(src, tgt, **attrs)

    # Add citation nodes and edges
    if include_citations:
        valid_theory_ids = set(G.nodes())
        for cnode in CITATION_NODES:
            cid = cnode["id"]
            G.add_node(cid, **{k: v for k, v in cnode.items() if k != "id"})

        for cedge in CITATION_EDGES:
            src, tgt = cedge[0], cedge[1]
            rel = cedge[2]
            if src in G and tgt in G:
                G.add_edge(src, tgt, relationship=rel)

    return G


# ---------------------------------------------------------------------------
# GraphML output
# ---------------------------------------------------------------------------

def export_graphml(G: nx.DiGraph, output_path: Path) -> None:
    """Export graph to GraphML format."""
    nx.write_graphml(G, str(output_path))
    print(f"GraphML written to {output_path}")


# ---------------------------------------------------------------------------
# D3.js / HTML output
# ---------------------------------------------------------------------------

D3_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Hypnosis Theory Citation Graph</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; }
  svg { display: block; width: 100vw; height: 100vh; }
  .link { stroke-opacity: 0.5; }
  .node-label { font-size: 11px; pointer-events: none; fill: #c9d1d9; }
  .edge-label { font-size: 9px; fill: #8b949e; pointer-events: none; }
  #legend { position: absolute; top: 16px; left: 16px; background: #161b22;
            border: 1px solid #30363d; border-radius: 6px; padding: 12px; font-size: 13px; }
  #legend h3 { margin-bottom: 8px; font-size: 14px; }
  .legend-item { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
  .legend-swatch { width: 14px; height: 14px; border-radius: 50%; }
  #title { position: absolute; top: 16px; right: 16px; background: #161b22;
           border: 1px solid #30363d; border-radius: 6px; padding: 12px 16px; }
  #title h2 { font-size: 16px; font-weight: 600; }
  #title p { font-size: 12px; color: #8b949e; margin-top: 4px; }
</style>
</head>
<body>
<div id="legend">
  <h3>Node Types</h3>
  <div class="legend-item"><div class="legend-swatch" style="background:#f78166"></div> Paradigm</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#79c0ff"></div> Construct</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#7ee787"></div> Citation</div>
</div>
<div id="title">
  <h2>Hypnosis Theories: State vs Non-State</h2>
  <p>Drag nodes to explore. Scroll to zoom.</p>
</div>
<svg></svg>
<script>
const graphData = __GRAPH_JSON__;

const COLOR_MAP = { paradigm: "#f78166", construct: "#79c0ff", citation: "#7ee787" };
const RADIUS_MAP = { paradigm: 18, construct: 13, citation: 9 };

const svg = d3.select("svg");
const width = window.innerWidth;
const height = window.innerHeight;
svg.attr("viewBox", [0, 0, width, height]);

const g = svg.append("g");

svg.call(d3.zoom().scaleExtent([0.2, 5]).on("zoom", (e) => g.attr("transform", e.transform)));

const simulation = d3.forceSimulation(graphData.nodes)
  .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(120))
  .force("charge", d3.forceManyBody().strength(-400))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => RADIUS_MAP[d.type] + 8));

// Arrow markers
svg.append("defs").selectAll("marker")
  .data(["arrow"])
  .join("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 25).attr("refY", 0)
    .attr("markerWidth", 6).attr("markerHeight", 6)
    .attr("orient", "auto")
  .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#484f58");

const link = g.append("g").selectAll("line")
  .data(graphData.links).join("line")
  .attr("class", "link")
  .attr("stroke", "#484f58")
  .attr("stroke-width", 1.5)
  .attr("marker-end", "url(#arrow)");

const edgeLabel = g.append("g").selectAll("text")
  .data(graphData.links).join("text")
  .attr("class", "edge-label")
  .text(d => d.relationship || "");

const node = g.append("g").selectAll("circle")
  .data(graphData.nodes).join("circle")
  .attr("r", d => RADIUS_MAP[d.type] || 10)
  .attr("fill", d => COLOR_MAP[d.type] || "#8b949e")
  .attr("stroke", "#0d1117").attr("stroke-width", 2)
  .call(d3.drag()
    .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
    .on("end", (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

node.append("title").text(d => `${d.label}\n${d.description || ""}`);

const label = g.append("g").selectAll("text")
  .data(graphData.nodes).join("text")
  .attr("class", "node-label")
  .attr("text-anchor", "middle").attr("dy", d => -(RADIUS_MAP[d.type] || 10) - 6)
  .text(d => d.label);

simulation.on("tick", () => {
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  edgeLabel.attr("x", d => (d.source.x + d.target.x) / 2)
           .attr("y", d => (d.source.y + d.target.y) / 2);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
  label.attr("x", d => d.x).attr("y", d => d.y);
});
</script>
</body>
</html>"""


def export_d3_html(G: nx.DiGraph, output_path: Path) -> None:
    """Export graph as a standalone D3.js HTML visualization."""
    nodes = []
    for nid, attrs in G.nodes(data=True):
        node = {"id": nid}
        node.update(attrs)
        nodes.append(node)

    links = []
    for src, tgt, attrs in G.edges(data=True):
        link = {"source": src, "target": tgt}
        link.update(attrs)
        links.append(link)

    graph_json = json.dumps({"nodes": nodes, "links": links}, indent=2)
    html = D3_HTML_TEMPLATE.replace("__GRAPH_JSON__", graph_json)
    output_path.write_text(html)
    print(f"D3.js HTML written to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a citation graph / concept map of major hypnosis theories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --output-format d3
  %(prog)s --output-format graphml --include-theories state
  %(prog)s --output-format html --include-theories all --include-citations
""",
    )
    parser.add_argument(
        "--output-format",
        choices=["html", "d3", "graphml"],
        default="html",
        help="Output format: html/d3 for interactive D3.js visualization, graphml for NetworkX GraphML export (default: html)",
    )
    parser.add_argument(
        "--include-theories",
        choices=["state", "non-state", "all"],
        default="all",
        help="Which theory family to include (default: all)",
    )
    parser.add_argument(
        "--include-citations",
        action="store_true",
        default=False,
        help="Include citation/reference nodes and edges in the graph",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Output file path (default: auto-generated based on format)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # Build graph
    G = build_graph(args.include_theories, args.include_citations)
    print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Determine output path
    if args.output_file:
        output_path = Path(args.output_file)
    else:
        ext = ".graphml" if args.output_format == "graphml" else ".html"
        output_path = Path(f"hypnosis_theory_graph{ext}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export
    if args.output_format in ("html", "d3"):
        export_d3_html(G, output_path)
    elif args.output_format == "graphml":
        export_graphml(G, output_path)

    print("Done.")


if __name__ == "__main__":
    main()
