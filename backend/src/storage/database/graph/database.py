from enum import Enum
from typing import Dict, List, Set, Tuple, Any, Optional

import networkx as nx
from networkx.classes.reportviews import OutEdgeDataView, InEdgeDataView, OutEdgeView

from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk
from backend.src.storage.database.graph.constructor.struct_graph import build_struct_graph
from backend.src.storage.utils.utils import __append_unique__


class Direction(Enum):
	NONE = 0
	UP   = 1
	DOWN = 2


class GraphStorage:
	def __init__(self):
		self.graph = nx.DiGraph()

		self.stack: Dict[str, Dict[str, Any]] = {}


	# -------------------------
	# Index helpers
	# -------------------------

	@staticmethod
	def _document_id(
			graph_id: str,
			index:    str,
	) -> str:
		return index # f"{graph_id}::[{index}]"

	@staticmethod
	def _node_id(
			graph_id: str,
			chunk:    WordChunk,
	) -> str:
		return f"{graph_id}::{chunk.norm}"


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



	# def get_node(
	# 		self,
	# 		chunk:    WordChunk,
	# 		graph_id: str = "root",
	# ) -> Dict[str, Any] | None:
	# 	node_id = self._node_id(graph_id, chunk)
	# 	if not self.graph.has_node(node_id):
	# 		return None
	# 	return self.graph.nodes[node_id]
	#
	# def neighbors(
	# 		self,
	# 		chunk: WordChunk,
	# 		graph_id: str = "root",
	# ) -> List[str]:
	# 	node_id = self._node_id(graph_id, chunk)
	# 	if not self.graph.has_node(node_id):
	# 		return []
	# 	return list(
	# 		set(self.graph.successors(node_id)) |
	# 		set(self.graph.predecessors(node_id))
	# 	)



	# 	if not
	# 		self.graph.add_node(
	# 			node_id,
	# 			label=text_norm,
	# 			type="TERM",
	# 			data={
	# 				"text": text,
	# 				"norm": text_norm,
	# 				"type": (chunk.chunk_type, chunk.lex_type),
	# 				"level": chunk.level,
	# 			},
	# 		)


	# 	for n, data in self.graph.nodes(data=True):
	# 		if not n.startswith(graph_id):
	# 			continue
	#
	# 		if data.get("type") != "TERM":
	# 			continue
	#
	# 		if data["data"]["norm"] == norm:
	# 			result.append(n)
	#
	# 	return result
	#
	# def get_fragment_nodes(
	# 		self,
	# 		graph_id: str,
	# 		fragment: str,
	# ) -> List[str]:
	#
	# 	fid = self._fragment_id(graph_id, fragment)
	#
	# 	if not self.graph.has_node(fid):
	# 		return []
	#
	# 	return list(self.graph.successors(fid))
	#
	# # -------------------------
	# # GRAPH NEIGHBORS
	# # -------------------------
	#
	# def neighbors(self, node_id: str, depth: int = 1) -> Set[str]:
	# 	visited = set()
	# 	current = {node_id}
	#
	# 	for _ in range(depth):
	# 		next_nodes = set()
	# 		for n in current:
	# 			next_nodes.update(self.graph.successors(n))
	# 			next_nodes.update(self.graph.predecessors(n))
	#
	# 		visited.update(next_nodes)
	# 		current = next_nodes
	#
	# 	return visited




