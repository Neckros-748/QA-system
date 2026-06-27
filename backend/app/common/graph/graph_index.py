from typing import Dict, List, Set, Any, Optional, Union, Iterable

import spacy
from spacy.language import Language
from spacy.tokens import Doc
import networkx as nx

from app.common.graph.nlp.nlp_utils import NLPUtils
from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.common.graph.constructor.struct_graph import build_struct_graph
from app.storage.utils.utils import __append_unique__
from app.config import Config


class GraphIndex:
	def __init__(
			self,
			config: Config,
	):
		self.graph:  nx.DiGraph = nx.DiGraph()
		self.config: Config     = config

		self.model: Language = spacy.load(
			config.model_name["spacy"],
			disable = self.config.disable if self.config.disable else []
		)

		self.stack: Dict[str, Dict[str, Any]] = {}


	# ==========================================================================
	# Методы обработки
	# ==========================================================================

	def process(
			self,
			text: str,
	) -> Doc:
		return NLPUtils.merge_terms(
			self.model(text)
		)

	def pipe(
			self,
			texts: List[str],
	) -> Iterable[Doc]:
		docs = self.model.pipe(
			texts,
			batch_size = self.config.batch_size,
			n_process  = self.config.n_process,
		)
		for doc in docs:
			yield NLPUtils.merge_terms(doc)


	# ==========================================================================
	# Вспомогательные методы
	# ==========================================================================

	@staticmethod
	def _document_id(
			graph_id: str,
			index:    str,
	) -> str:
		return index

	@staticmethod
	def _node_id(
			graph_id: str,
			chunk:    WordChunk,
	) -> str:
		return chunk.norm


	# ==========================================================================
	# Upsert document (Insert / Update)
	# ==========================================================================

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
			data  = {
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
			node_id: str = self._node_id(graph_id, chunk)
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
				node_data = self.graph.nodes[node_id]

				cur_type = node_data.get("data", {}).get("type", (-1, -1))
				if chunk.chunk_type.value < cur_type[0].value:
					node_data["data"]["type"] = (chunk.chunk_type, chunk.lex_type)

				cur_level = node_data.get("data", {}).get("level", -1)
				if chunk.level > cur_level:
					node_data["data"]["level"] = chunk.level

	def _upsert_edges(
			self,
			chunks:      List[WordChunk],
			graph_id:    str = "root",
			document_id: str = "",
			fragment_id: str = "",
	):
		for chunk in chunks:
			node_id: str = self._node_id(graph_id, chunk)

			# ==================================================================
			# LINK (Термин <- Значение)
			# ==================================================================

			if chunk.link is not None:
				link_id: str = self._node_id(graph_id, chunk.link)
				if not self.graph.has_edge(node_id, link_id):
					self.graph.add_edge(
						node_id,
						link_id,
						label = "",
						type  = "link",
					)

			# ==================================================================
			# PARENT (Родительский <- Дочерний)
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

			# ==================================================================
			# CONTAINS (Документ/Фрагмент <- Узел)
			# ==================================================================

			if document_id:
				if not self.graph.has_edge(node_id, document_id):
					self.graph.add_edge(
						node_id,
						document_id,
						label = "",
						type  = "contains",
						to    = [fragment_id] if fragment_id else [],
					)
				else:
					edge_data = self.graph.edges[node_id, document_id]
					if "to" not in edge_data:
						edge_data["to"] = []
					if fragment_id and fragment_id not in edge_data["to"]:
						edge_data["to"].append(fragment_id)


	# ==========================================================================
	# Delete document
	# ==========================================================================


	# ==========================================================================
	# Search document
	# ==========================================================================

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

	def search(
			self,
			chunks: List[WordChunk],
			top_k: int = 10,
			epsilon: float = 1e-8
	) -> List[Dict[str, Any]]:
		# ==========================================================================
		# 1. Построение множеств запроса V_q и E_q
		# ==========================================================================

		V_q = set()
		E_q = set()

		# Собираем уникальные нормы (идентификаторы узлов)

		for chunk in chunks:
			V_q.add(chunk.norm)

		# Рёбра: link и parent (только если оба узла присутствуют в V_q)
		for chunk in chunks:
			if chunk.link is not None and chunk.link.norm in V_q:
				edge = tuple(sorted((chunk.norm, chunk.link.norm)))
				E_q.add(edge)
			if chunk.parent is not None and chunk.parent.norm in V_q:
				edge = tuple(sorted((chunk.norm, chunk.parent.norm)))
				E_q.add(edge)

		# ==========================================================================
		# 2. Получение всех узлов графа (только термины, не SUBGRAPH)
		# ==========================================================================

		all_nodes = self._get_all_nodes()
		term_nodes = {
			node_id: info
			for node_id, info in all_nodes.items()
			if info.get('type') and info['type'][0] != 'SUBGRAPH'
		}

		if not term_nodes:
			return []

		# ==========================================================================
		# 3. Построение индекса смежности (для рёбер)
		# ==========================================================================

		adjacency = {}  # node_id -> set of neighbor node_ids
		for node_id, info in term_nodes.items():
			neighbors = set()
			# Исходящие связи
			neighbors.update(info.get('out', {}).get('link', []))
			neighbors.update(info.get('out', {}).get('parent', []))
			# Входящие связи (для неориентированного представления)
			neighbors.update(info.get('in', {}).get('link', []))
			neighbors.update(info.get('in', {}).get('parent', []))
			adjacency[node_id] = neighbors

		# ==========================================================================
		# 4. Сбор фрагментов и их терминов/рёбер
		# ==========================================================================

		fragment_terms = {}  # fragment_id -> set of node_ids
		fragment_edges = {}  # fragment_id -> set of edge tuples
		fragment_doc = {}  # fragment_id -> doc_id

		for node_id, info in term_nodes.items():
			for doc_id, fragments in info.get('documents', {}).items():
				for frag_id in fragments:
					if frag_id not in fragment_terms:
						fragment_terms[frag_id] = set()
						fragment_edges[frag_id] = set()
						fragment_doc[frag_id] = doc_id
					fragment_terms[frag_id].add(node_id)

		# Для каждого фрагмента добавляем рёбра между его терминами
		for frag_id, terms in fragment_terms.items():
			edges = fragment_edges[frag_id]
			for node in terms:
				for neighbor in adjacency.get(node, set()):
					if neighbor in terms:
						edge = tuple(sorted((node, neighbor)))
						edges.add(edge)

		# ==========================================================================
		# 5. Вычисление оценок
		# ==========================================================================

		denom = len(V_q) + len(E_q) + epsilon
		results = []

		for frag_id, V_f in fragment_terms.items():
			inter_vertices = len(V_q & V_f)
			inter_edges = len(E_q & fragment_edges.get(frag_id, set()))
			score = (inter_vertices + inter_edges) / denom

			if score > 0:
				results.append({
					'id': frag_id,
					'metadata': {'doc_id': fragment_doc.get(frag_id, '')},
					'score': score
				})

		# ==========================================================================
		# 6. Сортировка и ограничение по top_k
		# ==========================================================================

		results.sort(key=lambda x: x['score'], reverse=True)
		return results[:top_k]

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

	@staticmethod
	def _normalize_scope(
			scope: Optional[Union[List[str], Dict[str, List[str]]]] = None,
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
