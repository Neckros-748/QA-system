from enum import Enum
import json
from html import escape
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Iterable

import networkx as nx
from networkx.classes.reportviews import OutEdgeDataView, InEdgeDataView, OutEdgeView

from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk
from backend.src.storage.database.graph.constructor.struct_graph import build_struct_graph
from backend.src.storage.utils.utils import __append_unique__



class Direction(Enum):
	NONE = 0
	UP   = 1
	DOWN = 2

def _short_value(v: Any) -> Any:
	if v is None or isinstance(v, (str, int, float, bool)):
		return v
	if isinstance(v, Enum):
		return v.name
	if isinstance(v, nx.Graph):
		return {
			"graph_type": v.__class__.__name__,
			"nodes": v.number_of_nodes(),
			"edges": v.number_of_edges(),
		}
	if isinstance(v, dict):
		return {str(k): _short_value(val) for k, val in v.items()}
	if isinstance(v, (list, tuple, set)):
		return [_short_value(x) for x in v]
	if hasattr(v, "__dict__"):
		return _short_value(vars(v))
	return str(v)


class GraphStorage:
	def __init__(self):
		self.graph = nx.DiGraph()

		self.stack: Dict[str, Dict[str, Any]] = {}

	def to_html(self, height: str = "800px") -> str:
		nodes: List[Dict[str, Any]] = []
		edges: List[Dict[str, Any]] = []

		for node_id, attrs in self.graph.nodes(data=True):
			node_type = attrs.get("type", "TERM")
			label = attrs.get("label", node_id)

			if node_type == "SUBGRAPH":
				color = {
					"background": "#e3f2fd",
					"border": "#1e88e5",
					"highlight": {"background": "#bbdefb", "border": "#1565c0"},
				}
				shape = "box"
			else:
				color = {
					"background": "#fff3e0",
					"border": "#fb8c00",
					"highlight": {"background": "#ffe0b2", "border": "#ef6c00"},
				}
				shape = "ellipse"

			data = attrs.get("data", {})
			safe_data = _short_value(data)

			# Короткая подсказка вместо огромного JSON
			tooltip = json.dumps(safe_data, ensure_ascii=False)

			nodes.append({
				"id": node_id,
				"label": label,
				"title": escape(tooltip),
				"shape": shape,
				"color": color,
				"font": {"size": 14},
			})

		for source, target, attrs in self.graph.edges(data=True):
			edge_type = attrs.get("type", "")

			if edge_type == "contains":
				color = "#9e9e9e"
				dashes = True
				width = 1
			elif edge_type == "parent":
				color = "#1565c0"
				dashes = False
				width = 2
			elif edge_type == "link":
				color = "#2e7d32"
				dashes = False
				width = 2
			else:
				color = "#616161"
				dashes = False
				width = 1

			edges.append({
				"from": source,
				"to": target,
				"arrows": "to",
				"color": color,
				"dashes": dashes,
				"width": width,
				"title": edge_type,
				"smooth": False,  # быстрее, чем cubicBezier
			})

		nodes_json = json.dumps(nodes, ensure_ascii=False)
		edges_json = json.dumps(edges, ensure_ascii=False)

		return f"""
	<!doctype html>
	<html lang="ru">
	<head>
	  <meta charset="utf-8" />
	  <meta name="viewport" content="width=device-width, initial-scale=1" />
	  <title>Knowledge Graph</title>
	  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
	  <style>
	    html, body {{
	      margin: 0;
	      width: 100%;
	      height: 100%;
	      overflow: hidden;
	      font-family: Arial, sans-serif;
	      background: #f7f7f7;
	    }}
	    .toolbar {{
	      display: flex;
	      gap: 8px;
	      align-items: center;
	      padding: 10px 12px;
	      background: #fff;
	      border-bottom: 1px solid #ddd;
	      box-sizing: border-box;
	    }}
	    #search {{
	      padding: 8px 10px;
	      min-width: 320px;
	      border: 1px solid #ccc;
	      border-radius: 8px;
	      outline: none;
	    }}
	    button {{
	      padding: 8px 12px;
	      border: none;
	      border-radius: 8px;
	      background: #1976d2;
	      color: white;
	      cursor: pointer;
	    }}
	    #graph {{
	      width: 100%;
	      height: calc(100vh - 56px);
	      background: #fafafa;
	    }}
	    .hint {{
	      font-size: 13px;
	      color: #666;
	      margin-left: auto;
	    }}
	  </style>
	</head>
	<body>
	  <div class="toolbar">
	    <input id="search" type="text" placeholder="Поиск по узлу..." />
	    <button onclick="focusNode()">Найти</button>
	    <button onclick="resetView()">Сбросить</button>
	    <div class="hint">Двойной клик — центрировать</div>
	  </div>
	  <div id="graph"></div>

	  <script>
	    const nodes = new vis.DataSet({nodes_json});
	    const edges = new vis.DataSet({edges_json});

	    const network = new vis.Network(
	      document.getElementById("graph"),
	      {{ nodes, edges }},
	      {{
	        layout: {{
	          hierarchical: {{
	            enabled: true,
	            direction: "UD",
	            sortMethod: "directed",
	            levelSeparation: 160,
	            nodeSpacing: 120
	          }}
	        }},
	        physics: false,
	        interaction: {{
	          hover: false,
	          navigationButtons: true,
	          keyboard: true,
	          multiselect: false
	        }},
	        nodes: {{
	          borderWidth: 2,
	          shadow: false,
	          margin: 8
	        }},
	        edges: {{
	          arrows: {{
	            to: {{ enabled: true, scaleFactor: 0.8 }}
	          }},
	          smooth: false,
	          font: {{
	            size: 11,
	            align: "top"
	          }}
	        }}
	      }}
	    );

	    function focusNode() {{
	      const query = document.getElementById("search").value.trim().toLowerCase();
	      if (!query) return;

	      const allNodes = nodes.get();
	      const found = allNodes.find(n =>
	        String(n.id).toLowerCase().includes(query) ||
	        String(n.label || "").toLowerCase().includes(query)
	      );

	      if (found) {{
	        network.selectNodes([found.id]);
	        network.focus(found.id, {{
	          scale: 1.2,
	          animation: {{
	            duration: 300,
	            easingFunction: "easeInOutQuad"
	          }}
	        }});
	      }} else {{
	        alert("Узел не найден");
	      }}
	    }}

	    function resetView() {{
	      network.fit({{
	        animation: {{
	          duration: 300,
	          easingFunction: "easeInOutQuad"
	        }}
	      }});
	      network.unselectAll();
	      document.getElementById("search").value = "";
	    }}

	    network.on("doubleClick", function(params) {{
	      if (params.nodes.length > 0) {{
	        network.focus(params.nodes[0], {{
	          scale: 1.25,
	          animation: {{
	            duration: 250,
	            easingFunction: "easeInOutQuad"
	          }}
	        }});
	      }}
	    }});

	    document.getElementById("search").addEventListener("keydown", function(e) {{
	      if (e.key === "Enter") focusNode();
	    }});
	  </script>
	</body>
	</html>
	"""

	# -------------------------
	# Index helpers
	# -------------------------

	@staticmethod
	def _document_id(
			graph_id: str,
			index:    str,
	) -> str:
		return "1-1-1" # index # f"{graph_id}::[{index}]"

	@staticmethod
	def _node_id(
			graph_id: str,
			chunk:    WordChunk,
	) -> str:
		return chunk.norm # f"{graph_id}::{chunk.norm}"


	# -------------------------
	# Upsert document (Insert / Update)
	# -------------------------

	def upsert(
			self,
			doc:    dict,
			chunks: Dict[str, List[WordChunk]],
	):
		document_id: str = self._document_id("root", doc['id'])
		self.graph.add_node(
			document_id,
			label = doc['title'],
			type  = "SUBGRAPH",
			data = {
				"subgraph": build_struct_graph(doc),
			},
		)

		# ======================================================================
		# NODES
		# ======================================================================

		for fragment, chunk in chunks.items():
			self._upsert_nodes(
				chunk
			)

		# ======================================================================
		# EDGES
		# ======================================================================

		for fragment, chunk in chunks.items():
			self._upsert_edges(
				chunk, document_id=document_id, fragment_id=fragment,
			)

	def _upsert_nodes(
			self,
			chunks:   List[WordChunk],
			graph_id: str = "root",
	):
		for chunk in chunks:
			node_id: str   = self._node_id(graph_id, chunk)
			# text: str      = f"{chunk.text}" # f"({chunk.start}:{chunk.end})[t] - {chunk.text}"
			# text_norm: str = f"{chunk.norm}" # f"({chunk.start}:{chunk.end})[l] - {chunk.norm}"

			if not self.graph.has_node(node_id):
				self.graph.add_node(
					node_id,
					label = chunk.norm,
					type  = "TERM",
					data = {
						"type":  (chunk.chunk_type, chunk.lex_type),
						"level": chunk.level,
					},
				)
			else:

				pass

		pass

	def _upsert_edges(
			self,
			chunks:      List[WordChunk],
			graph_id:    str = "root",
			document_id: str = "",
			fragment_id: str = "",
	):
		for chunk in chunks:
			node_id: str   = self._node_id(graph_id, chunk)
			# text: str      = f"{chunk.text}" # f"({chunk.start}:{chunk.end})[t] - {chunk.text}"
			# text_norm: str = f"{chunk.norm}" # f"({chunk.start}:{chunk.end})[l] - {chunk.norm}"

			# ==================================================================
			# LINK
			# ==================================================================

			if chunk.link is not None:
				link_id: str = self._node_id(graph_id, chunk.link)

				if not self.graph.has_edge(node_id, link_id):
					self.graph.add_edge(
						node_id,
						link_id,
						label = "", # chunk.source.tokens[0].dep if chunk.source.tokens else ""
						type  = "link",
					)
				else:

					pass

				pass

			# ==================================================================
			# PARENT
			# ==================================================================

			if chunk.parent is not None:
				link_id: str = self._node_id(graph_id, chunk.parent)

				if not self.graph.has_edge(node_id, link_id):
					self.graph.add_edge(
						node_id,
						link_id,
						label = "",
						type  = "parent",
					)
				else:

					pass

				pass

			# ==================================================================
			# DOCUMENT
			# ==================================================================

			if True:

				if not self.graph.has_edge(node_id, document_id):
					self.graph.add_edge(
						node_id,
						document_id,
						label = "",
						type  = "contains",
						to = [
							fragment_id,
						],
					)
				else:
					self.graph.edges[
						node_id,
						document_id
					]["to"].append(fragment_id)

		pass


	# -------------------------
	# Delete document
	# -------------------------


	# -------------------------
	# Search document
	# -------------------------

	def _request_step(
			self,
			node_id: str,
	) -> Dict[str, Any]:
		result: Dict[str, Any] = {
			"data": {
				"nodes": [
					node_id,
				],
				"link": {
					"out": [],
					"in":  [],
				},
				"parent": {
					"out": [],
					"in":  [],
				},
			},
			"contains": {},
		}

		# ======================================================================
		# Узел уже просчитан
		# ======================================================================

		if node_id in self.stack:
			return self.stack[node_id]

		# ======================================================================
		# Узел не существует
		# ======================================================================

		if not self.graph.has_node(node_id):
			self.stack[node_id] = result
			return self.stack[node_id]

		self.stack[node_id] = result

		# ======================================================================
		# Исходящие связи
		# ======================================================================

		edges_out: Any = self.graph.out_edges(node_id, data=True)
		for edge in edges_out:
			node_edge_id: str              = edge[1]
			node_edge_data: Dict[str, Any] = edge[2]
			edge_type: str                 = node_edge_data.get("type", "")

			match edge_type:
				case "link":
					# ----------------------------------------------------------
					# LINK (Невостребованно)
					#
					# Связь между термином и его значением.
					# Текущий узел: Значение
					# ----------------------------------------------------------

					__append_unique__(
						result["data"]["link"]["out"],
						node_edge_id)
				case "parent":
					# ----------------------------------------------------------
					# PARENT
					#
					# Связь между родительским и дочерним узлом.
					# Текущий узел: Дочерний
					# ----------------------------------------------------------

					__append_unique__(
						result["data"]["parent"]["out"],
						node_edge_id)

					data = self._request_step(node_edge_id)

					# ==========================================================
					# MERGE DATA
					# ==========================================================

					__append_unique__(
						result["data"]["nodes"],
						data["data"]["nodes"])

					__append_unique__(
						result["data"]["link"]["out"],
						data["data"]["link"]["out"])
					__append_unique__(
						result["data"]["parent"]["out"],
						data["data"]["parent"]["out"])
					__append_unique__(
						result["data"]["link"]["in"],
						data["data"]["link"]["in"])
					__append_unique__(
						result["data"]["parent"]["in"],
						data["data"]["parent"]["in"])

					# ==========================================================
					# MERGE CONTAINS
					# ==========================================================

					for key, values in data["contains"].items():
						if key in result["contains"]:
							__append_unique__(
								result["contains"][key],
								values)
						else:
							result["contains"][key] = list(dict.fromkeys(values))
				case "contains":
					# ----------------------------------------------------------
					# CONTAINS
					#
					# Связь между документом и узлом графа.
					# Текущий узел: Узел графа
					# ----------------------------------------------------------

					to_nodes = node_edge_data.get("to", [])
					if not isinstance(to_nodes, list):
						to_nodes = [to_nodes]

					if node_edge_id in result["contains"]:
						__append_unique__(
							result["contains"][node_edge_id],
							to_nodes)
					else:
						result["contains"][node_edge_id] = to_nodes
				case _:
					pass

			# ==================================================================
			# Входящие связи
			# ==================================================================


			edges_in: Any = self.graph.in_edges(node_id, data=True)
			for edge in edges_in:
				node_edge_id: str              = edge[0]
				node_edge_data: Dict[str, Any] = edge[2]
				edge_type: str                 = node_edge_data.get("type", "")

				match edge_type:
					case "link":
						# ----------------------------------------------------------
						# LINK (Невостребованно)
						#
						# Связь между термином и его значением.
						# Текущий узел: Значение
						# ----------------------------------------------------------

						__append_unique__(
							result["data"]["link"]["in"],
							node_edge_id)
					case "parent":
						# ----------------------------------------------------------
						# PARENT (Невостребованно)
						#
						# Связь между родительским и дочерним узлом.
						# Текущий узел: Родительский
						# ----------------------------------------------------------

						__append_unique__(
							result["data"]["parent"]["in"],
							node_edge_id)
					case "contains":
						# ----------------------------------------------------------
						# CONTAINS (Невозможно)
						#
						# Связь между документом и узлом графа.
						# Текущий узел: Документ
						# ----------------------------------------------------------

						pass
					case _:
						pass

		return result

	def request(
			self,
			chunks: List[WordChunk],
	) -> List[Dict[str, Any]]:
		result: List[Dict[str, Any]] = []

		for chunk in chunks:
			node_id: str = self._node_id("root", chunk)

			node_result: Dict[str, Any]     = self._request_step(node_id)
			node_result["chunk"]: WordChunk = chunk

			result.append(node_result)

		return result





	@staticmethod
	def _empty_node_info(
			attrs: Dict[str, Any]
	) -> Dict[str, Any]:
		return {
			"label": attrs["label"],
			"type":  (
				attrs["type"],
				attrs["data"]["type"][0],
				attrs["data"]["type"][1],
				attrs["data"]["level"],
			),
			"in": {
				"link": [],
				"parent": [],
				"contains": [],
			},
			"out": {
				"link": [],
				"parent": [],
				"contains": [],
			},
			"documents": {},
		}




	# @staticmethod
	# def _fragment_matches(fragment_id: str, section_id: str) -> bool:
	# 	if not section_id:
	# 		return True
	#
	# 	return (
	# 		fragment_id == section_id
	# 		or section_id in fragment_id
	# 		or f"[{section_id}]" in fragment_id
	# 	)
	#
	# @classmethod
	# def _documents_in_scope(
	# 		cls,
	# 		documents: Dict[str, List[str]],
	# 		document_id: Optional[str] = None,
	# 		section_id: Optional[str] = None,
	# ) -> Dict[str, List[str]]:
	# 	result: Dict[str, List[str]] = {}
	#
	# 	for doc_id, fragments in (documents or {}).items():
	# 		if document_id is not None and doc_id != document_id:
	# 			continue
	#
	# 		if not isinstance(fragments, list):
	# 			fragments = [fragments]
	#
	# 		if section_id is None:
	# 			result[doc_id] = list(dict.fromkeys(fragments))
	# 			continue
	#
	# 		matched = [
	# 			fragment_id
	# 			for fragment_id in fragments
	# 			if cls._fragment_matches(fragment_id, section_id)
	# 		]
	#
	# 		if matched:
	# 			result[doc_id] = list(dict.fromkeys(matched))
	#
	# 	return result
	#
	# def _scope_nodes(
	# 		self,
	# 		all_nodes: Dict[str, Dict[str, Any]],
	# 		document_id: Optional[str] = None,
	# 		section_id: Optional[str] = None,
	# ) -> Dict[str, Dict[str, Any]]:
	# 	result: Dict[str, Dict[str, Any]] = {}
	#
	# 	for node_id, info in all_nodes.items():
	# 		documents = self._documents_in_scope(
	# 			info.get("documents", {}),
	# 			document_id=document_id,
	# 			section_id=section_id,
	# 		)
	#
	# 		if documents:
	# 			item = {
	# 				**info,
	# 				"documents": documents,
	# 			}
	# 			result[node_id] = item
	#
	# 	return result
	#
	# def _parent_component(
	# 		self,
	# 		seed_ids: Set[str],
	# 		all_nodes: Dict[str, Dict[str, Any]],
	# 		scope_ids: Set[str],
	# ) -> Set[str]:
	# 	"""
	# 	Расширение по parent-связям в обе стороны:
	# 	in.parent + out.parent
	# 	"""
	# 	result = set(seed_ids)
	# 	stack = list(seed_ids)
	#
	# 	while stack:
	# 		node_id = stack.pop()
	# 		info = all_nodes.get(node_id)
	# 		if not info:
	# 			continue
	#
	# 		related = set(info["in"]["parent"]) | set(info["out"]["parent"])
	#
	# 		for nxt in related:
	# 			if nxt in scope_ids and nxt not in result:
	# 				result.add(nxt)
	# 				stack.append(nxt)
	#
	# 	return result
	#
	# def _neighbor_nodes(
	# 		self,
	# 		seed_ids: Set[str],
	# 		all_nodes: Dict[str, Dict[str, Any]],
	# 		scope_ids: Set[str],
	# ) -> Set[str]:
	# 	"""
	# 	Соседи по link-связям:
	# 	in.link + out.link
	# 	"""
	# 	result = set(seed_ids)
	#
	# 	for node_id in list(seed_ids):
	# 		info = all_nodes.get(node_id)
	# 		if not info:
	# 			continue
	#
	# 		related = set(info["in"]["link"]) | set(info["out"]["link"])
	#
	# 		for nxt in related:
	# 			if nxt in scope_ids:
	# 				result.add(nxt)
	#
	# 	return result
	#
	# def _select_by_predicate(
	# 		self,
	# 		predicate,
	# 		document_id: Optional[str] = None,
	# 		section_id: Optional[str] = None,
	# 		include_parents: bool = False,
	# ) -> Dict[str, Dict[str, Any]]:
	# 	all_nodes = self.get_all_nodes()
	# 	scoped_nodes = self._scope_nodes(
	# 		all_nodes,
	# 		document_id=document_id,
	# 		section_id=section_id,
	# 	)
	#
	# 	scope_ids = set(scoped_nodes.keys())
	# 	seed_ids = {
	# 		node_id
	# 		for node_id, info in scoped_nodes.items()
	# 		if predicate(node_id, info)
	# 	}
	#
	# 	if include_parents:
	# 		seed_ids = self._parent_component(seed_ids, all_nodes, scope_ids)
	#
	# 	return {node_id: scoped_nodes[node_id] for node_id in seed_ids}


	@staticmethod
	def _normalize_scope(
			scope: Optional[
				Union[
					List[str],
					Dict[str, List[str]]
				]] = None,
	) -> Optional[Dict[str, Optional[Set[str]]]]:
		if not scope:
			return None

		if isinstance(scope, list):
			return {doc_id: None for doc_id in scope}

		if isinstance(scope, dict):
			result: Dict[str, Optional[Set[str]]] = {}
			for doc_id, sections in scope.items():
				if not sections:
					result[doc_id] = None
				else:
					result[doc_id] = set(sections)
			return result

		raise TypeError("")

	@classmethod
	def _documents_in_scope(
			cls,
			documents: Dict[str, List[str]],
			scope: Optional[
				Union[
					List[str],
					Dict[str, List[str]]
				]] = None,
	) -> Dict[str, List[str]]:
		normalized = cls._normalize_scope(scope)
		if normalized is None:
			return {
				doc_id:
					list(
						dict.fromkeys(
							fragments if isinstance(fragments, list) else [fragments]
						))
				for doc_id, fragments in (documents or {}).items()
			}

		result: Dict[str, List[str]] = {}

		for doc_id, fragments in (documents or {}).items():
			if doc_id not in normalized:
				continue

			if not isinstance(fragments, list):
				fragments = [fragments]

			allowed_sections = normalized[doc_id]

			if allowed_sections is None:
				result[doc_id] = list(dict.fromkeys(fragments))
			else:
				filtered = [f for f in fragments if f in allowed_sections or any(s in f for s in allowed_sections)]
				if filtered:
					result[doc_id] = list(dict.fromkeys(filtered))

		return result

	def _scope_nodes(
			self,
			nodes: Dict[str, Dict[str, Any]],
			scope: Optional[
				Union[
					List[str],
					Dict[str, List[str]]
				]] = None,
	) -> Dict[str, Dict[str, Any]]:
		result: Dict[str, Dict[str, Any]] = {}

		for node_id, info in nodes.items():
			documents = self._documents_in_scope(info.get("documents", {}), scope=scope)
			if documents:
				result[node_id] = {
					**info,
					"documents": documents,
				}

		return result

	@staticmethod
	def _parent_component(
			seed_ids: Set[str],
			all_nodes: Dict[str, Dict[str, Any]],
			scope_ids: Set[str],
	) -> Set[str]:
		result = set(seed_ids)
		stack = list(seed_ids)

		while stack:
			node_id = stack.pop()
			info = all_nodes.get(node_id)
			if not info:
				continue

			related = set(info["in"]["parent"]) | set(info["out"]["parent"])
			for nxt in related:
				if nxt in scope_ids and nxt not in result:
					result.add(nxt)
					stack.append(nxt)

		return result

	@staticmethod
	def _neighbor_nodes(
			seed_ids: Set[str],
			all_nodes: Dict[str, Dict[str, Any]],
			scope_ids: Set[str],
	) -> Set[str]:
		result = set(seed_ids)

		for node_id in list(seed_ids):
			info = all_nodes.get(node_id)
			if not info:
				continue

			related = set(info["in"]["link"]) | set(info["out"]["link"])
			for nxt in related:
				if nxt in scope_ids:
					result.add(nxt)

		return result

	def _select_by_predicate(
			self,
			predicate,
			scope: Optional[
				Union[
					List[str],
					Dict[str, List[str]]
				]] = None,
			include_parents: bool = False,
	) -> Dict[str, Dict[str, Any]]:
		all_nodes = self.get_all_nodes()
		scoped_nodes = self._scope_nodes(all_nodes, scope=scope)

		scope_ids = set(scoped_nodes.keys())
		seed_ids = {
			node_id
			for node_id, info in scoped_nodes.items()
			if predicate(node_id, info)
		}

		if include_parents:
			seed_ids = self._parent_component(seed_ids, all_nodes, scope_ids)

		return {node_id: scoped_nodes[node_id] for node_id in seed_ids}



	def _get_all_nodes(self) -> Dict[str, Dict[str, Any]]:
		result: Dict[str, Dict[str, Any]] = {}

		# 1) Инициализируем все узлы
		for node_id, attrs in self.graph.nodes(data=True):
			if attrs.get("type") == "SUBGRAPH":
				continue
			result[node_id] = self._empty_node_info(attrs)

		# 2) Обходим все ребра
		for source, target, attrs in self.graph.edges(data=True):
			edge_type = attrs.get("type", "")

			if edge_type == "link":
				if target not in result[source]["out"]["link"]:
					result[source]["out"]["link"].append(target)
				if source not in result[target]["in"]["link"]:
					result[target]["in"]["link"].append(source)

			elif edge_type == "parent":
				if target not in result[source]["out"]["parent"]:
					result[source]["out"]["parent"].append(target)
				if source not in result[target]["in"]["parent"]:
					result[target]["in"]["parent"].append(source)

			elif edge_type == "contains":
				fragments = attrs.get("to", [])
				if not isinstance(fragments, list):
					fragments = [fragments]

				if target not in result[source]["documents"]:
					result[source]["documents"][target] = []

				for fragment_id in fragments:
					if fragment_id not in result[source]["documents"][target]:
						result[source]["documents"][target].append(fragment_id)

		return result

	def get_all_nodes(
			self,
			scope: Optional[
				Union[
					List[str],
					Dict[str, List[str]]
				]] = None,
			include_parents: bool = False,
	) -> Dict[str, Dict[str, Any]]:
		nodes = self._get_all_nodes()
		scoped_nodes = self._scope_nodes(nodes, scope=scope)

		if not include_parents:
			return scoped_nodes

		scope_ids = set(scoped_nodes.keys())
		expanded_ids = self._parent_component(scope_ids, nodes, scope_ids)
		return {node_id: scoped_nodes[node_id] for node_id in expanded_ids}

	def get_terms(
			self,
	        scope: Optional[Union[List[str], Dict[str, List[str]]]] = None,
			include_parents: bool = False,
	) -> Dict[str, Dict[str, Any]]:
		return self._select_by_predicate(
			lambda _node_id, info: len(info["in"]["link"]) > 0,
			scope           = scope,
			include_parents = include_parents,
		)

	def get_values(
			self,
			scope: Optional[Union[List[str], Dict[str, List[str]]]] = None,
			include_parents: bool = False,

	) -> Dict[str, Dict[str, Any]]:
		return self._select_by_predicate(
			lambda _node_id, info: len(info["out"]["link"]) > 0,
			scope=scope,
			include_parents=include_parents,
		)

	def get_neighbors(
			self,
			node_ids: Iterable[str] | str,
			scope: Optional[Union[List[str], Dict[str, List[str]]]] = None,
			include_parents: bool = False,
	) -> Dict[str, Dict[str, Any]]:
		if isinstance(node_ids, str):
			node_ids = [node_ids]

		all_nodes = self._get_all_nodes()
		scoped_nodes = self._scope_nodes(all_nodes, scope=scope)

		scope_ids = set(scoped_nodes.keys())
		seed_ids = {nid for nid in node_ids if nid in scope_ids}

		if include_parents:
			neighbor_ids = self._neighbor_nodes(seed_ids, all_nodes, scope_ids)
			ids = self._parent_component(neighbor_ids, all_nodes, scope_ids)
		else:
			ids = self._neighbor_nodes(seed_ids, all_nodes, scope_ids)

		return {node_id: scoped_nodes[node_id] for node_id in ids}
