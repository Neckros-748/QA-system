from pathlib import Path
from typing import Dict, List, Any, Optional, OrderedDict, Sequence
#
# import numpy as np
#
from app.common.graph.nlp.utils.word_chunk import WordChunk
# from backend.app.docs.file.file_utils import FileIO
# from backend.app.storage.database.graph.database import GraphStorage
# from backend.app.storage.database.postgres.database import PostgresStore
# from backend.app.storage.utils.utils import __append_unique__

from app.config import AnnotatorConfig

from app.common.graph.graph_index import GraphStorage
from app.common.lexical.lexical_index import BM25Index


# from app.common.graph.nlp.nlp_utils import NLPUtils


# from app.storage.database.graph.database import GraphStorage
# from app.storage.database.postgres.database import PostgresStore


class Storage:
	def __init__(
			self,
			file_path: str,
			config: AnnotatorConfig = AnnotatorConfig(),
	):
		self.file_path: str                  = file_path
		self.documents: list[dict[str, Any]] = []

		self.graph_index:   GraphStorage = GraphStorage(config)
		self.lexical_index: BM25Index    = BM25Index(
			storage_path = Path(file_path).parent / "bm25")
		self.lexical_index.load()
		self.vector_index  = None

		# self.extractor: ExtractorWrapper = ExtractorWrapper
		# self.encoder:   EncoderWrapper   = EncoderWrapper(config)

	# ==========================================================================
	# Upsert document (Insert / Update)
	# ==========================================================================

	def upsert(
			self,
			data:        Dict[str, Any],
			word_chunks: Dict[str, List[WordChunk]],
	):
		self.graph_index.upsert(data, word_chunks)

		if "sections" in data:
			data_meta = {
				"id":         data["id"],
				"title":      data["title"],
				"created_at": data["created_at"],
			}
			self._upsert_section(data_meta, data)

	# 		self.database.upsert(data, embeddings, False)
	def _upsert_section(
			self,
			data_meta: Dict[str, Any],
			section:   Dict[str, Any],
	):
		paragraphs = section.get("paragraphs", [])
		if paragraphs:
			self._upsert_paragraph(
				data_meta, section, paragraphs,
			)

		sections = section.get("sections", [])
		if sections:
			for it in sections:
				self._upsert_section(data_meta, it)

	def _upsert_paragraph(
			self,
			data_meta:  Dict[str, Any],
			section:    Dict[str, Any],
			paragraphs: List[Dict[str, Any]],
	):
		texts: List[str] = [
			p.get("text", "")
			for p in paragraphs
		]

		title:   str              = section.get("title", "")
		content: str              = "\n".join(texts)
		# 	docs:    List[Doc]        = list(self.extractor.pipe(texts))
		# 	embs:    List[np.ndarray] = list(self.encoder.pipe(texts))

		# ======================================================================
		# Выделение параграфов
		# ======================================================================

		texts: List[Dict[str, Any]] = []
		if title or content:
			if section["id"] != "sct_h0:1":
				texts.append({
					"doc_id": data_meta["id"],
					"id":     section["id"],
					"text":   f"{title}\n{content}".strip(),
				})

			for p in paragraphs:
				texts.append({
					"doc_id": data_meta["id"],
					"id":     section["id"],
					"text":   p["text"],
				})

		# Добавляем в лексический индекс
		if texts:
			self.lexical_index.add_texts(texts, text_field="text")
			self.lexical_index.save()






	def request(
			self,
			query:       str,
			word_chunks: List[WordChunk],
			top_k:       int = 10,
	):


		return {
			"graph_index": self.graph_index.search(word_chunks, top_k=top_k),
			"lexical_index": self.lexical_index.search(query, top_k),
		}


# 		# ======================================================================
# 		# Шаг 1: Графовый поиск
# 		# ======================================================================
#
# 		result: List[Dict[str, Any]] = self.graph.request(word_chunks)
#
# 		contains: Dict[str, Any] = {}
# 		for chunk in result:
# 			for key, value in chunk["contains"].items():
# 				if key in contains:
# 					self._append_unique(contains[key], value)
# 				else:
# 					contains[key] = value
#
# 		for key, value in contains.items():
# 			self.database.set_active(key, value, True)
#
# 		res = self.database.search(embedding, active_only=True)
# 		self.database.clear_active()
#
# 		# ======================================================================
# 		# Шаг 2: Embedding + BM25
# 		# ======================================================================
#
# 		return res





# 		self.graph    = GraphStorage()
# 		self.database = PostgresStore()
# 		# cur.execute("SET ivfflat.probes = 10;")
# 		# embedding   vector(384),
#  # "data/graph/graph_view.html"
#
# 		self.lock = threading.RLock()
#
#
#
#
# 	# -------------------------
# 	# Delete document
# 	# -------------------------
#
#
#
# 	@staticmethod
# 	def _append_unique(
# 			target: List[str],
# 			value:  List[str] | str,
# 	) -> None:
# 		if isinstance(value, list):
# 			for v in value:
# 				if v not in target:
# 					target.append(v)
# 		elif isinstance(value, str):
# 			if value not in target:
# 				target.append(value)
#
#
#
# 	# g = app.storage.graph.search(word_chunks)
#
# 	# embedding: np.ndarray = app.annotator.encoder.process(query)
# 	#
# 	# res = app.storage.database.search(embedding, active_only=False)
#
# # if title or content:
# # 	embeddings[cur.get("id") + "|" + "title"] = self.encoder.process(title)
# # 	embeddings[cur.get("id") + "|" + "content"] = self.encoder.process(content)
#
#
# # id - документ
# # документ - структуру
# # word_chunk - документ / фрагмент документа
# # embedding - документ / фрагмент документа
# #
# #
# #
#
#
# #
# # app.graph.draw_graph()

