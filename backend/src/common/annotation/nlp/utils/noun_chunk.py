from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.src.common.annotation.nlp.utils.text_chunk import TextChunk


@dataclass
class NounChunk:
	source:  TextChunk
	parent:  Optional[NounChunk] = None
	c_type:  int = -1    # 1 = noun_chunk; 2, 3 = subchunk; 4 = not subchunk
	c_level: int = -1    # глубина (0 — корневой chunk)

	# Type = 1 : noun_chunk     - основной чанк текста / термин
	# Type = 2 : subchunk       - подчанк основного чанка (Type = 1) текста
	# Type = 3 : subchunk       - подчанк нижнего уровня
	# Type = 4 : not subchunk   - подчанк основного чанка текста (Type = 2), но не входящий в основной чанк (Type = 1)

	def __repr__(self):
		if self.c_type == 1:
			return f"{self.source.text}"
		return f"T{self.c_type} : L{self.c_level} : {self.source.text}"



# 	def extract(self) -> List[WordChunk]:
# 		noun_chunks = self._extract_noun_chunks()

#
# 		# 1) Сначала строим узлы из noun chunks
# 		for chunk in sorted(
# 			noun_chunks,
# 			key=lambda c: (c.c_type, c.c_level, c.source.start, c.source.end),
# 		):
# 			key = self._chunk_key(chunk.source)
#
# 			parent_node = None
# 			if chunk.parent is not None:
# 				parent_key = self._chunk_key(chunk.parent.source)
# 				parent_node = node_by_key.get(parent_key)
#
# 			node = self._make_word_chunk(
# 				source=chunk.source,
# 				parent=parent_node,
# 				c_type=chunk.c_type,
# 				c_level=chunk.c_level,
# 			)
#
# 			nodes.append(node)
# 			node_by_key[key] = node
# 			source_link_by_key[key] = chunk.source.link
# 			covered.update(t.i for t in chunk.source.tokens)
#
#
# 		nodes.sort(key=lambda c: (c.start, c.end, c.c_type, c.c_level))
# 		return nodes






#
#
# 	def _make_word_chunk(
# 		self,
# 		source: TextChunk,
# 		parent: Optional[WordChunk],
# 		c_type: int,
# 		c_level: int,
# 	) -> WordChunk:
# 		# WordChunk не должен падать на source.link != -1,
# 		# поэтому в сам WordChunk кладём копию source с link=-1,
# 		# а связь восстанавливаем позже через _resolve_links().
# 		detached_source = TextChunk(tokens=source.tokens, link=-1)
#
# 		return WordChunk(
# 			source=detached_source,
# 			parent=parent,
# 			c_type=c_type,
# 			c_level=c_level,
# 		)
#



# def add_document(self, doc: dict, spans: Dict[str, List[WordChunk]]):
# 	doc_id = str(doc.get("id", doc.get("doc_id", "doc")))
#
# 	node_by_objid: Dict[int, str] = {}
# 	node_by_key: Dict[Tuple[int, int, str], str] = {}
#
# 	# 1)
# 	for spans_key, spans_value in spans.items():
# 		self._process_nodes(
# 			doc_id=doc_id,
# 			group_key=spans_key,
# 			spans=spans_value,
# 			node_by_objid=node_by_objid,
# 			node_by_key=node_by_key,
# 		)
#
# 	# 2) Рёбра
# 	for spans_key, spans_value in spans.items():
# 		self._process_edges(
# 			doc_id=doc_id,
# 			group_key=spans_key,
# 			spans=spans_value,
# 			node_by_objid=node_by_objid,
# 			node_by_key=node_by_key,
# 		)
#
# def _process_nodes(
# 		self,
# 		doc_id: str,
# 		group_key: str,
# 		spans: List[WordChunk],
# 		node_by_objid: Dict[int, str],
# 		node_by_key: Dict[Tuple[int, int, str], str],
# ):
# 	for chunk in spans:
# 		node_id = self._index_of(doc_id, group_key, chunk)
# 		key = self._chunk_key(chunk)
#
# 		if not self.graph.has_node(node_id):
# 			self.graph.add_node(
# 				node_id,
# 				data={
# 					"text": chunk.text,
# 					"norm": chunk.norm,
# 					"start": chunk.start,
# 					"end": chunk.end,
# 					"c_type": chunk.c_type,
# 					"c_level": chunk.c_level,
# 				},
# 				label=chunk.text,
# 				type="TERM",
# 				level=(chunk.c_type, chunk.c_level),
# 			)
#
# 		node_by_objid[id(chunk)] = node_id
# 		node_by_key[key] = node_id
#
# def _process_edges(
# 		self,
# 		doc_id: str,
# 		group_key: str,
# 		spans: List[WordChunk],
# 		node_by_objid: Dict[int, str],
# 		node_by_key: Dict[Tuple[int, int, str], str],
# ):
# 	for chunk in spans:
# 		source_id = self._resolve_node_id(chunk, node_by_objid, node_by_key)
# 		if source_id is None:
# 			continue
#
# 		# parent -> child
# 		if chunk.parent is not None:
# 			target_id = self._resolve_node_id(chunk.parent, node_by_objid, node_by_key)
# 			if target_id is not None and source_id != target_id:
# 				self._add_edge_once(
# 					source_id=target_id,
# 					target_id=source_id,
# 					relation="parent",
# 				)
#
# 		# link -> target
# 		if chunk.link is not None:
# 			target_id = self._resolve_node_id(chunk.link, node_by_objid, node_by_key)
# 			if target_id is not None and source_id != target_id:
# 				self._add_edge_once(
# 					source_id=source_id,
# 					target_id=target_id,
# 					relation="link",
# 				)
#
# def _resolve_node_id(
# 		self,
# 		chunk: WordChunk,
# 		node_by_objid: Dict[int, str],
# 		node_by_key: Dict[Tuple[int, int, str], str],
# ) -> Optional[str]:
# 	obj_id = node_by_objid.get(id(chunk))
# 	if obj_id is not None:
# 		return obj_id
#
# 	return node_by_key.get(self._chunk_key(chunk))
#
# def _add_edge_once(self, source_id: str, target_id: str, relation: str):
# 	if self.graph.has_edge(source_id, target_id):
# 		existing = self.graph[source_id][target_id]
# 		relations = existing.get("relations", set())
# 		if not isinstance(relations, set):
# 			relations = set(relations if isinstance(relations, list) else [relations])
# 		relations.add(relation)
# 		existing["relations"] = relations
# 		return
#
# 	self.graph.add_edge(
# 		source_id,
# 		target_id,
# 		relation=relation,
# 		relations={relation},
# 	)




