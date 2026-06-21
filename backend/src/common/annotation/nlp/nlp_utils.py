from typing import List

from spacy.tokens import Doc

from backend.src.common.annotation.nlp.extractors.noun_chunks import NounChunkExtractor
from backend.src.common.annotation.nlp.extractors.noun_subchunks import NounSubchunkExtractor
from backend.src.common.annotation.nlp.utils.noun_chunk import NounChunk


class NLPUtils:

	@staticmethod
	def merge_terms(doc: Doc) -> Doc:
		with doc.retokenize() as retokenizer:
			i = 0
			while i < len(doc) - 2:
				t1, t2, t3 = doc[i], doc[i + 1], doc[i + 2]

				if (
						t2.text == "-"
						and t1.is_alpha
						and t3.is_alpha
						and t1.whitespace_ == ""
				):
					span = doc[i: i + 3]
					retokenizer.merge(span)
					i += 1
				else:
					i += 1
		return doc

	@staticmethod
	def extract_noun_chunks(doc: Doc, include_subchunks: bool = False) -> List[NounChunk]:
		chunks: List[NounChunk] = NounChunkExtractor(doc).extract()
		subchunks: List[NounChunk] = []

		if include_subchunks:
			for chunk in chunks:
				subchunks.extend(
					NounSubchunkExtractor(chunk, True).extract()
				)
			chunks.extend(subchunks)

		chunks.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return chunks

	@staticmethod
	def extract_noun_subchunks(chunk: NounChunk, include_single_tokens: bool = True) -> List[NounChunk]:
		chunks: List[NounChunk] = NounSubchunkExtractor(chunk, include_single_tokens).extract()
		chunks.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return chunks

