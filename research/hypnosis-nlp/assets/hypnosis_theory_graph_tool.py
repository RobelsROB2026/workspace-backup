#!/usr/bin/env python3
"""Hypnosis Theory Citation Graph / Concept Map Builder.

Builds a directed citation and concept graph of major hypnosis theories
(State vs. Non-State debate) using networkx. Supports GraphML and
interactive HTML (D3.js) output formats.

Usage examples:
    python hypnosis_theory_graph_tool.py --output-format html --output-file graph.html
    python hypnosis_theory_graph_tool.py --output-format graphml --output-file graph.graphml
    python hypnosis_theory_graph_tool.py --include-theories state_theory non_state_theory erickson hilgard
    python hypnosis_theory_graph_tool.py --include-citations --show-edges --output-format html
    python hypnosis_theory_graph_tool.py --list-theories
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

try:
    import networkx as nx
except ImportError:
    sys.exit("Error: networkx is required. Install with: pip install networkx")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# -- Built-in theory dataset ------------------------------------------------

THEORIES: list[dict[str, Any]] = [
    # Top-level paradigms
    {
        "id": "state_theory",
        "label": "State Theory",
        "category": "state",
        "description": (
            "Hypnosis produces a distinct altered state of consciousness -- "
            "a qualitatively different 'trance' mode with unique cognitive and "
            "neurophysiological characteristics."
        ),
        "key_authors": ["Hilgard", "Weitzenhoffer", "Orne"],
        "year": 1965,
    },
    {
        "id": "non_state_theory",
        "label": "Non-State Theory",
        "category": "non_state",
        "description": (
            "Hypnotic phenomena are fully explained by ordinary psychological "
            "processes -- expectancy, motivation, focused attention, and "
            "cognitive strategies -- without positing a special state."
        ),
        "key_authors": ["Barber", "Spanos", "Kirsch"],
        "year": 1969,
    },
    # State sub-theories
    {
        "id": "erickson",
        "label": "Ericksonian Hypnosis",
        "category": "state",
        "description": (
            "Milton Erickson's utilization approach treats hypnosis as a "
            "naturalistic altered state accessed through indirect suggestion, "
            "metaphor, and strategic communication tailored to each individual."
        ),
        "key_authors": ["Erickson", "Rossi"],
        "year": 1958,
    },
    {
        "id": "hilgard",
        "label": "Hilgard's Neodissociation Theory",
        "category": "state",
        "description": (
            "Hypnosis divides consciousness into parallel streams with an "
            "executive monitor ('hidden observer'). Dissociation -- not role-play "
            "-- accounts for the involuntariness of hypnotic responses."
        ),
        "key_authors": ["Hilgard"],
        "year": 1977,
    },
    {
        "id": "hypnotic_susceptibility_scale",
        "label": "Hypnotic Susceptibility Scale",
        "category": "state",
        "description": (
            "Standardized instruments (Stanford Hypnotic Susceptibility Scale, "
            "Harvard Group Scale) measuring individual differences in hypnotic "
            "responsiveness. Developed within the state-theory tradition to "
            "quantify trance depth and suggestibility."
        ),
        "key_authors": ["Weitzenhoffer", "Hilgard", "Shor"],
        "year": 1962,
    },
    {
        "id": "dissociation_model",
        "label": "Dissociation Model",
        "category": "state",
        "description": (
            "Hypnotic phenomena result from dissociative processes that split "
            "awareness into functionally independent streams. Encompasses "
            "Hilgard's neodissociation and Watkins's ego-state theory."
        ),
        "key_authors": ["Hilgard", "Watkins", "Bowers"],
        "year": 1977,
    },
    # Non-state sub-theories
    {
        "id": "social_learning_theory",
        "label": "Social Learning Theory",
        "category": "non_state",
        "description": (
            "Hypnotic behavior is learned through observation, modeling, and "
            "reinforcement. Subjects enact the 'hypnotized person' role based "
            "on social cues, expectations, and prior exposure to hypnosis "
            "narratives."
        ),
        "key_authors": ["Sarbin", "Coe", "Spanos"],
        "year": 1972,
    },
    {
        "id": "cognitive_theory",
        "label": "Cognitive Theory",
        "category": "non_state",
        "description": (
            "Hypnotic responding is mediated by cognitive strategies including "
            "focused attention, imaginative absorption, response expectancy, "
            "and reinterpretation of experience -- all normal cognitive "
            "processes, not a special state."
        ),
        "key_authors": ["Barber", "Kirsch", "Lynn"],
        "year": 1969,
    },
    {
        "id": "hypnotic_induction_model",
        "label": "Hypnotic Induction Model",
        "category": "non_state",
        "description": (
            "Analyzes how induction procedures work through non-state mechanisms: "
            "relaxation, focused attention, expectancy generation, and compliance "
            "priming. The induction ritual is effective not because it creates a "
            "trance but because it shapes expectancies and motivation."
        ),
        "key_authors": ["Barber", "Spanos", "Chaves"],
        "year": 1974,
    },
    # Integrative theories
    {
        "id": "neurocognitive",
        "label": "Neurocognitive Theory",
        "category": "integrative",
        "description": (
            "Hypnotic responding reflects individual differences in frontal "
            "executive attention and inhibitory control. High hypnotizability "
            "correlates with superior attentional flexibility and distinct "
            "neural activation patterns in prefrontal cortex."
        ),
        "key_authors": ["Gruzelier", "Crawford", "Raz"],
        "year": 1998,
    },
    {
        "id": "dual_process",
        "label": "Dual-Process Theory",
        "category": "integrative",
        "description": (
            "Hypnotic phenomena arise from the interplay of two processing "
            "systems: an automatic, fast (Type 1) system and a controlled, "
            "deliberative (Type 2) system. Suggestions shift the balance "
            "toward automatic processing while reducing executive monitoring."
        ),
        "key_authors": ["Dienes", "Brown", "Oakley"],
        "year": 2009,
    },
    {
        "id": "response_expectancy",
        "label": "Response Expectancy Theory",
        "category": "non_state",
        "description": (
            "Expecting to respond in a certain way generates the response "
            "automatically. Hypnotic inductions work primarily by altering "
            "response expectancies."
        ),
        "key_authors": ["Kirsch"],
        "year": 1985,
    },
]

# Citation edges: represent direct citation or intellectual debt
CITATIONS: list[dict[str, str]] = [
    {"source": "hilgard", "target": "state_theory",
     "relation": "cites", "label": "Hilgard, E.R. (1977). Divided consciousness. Wiley."},
    {"source": "erickson", "target": "state_theory",
     "relation": "cites", "label": "Erickson, M.H. (1958). Naturalistic techniques of hypnosis. Am. J. Clin. Hypn."},
    {"source": "hypnotic_susceptibility_scale", "target": "state_theory",
     "relation": "cites", "label": "Weitzenhoffer, A.M. & Hilgard, E.R. (1962). Stanford Hypnotic Susceptibility Scale."},
    {"source": "dissociation_model", "target": "hilgard",
     "relation": "cites", "label": "Bowers, K.S. (1992). Imagination and dissociation in hypnotic responding."},
    {"source": "dissociation_model", "target": "state_theory",
     "relation": "cites", "label": "Hilgard, E.R. (1977). Divided consciousness: Multiple controls in human thought."},
    {"source": "social_learning_theory", "target": "non_state_theory",
     "relation": "cites", "label": "Sarbin, T.R. & Coe, W.C. (1972). Hypnosis: A social psychological analysis."},
    {"source": "cognitive_theory", "target": "non_state_theory",
     "relation": "cites", "label": "Barber, T.X. (1969). Hypnosis: A scientific approach. Van Nostrand."},
    {"source": "hypnotic_induction_model", "target": "non_state_theory",
     "relation": "cites", "label": "Barber, T.X., Spanos, N.P. & Chaves, J.F. (1974). Hypnotism: Imagination and human potentialities."},
    {"source": "hypnotic_induction_model", "target": "cognitive_theory",
     "relation": "cites", "label": "Barber's cognitive reframing of the induction process"},
    {"source": "response_expectancy", "target": "cognitive_theory",
     "relation": "cites", "label": "Kirsch, I. (1985). Response expectancy as a determinant of experience and behavior."},
    {"source": "response_expectancy", "target": "social_learning_theory",
     "relation": "cites", "label": "Kirsch drew on sociocognitive and social learning frameworks"},
    {"source": "neurocognitive", "target": "dissociation_model",
     "relation": "cites", "label": "Gruzelier, J.H. (1998). A working model of the neurophysiology of hypnosis."},
    {"source": "neurocognitive", "target": "hilgard",
     "relation": "cites", "label": "Neurocognitive theory references Hilgard's dissociation concepts"},
    {"source": "dual_process", "target": "neurocognitive",
     "relation": "cites", "label": "Dienes, Z. & Brown, E. (2012). Dual-process model references neurocognitive work"},
    {"source": "dual_process", "target": "hilgard",
     "relation": "cites", "label": "Dual-process theory re-examines Hilgard's dissociative mechanisms"},
    {"source": "erickson", "target": "hypnotic_susceptibility_scale",
     "relation": "cites", "label": "Erickson acknowledged individual differences in susceptibility"},
    {"source": "social_learning_theory", "target": "cognitive_theory",
     "relation": "cites", "label": "Social learning theory incorporates cognitive-behavioral explanations"},
]

# Relationship edges: conceptual links (opposition, influence, subsumption)
RELATIONSHIPS: list[dict[str, str]] = [
    {"source": "state_theory", "target": "non_state_theory",
     "relation": "opposes", "label": "The central debate in hypnosis research"},
    {"source": "non_state_theory", "target": "state_theory",
     "relation": "opposes", "label": "Non-state theorists reject the trance concept"},
    {"source": "state_theory", "target": "erickson",
     "relation": "subsumes", "label": "Ericksonian hypnosis falls under the state paradigm"},
    {"source": "state_theory", "target": "hilgard",
     "relation": "subsumes", "label": "Neodissociation is a state sub-theory"},
    {"source": "state_theory", "target": "hypnotic_susceptibility_scale",
     "relation": "subsumes", "label": "Susceptibility scales developed within state tradition"},
    {"source": "state_theory", "target": "dissociation_model",
     "relation": "subsumes", "label": "Dissociation model is a state sub-theory"},
    {"source": "non_state_theory", "target": "social_learning_theory",
     "relation": "subsumes", "label": "Social learning theory is a non-state sub-theory"},
    {"source": "non_state_theory", "target": "cognitive_theory",
     "relation": "subsumes", "label": "Cognitive theory is a non-state sub-theory"},
    {"source": "non_state_theory", "target": "hypnotic_induction_model",
     "relation": "subsumes", "label": "Induction model is a non-state sub-theory"},
    {"source": "non_state_theory", "target": "response_expectancy",
     "relation": "subsumes", "label": "Response expectancy is a non-state sub-theory"},
    {"source": "social_learning_theory", "target": "state_theory",
     "relation": "critiques", "label": "Social learning theorists argue trance is role enactment"},
    {"source": "cognitive_theory", "target": "dissociation_model",
     "relation": "critiques", "label": "Cognitive theorists dispute dissociation claims"},
    {"source": "neurocognitive", "target": "social_learning_theory",
     "relation": "challenges", "label": "Neuroimaging data challenge pure social-learning explanations"},
    {"source": "dual_process", "target": "state_theory",
     "relation": "refines", "label": "Reframes 'state' as a processing-mode shift, not trance"},
    {"source": "dual_process", "target": "non_state_theory",
     "relation": "refines", "label": "Incorporates cognitive/social factors within dual-system model"},
    {"source": "hilgard", "target": "dissociation_model",
     "relation": "influenced", "label": "Hilgard's work inspired the broader dissociation model"},
    {"source": "erickson", "target": "hilgard",
     "relation": "influenced", "label": "Erickson's clinical observations informed Hilgard's lab work"},
    {"source": "neurocognitive", "target": "dual_process",
     "relation": "influenced", "label": "Neurocognitive individual-differences work shaped dual-process models"},
]

CATEGORY_COLORS = {
    "state": "#2a6fdb",
    "non_state": "#e85d04",
    "integrative": "#2d6a4f",
}

RELATION_COLORS = {
    "cites": "#8b949e",
    "subsumes": "#999",
    "influenced": "#2a6fdb",
    "opposes": "#d00000",
    "critiques": "#bd1f36",
    "challenges": "#e85d04",
    "refines": "#2d6a4f",
}


# -- Graph construction -----------------------------------------------------


def build_graph(
    theories: list[dict[str, Any]],
    citations: list[dict[str, str]],
    relationships: list[dict[str, str]],
    include_theories: list[str] | None = None,
    include_citations: bool = False,
    show_edges: bool = False,
) -> nx.DiGraph:
    """Build a directed graph from theory nodes and edge lists.

    Args:
        theories: List of theory node dicts.
        citations: List of citation edge dicts.
        relationships: List of relationship edge dicts.
        include_theories: If given, only include these theory IDs (default: all).
        include_citations: Whether to add citation edges (default: False).
        show_edges: Whether to add conceptual relationship edges (default: False).

    Returns:
        A populated networkx DiGraph.
    """
    G = nx.DiGraph()

    for theory in theories:
        tid = theory["id"]
        if include_theories and tid not in include_theories:
            continue
        G.add_node(
            tid,
            label=theory.get("label", tid),
            category=theory.get("category", "unknown"),
            description=theory.get("description", ""),
            key_authors=", ".join(theory.get("key_authors", [])),
            year=str(theory.get("year", "")),
        )
    log.info("Added %d theory nodes.", G.number_of_nodes())

    node_ids = set(G.nodes())

    def _add_edges(edges: list[dict[str, str]], edge_type: str) -> int:
        count = 0
        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            if src in node_ids and tgt in node_ids:
                G.add_edge(
                    src, tgt,
                    relation=edge.get("relation", "related"),
                    edge_type=edge_type,
                    label=edge.get("label", ""),
                )
                count += 1
        return count

    if include_citations:
        n = _add_edges(citations, "citation")
        log.info("Added %d citation edges.", n)

    if show_edges:
        n = _add_edges(relationships, "relationship")
        log.info("Added %d relationship edges.", n)

    log.info("Total graph: %d nodes, %d edges.", G.number_of_nodes(), G.number_of_edges())
    return G


# -- Output: list theories --------------------------------------------------


def list_theories(theories: list[dict[str, Any]]) -> None:
    """Print a formatted list of available theory IDs and labels."""
    print("\nAvailable theories:\n")
    for t in theories:
        cat = t.get("category", "?")
        year = f" ({t['year']})" if t.get("year") else ""
        authors = ", ".join(t.get("key_authors", []))
        print(f"  {t['id']:<30} {t['label']}{year}")
        print(f"  {'':30} [{cat}] {authors}")
        print()


# -- Output: GraphML --------------------------------------------------------


def export_graphml(G: nx.DiGraph, output_path: str) -> None:
    """Write the graph to GraphML format with full node/edge attributes.

    Args:
        G: The directed graph.
        output_path: Destination file path.
    """
    nx.write_graphml(G, output_path)
    log.info("GraphML written to %s", output_path)


# -- Output: HTML / D3.js ---------------------------------------------------


def export_html(G: nx.DiGraph, output_path: str) -> None:
    """Generate a standalone interactive HTML visualization using D3.js.

    Features: force-directed layout, zoom/pan, draggable nodes, node
    labels, hover tooltips with theory details, edge labels, and a legend.

    Args:
        G: The directed graph.
        output_path: Destination file path.
    """
    nodes_json = []
    for nid, attrs in G.nodes(data=True):
        nodes_json.append({
            "id": nid,
            "label": attrs.get("label", nid),
            "category": attrs.get("category", "unknown"),
            "description": attrs.get("description", ""),
            "authors": attrs.get("key_authors", ""),
            "year": attrs.get("year", ""),
            "color": CATEGORY_COLORS.get(attrs.get("category", ""), "#888"),
        })

    links_json = []
    for src, tgt, attrs in G.edges(data=True):
        rel = attrs.get("relation", "related")
        links_json.append({
            "source": src,
            "target": tgt,
            "relation": rel,
            "edge_type": attrs.get("edge_type", ""),
            "label": attrs.get("label", ""),
            "color": RELATION_COLORS.get(rel, "#999"),
        })

    data_js = json.dumps({"nodes": nodes_json, "links": links_json}, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Hypnosis Theory Citation Graph</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; overflow: hidden; }}
  svg {{ display: block; }}
  .tooltip {{
    position: absolute; padding: 12px 16px; background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; font-size: 13px; pointer-events: none; opacity: 0;
    transition: opacity .15s; max-width: 360px; line-height: 1.5; z-index: 100;
  }}
  .tooltip .tt-title {{ font-weight: 700; font-size: 15px; margin-bottom: 4px; }}
  .tooltip .tt-meta {{ color: #8b949e; font-size: 12px; margin-bottom: 6px; }}
  .tooltip .tt-desc {{ margin-bottom: 4px; }}
  .legend {{
    position: absolute; top: 16px; left: 16px; background: #161b22ee;
    border: 1px solid #30363d; border-radius: 8px; padding: 14px 18px; font-size: 13px;
    max-height: calc(100vh - 32px); overflow-y: auto;
  }}
  .legend h3 {{ margin-bottom: 8px; font-size: 14px; color: #e6edf3; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
  .legend-line {{ width: 20px; height: 2px; flex-shrink: 0; }}
  h1 {{
    position: absolute; top: 16px; right: 16px; font-size: 18px; font-weight: 600;
    background: #161b22ee; border: 1px solid #30363d; border-radius: 8px; padding: 10px 16px;
  }}
  .controls {{
    position: absolute; bottom: 16px; right: 16px; background: #161b22ee;
    border: 1px solid #30363d; border-radius: 8px; padding: 10px 14px; font-size: 12px;
    color: #8b949e;
  }}
</style>
</head>
<body>
<h1>Hypnosis Theory Citation &amp; Concept Graph</h1>
<div class="legend">
  <h3>Node Categories</h3>
  <div class="legend-item"><span class="legend-dot" style="background:#2a6fdb"></span> State Theories</div>
  <div class="legend-item"><span class="legend-dot" style="background:#e85d04"></span> Non-State Theories</div>
  <div class="legend-item"><span class="legend-dot" style="background:#2d6a4f"></span> Integrative Theories</div>
  <h3 style="margin-top:12px">Edge Types</h3>
  <div class="legend-item"><span class="legend-line" style="background:#8b949e"></span> Cites</div>
  <div class="legend-item"><span class="legend-line" style="background:#999"></span> Subsumes</div>
  <div class="legend-item"><span class="legend-line" style="background:#2a6fdb"></span> Influenced</div>
  <div class="legend-item"><span class="legend-line" style="background:#d00000"></span> Opposes</div>
  <div class="legend-item"><span class="legend-line" style="background:#bd1f36"></span> Critiques</div>
  <div class="legend-item"><span class="legend-line" style="background:#e85d04"></span> Challenges</div>
  <div class="legend-item"><span class="legend-line" style="background:#2d6a4f"></span> Refines</div>
</div>
<div class="controls">Scroll to zoom &middot; Drag nodes to rearrange &middot; Hover for details</div>
<div class="tooltip" id="tooltip"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {data_js};

const width = window.innerWidth, height = window.innerHeight;
const svg = d3.select("body").append("svg").attr("width", width).attr("height", height);
const container = svg.append("g");

// Arrow markers per color
const markerColors = [...new Set(data.links.map(l => l.color))];
markerColors.forEach(c => {{
  svg.append("defs").append("marker")
    .attr("id", "arrow-" + c.replace("#",""))
    .attr("viewBox", "0 -5 10 10").attr("refX", 24).attr("refY", 0)
    .attr("markerWidth", 7).attr("markerHeight", 7).attr("orient", "auto")
    .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", c);
}});

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id).distance(160))
  .force("charge", d3.forceManyBody().strength(-500))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(40));

// Edges
const link = container.append("g").attr("class", "links")
  .selectAll("line").data(data.links).join("line")
  .attr("stroke", d => d.color).attr("stroke-width", d => d.edge_type === "citation" ? 1.2 : 2)
  .attr("stroke-opacity", 0.55)
  .attr("stroke-dasharray", d => d.edge_type === "citation" ? "5,4" : "none")
  .attr("marker-end", d => "url(#arrow-" + d.color.replace("#","") + ")");

// Edge label on hover
link.append("title").text(d => d.relation + (d.label ? ": " + d.label : ""));

// Nodes
const node = container.append("g").attr("class", "nodes")
  .selectAll("g").data(data.nodes).join("g")
  .call(d3.drag()
    .on("start", (e,d) => {{ if(!e.active) simulation.alphaTarget(0.3).restart(); d.fx=e.x; d.fy=e.y; }})
    .on("drag", (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
    .on("end", (e,d) => {{ if(!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }}));

node.append("circle")
  .attr("r", d => {{
    const main = ["state_theory","non_state_theory"];
    return main.includes(d.id) ? 20 : 14;
  }})
  .attr("fill", d => d.color)
  .attr("stroke", "#c9d1d9").attr("stroke-width", 1.5)
  .attr("cursor", "grab");

node.append("text")
  .text(d => d.label)
  .attr("dx", 22).attr("dy", 5)
  .attr("fill", "#c9d1d9").attr("font-size", "12px")
  .attr("pointer-events", "none");

// Tooltip
const tooltip = d3.select("#tooltip");
node.on("mouseover", (e, d) => {{
  tooltip.style("opacity", 1).html(
    `<div class="tt-title" style="color:${{d.color}}">${{d.label}}</div>` +
    `<div class="tt-meta">${{d.category.replace("_"," ")}}${{d.year ? " \\u00b7 " + d.year : ""}}</div>` +
    `<div class="tt-desc">${{d.description}}</div>` +
    (d.authors ? `<div class="tt-meta" style="margin-top:6px">Key authors: ${{d.authors}}</div>` : "")
  );
}}).on("mousemove", e => {{
  tooltip.style("left", (e.pageX + 16) + "px").style("top", (e.pageY - 12) + "px");
}}).on("mouseout", () => tooltip.style("opacity", 0));

// Tick
simulation.on("tick", () => {{
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

// Zoom & pan
svg.call(d3.zoom().scaleExtent([0.2, 6]).on("zoom", e => {{
  container.attr("transform", e.transform);
}}));
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    log.info("Interactive HTML written to %s", output_path)


# -- CLI ---------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    all_ids = [t["id"] for t in THEORIES]

    p = argparse.ArgumentParser(
        description="Build a citation graph / concept map of major hypnosis theories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--output-format",
        choices=["graphml", "html"],
        default="html",
        help="Output format: 'graphml' for NetworkX GraphML or 'html' for interactive D3.js visualization (default: html).",
    )
    p.add_argument(
        "--include-theories",
        nargs="+",
        metavar="ID",
        default=None,
        help=(
            "Theory IDs to include (default: all). "
            f"Available: {', '.join(all_ids)}"
        ),
    )
    p.add_argument(
        "--include-citations",
        action="store_true",
        default=False,
        help="Include citation edges between theories (default: false).",
    )
    p.add_argument(
        "--show-edges",
        action="store_true",
        default=False,
        help="Show conceptual relationship edges (opposes, subsumes, influences, etc.) (default: false).",
    )
    p.add_argument(
        "--output-file",
        default=None,
        help="Output file path. Defaults to hypnosis_theory_graph.<format>.",
    )
    p.add_argument(
        "--list-theories",
        action="store_true",
        help="List all available theory IDs and descriptions, then exit.",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )
    return p.parse_args()


def main() -> None:
    """Entry point: parse args, build graph, export."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list_theories:
        list_theories(THEORIES)
        return

    # Validate --include-theories IDs
    valid_ids = {t["id"] for t in THEORIES}
    if args.include_theories:
        bad = [tid for tid in args.include_theories if tid not in valid_ids]
        if bad:
            log.error("Unknown theory IDs: %s", ", ".join(bad))
            log.error("Valid IDs: %s", ", ".join(sorted(valid_ids)))
            sys.exit(1)

    G = build_graph(
        theories=THEORIES,
        citations=CITATIONS,
        relationships=RELATIONSHIPS,
        include_theories=args.include_theories,
        include_citations=args.include_citations,
        show_edges=args.show_edges,
    )

    if G.number_of_nodes() == 0:
        log.warning("Graph has no nodes -- nothing to export.")
        return

    output_path = args.output_file
    if not output_path:
        ext = "html" if args.output_format == "html" else "graphml"
        output_path = f"hypnosis_theory_graph.{ext}"

    if args.output_format == "html":
        export_html(G, output_path)
    else:
        export_graphml(G, output_path)

    print(f"\nGraph exported to {output_path}")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Format: {args.output_format}")


if __name__ == "__main__":
    main()
