from typing import Dict, Any

import networkx as nx


def build_struct_graph(
		doc: Dict[str, Any],
) -> nx.Graph:
	graph: nx.DiGraph = nx.DiGraph()

	graph.add_node(
		doc["id"],
		label = doc.get("title", ""),
		type  = "STRUCT::DOCUMENT",
	)

	if "sections" in doc:
		_build_section(graph, doc["id"], doc["sections"][0])

	return graph


def _build_section(
		graph:     nx.DiGraph,
		parent_id: str,
		section:   Dict[str, Any],
):
	graph.add_node(
		section["id"],
		label = section.get("title", ""),
		type  = "STRUCT::SECTION",
	)
	graph.add_edge(
		parent_id,
		section["id"],
		label = "",
		type  = "contains",
	)

	for par in section.get("paragraphs", []):
		_build_paragraph(graph, section["id"], par)

	for sect in section.get("sections", []):
		_build_section(graph, sect["id"], sect)

def _build_paragraph(
		graph:     nx.DiGraph,
		parent_id: str,
		paragraph: Dict[str, Any],
):
	graph.add_node(
		paragraph["id"],
		label = paragraph.get("title", ""),
		type  = "STRUCT::PARAGRAPH"
	)
	graph.add_edge(
		parent_id,
		paragraph["id"],
		label = "",
		type  = "contains",
	)
