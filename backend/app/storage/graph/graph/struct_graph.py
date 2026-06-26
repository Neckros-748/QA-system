import networkx as nx


def build_struct_graph(doc: dict) -> nx.Graph:

	G = nx.DiGraph()

	G.add_node(
		doc["id"],
		title=doc.get("title", ""),
		type="STRUCT::DOCUMENT"
	)

	def _build_section(parent_id: str, sect: dict):

		# Добавление узла
		G.add_node(
			sect["id"],
			title=sect.get("title", ""),
			type="STRUCT::SECTION"
		)

		# Добавление ребра (с родительским узлом)
		G.add_edge(
			parent_id,
			sect["id"],
			type="CONTAINS"
		)

		for sect_it in sect.get("sections", []):
			_build_section(sect["id"], sect_it)

		for par_it in sect.get("paragraphs", []):
			_build_paragraph(sect["id"], par_it)

	def _build_paragraph(parent_id: str, par: dict):

		# Добавление узла
		G.add_node(
			par["id"],
			title=par.get("title", ""),
			type="STRUCT::PARAGRAPH"
		)

		# Добавление ребра (с родительским узлом)
		G.add_edge(
			parent_id,
			par["id"],
			type="CONTAINS"
		)

	for sect in doc.get("sections", []):
		_build_section(doc["id"], sect)

	return G