# 	# @staticmethod
# 	# def noun_chunks(doc: Doc, include_subchunks: bool = False) -> List[NounChunk]:
# 	# 	chunks: List[NounChunk] = NLPUtils.extract_noun_chunks(doc, include_subchunks)
# 	# 	subchunk: List[NounChunk] = []
# 	#
# 	# 	# if include_subchunks:
# 	# 	# 	for chunk in chunks:
# 	# 	# 		subchunk.extend(NLPUtils.extract_noun_subchunks(chunk))
# 	# 	# 	chunks.extend(subchunk)
# 	#
# 	# 	chunks.sort(key=lambda c: (c.span.start, c.span.end))
# 	# 	return chunks
# 	# 	# return NLPUtils.dedupe_noun_chunks(chunks)
#
# 	# @staticmethod
# 	# def dedupe_noun_chunks(chunks: List[NounChunk]) -> List[NounChunk]:
# 	#
# 	# 	# 1. Группировка
# 	# 	groups: Dict[Tuple[int, int], List[NounChunk]] = defaultdict(list)
# 	# 	for ch in chunks:
# 	# 		key = (ch.span.start, ch.span.end)
# 	# 		groups[key].append(ch)
# 	#
# 	#
# 	#
# 	#
# 	#
# 	# 	# 2. выбор "лучшего" в каждой группе
# 	# 	best_map: Dict[NounChunk, NounChunk] = {}
# 	#
# 	# 	for group in groups.values():
# 	# 		if len(group) == 1:
# 	# 			best = group[0]
# 	# 		else:
# 	# 			roots = [g for g in group if g.c_type == 1]
# 	# 			if roots:
# 	# 				best = min(roots, key=lambda c: c.c_level)
# 	# 			else:
# 	# 				best = min(group, key=lambda c: (c.c_type, c.c_level))
# 	# 		for g in group:
# 	# 			best_map[g] = best
# 	#
# 	# 	# 3. перестройка parent-ссылок
# 	# 	new_chunks = []
# 	# 	for ch in chunks:
# 	# 		best = best_map[ch]
# 	#
# 	# 		# если это не лучший — пропускаем (удаляем)
# 	# 		if ch is not best:
# 	# 			continue
# 	#
# 	# 		parent = ch.parent
# 	#
# 	# 		# перепривязка родителя
# 	# 		if parent is not None:
# 	# 			parent = best_map.get(parent, parent)
# 	#
# 	# 			# защита от самоссылки
# 	# 			if parent is ch:
# 	# 				parent = None
# 	#
# 	# 		new_chunks.append(
# 	# 			NounChunk(
# 	# 				span=ch.span,
# 	# 				parent=parent,
# 	# 				c_level=ch.c_level,
# 	# 				c_type=ch.c_type
# 	# 			)
# 	# 		)
# 	#
# 	# 	# 4. сортировка по тексту
# 	# 	new_chunks.sort(key=lambda c: (c.span.start, c.span.end))
# 	# 	return new_chunks
#
#
#
#
#
# # import networkx as nx
# # from typing import List, Optional
# # from extractor.tokens import Doc
# #
# # from docs.nlp.utils.noun_chunk import NounChunk
# # from docs.nlp.nlp_utils import NLPUtils
# #
# #
# # def build_content_graph(doc: dict):
# #     G = nx.DiGraph()
# #
# #     def _build_section(doc_id: str, parent_id: str, section: dict):
# #         sec_id = section["id"]
# #
# #         for subsection in section.get("sections", []):
# #             _build_section(doc_id, sec_id, subsection)
# #
# #         for paragraph in section.get("paragraphs", []):
# #             _build_paragraph(doc_id, sec_id, paragraph)
# #
# #     def _build_paragraph(doc_id: str, parent_id: str, paragraph: dict):
# #         pr_id = paragraph["id"]
# #
# #         text = paragraph["src_text"]
# #         doc = paragraph["proc_text"]
# #
# #         chunks: List[NounChunk] = process_text(doc)
# #         chunks.sort(key=lambda c: (c.span.start, c.span.end, c.c_type, c.c_level))
# #
# #         print(text)
# #         print("=" * 100)
# #         for chunk in chunks:
# #             print(chunk)
# #         print()
# #
# #         para_node_id = get_paragraph_node_id(doc_id, pr_id)
# #         if para_node_id not in G:
# #             G.add_node(
# #                 para_node_id,
# #                 label=f"PARAGRAPH::{pr_id}",
# #                 type="PARAGRAPH",
# #                 level=0,
# #             )
# #
# #         for ch in chunks:
# #             _add_chunk_node(doc_id, pr_id, ch)
# #
# #         prev_main_chunk_id: Optional[str] = None
# #         for ch in chunks:
# #             prev_main_chunk_id = _add_chunk_edge(
# #                 doc_id=doc_id,
# #                 parent_id=pr_id,
# #                 chunk=ch,
# #                 paragraph_node_id=para_node_id,
# #                 prev_main_chunk_id=prev_main_chunk_id,
# #             )
# #
# #     def _add_chunk_node(doc_id: str, parent_id: str, chunk: NounChunk):
# #         node_id = get_chunk_id(doc_id, parent_id, chunk)
# #
# #         if node_id not in G:
# #             G.add_node(
# #                 node_id,
# #                 label=f"{node_id} :: {chunk.span.text}",
# #                 type=f"CHUNK::T{chunk.c_type}",
# #                 level=chunk.c_level,
# #             )
# #
# #         return node_id
# #
# #     def _add_chunk_edge(
# #         doc_id: str,
# #         parent_id: str,
# #         chunk: NounChunk,
# #         paragraph_node_id: str,
# #         prev_main_chunk_id: Optional[str] = None,
# #     ) -> Optional[str]:
# #         chunk_id = get_chunk_id(doc_id, parent_id, chunk)
# #
# #         if chunk.c_type == 1:
# #             # Корневой chunk не удаляем и всегда привязываем к параграфу
# #             G.add_edge(paragraph_node_id, chunk_id, type="main")
# #
# #             # Связь между соседними root-chunk'ами через промежуточный узел
# #             if prev_main_chunk_id is not None:
# #                 rel_node_id = get_rel_node_id(doc_id, parent_id, prev_main_chunk_id, chunk_id)
# #
# #                 if rel_node_id not in G:
# #                     G.add_node(
# #                         rel_node_id,
# #                         label="REL::main_to_main",
# #                         type="REL",
# #                         level=0,
# #                     )
# #
# #                 G.add_edge(prev_main_chunk_id, rel_node_id, type="seq")
# #                 G.add_edge(rel_node_id, chunk_id, type="seq")
# #
# #             return chunk_id
# #
# #         else:
# #             if chunk.parent is None:
# #                 return prev_main_chunk_id
# #
# #             parent_chunk_id = get_chunk_id(doc_id, parent_id, chunk.parent)
# #             G.add_edge(parent_chunk_id, chunk_id, type="sub")
# #             return prev_main_chunk_id
# #
# #     for section in doc.get("sections", []):
# #         _build_section(doc["id"], doc["id"], section)
# #
# #     return G
# #
# #
# # def get_paragraph_node_id(doc_id: str, paragraph_id: str) -> str:
# #     return f"{doc_id}::PAR::{paragraph_id}"
# #
# #
# # def get_rel_node_id(doc_id: str, parent_id: str, left_chunk_id: str, right_chunk_id: str) -> str:
# #     return f"{doc_id}::{parent_id}::REL::{left_chunk_id}__{right_chunk_id}"
# #
# #
# # def get_chunk_id(doc_id: str, parent_id: str, chunk: NounChunk) -> str:
# #     return f"{doc_id}::[{chunk.span.text}, {chunk.span.start}:{chunk.span.end}]-T{chunk.c_type}-L{chunk.c_level}"
# #
# #
# # def process_text(doc: Doc) -> List[NounChunk]:
# #     return NLPUtils.noun_chunks(doc, True)