import threading
from typing import Dict, List, Any, Optional, OrderedDict, Sequence

import numpy as np

# from backend.src.common.annotation.annotator import Annotator
from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk
from backend.src.docs.file.file_utils import FileIO
from backend.src.storage.database.graph.database import GraphStorage
from backend.src.storage.database.postgres.database import PostgresStore
from backend.src.storage.utils.utils import __append_unique__


class Storage:
	def __init__(self, file_path: str):
		# self.annotator: Optional[Annotator] = None
		self.graph    = GraphStorage()
		self.database = PostgresStore()

		self._lock = threading.RLock()
		self.file_path: str = file_path
		self._global_index = None
		self._global_dirty = True

		self._candidate_cache: OrderedDict[str, object] = OrderedDict()

	# def set_annotator(
	# 		self,
	# 		annotator: Annotator,
	# ):
	# 	self.annotator = annotator


	# -------------------------
	# Search document
	# -------------------------

	def request(
			self,
			word_chunks: List[WordChunk],
			embedding:   np.ndarray,
			top_k:       int = 10,
	):
		# ======================================================================
		# Шаг 1: Графовый поиск
		# ======================================================================

		result: List[Dict[str, Any]] = self.graph.request(word_chunks)

		contains: Dict[str, Any] = {}
		for chunk in result:
			for key, value in chunk["contains"].items():
				if key in contains:
					__append_unique__(contains[key], value)
				else:
					contains[key] = value

		for key, value in contains.items():
			self.database.set_active(key, value, True)

		# ======================================================================
		# Шаг 2: Embedding + BM25
		# ======================================================================

		res = self.database.search(embedding, active_only=True, limit=top_k)
		self.database.clear_active()

		# ======================================================================
		# Шаг 3: Дополнение результатов
		# ======================================================================

		result: Dict[str, Any] = {}
		for r in res:
			result[f"({r[0]}:{r[1]})"] = {
				"document": r[0],
				"target":   r[1],
				"score":    r[2],
			}

		data = FileIO.read(self.file_path)


		def _update_data(node: Dict[str, Any]):
			node_id: str = f"({data.get('id')}:{node.get('id')})"

			if node_id in result:
				result[node_id]["text"] = node["text"]

			# Paragraph
			for p in node.get("paragraphs", []):
				_update_data(p)

			# Section
			for s in node.get("sections", []):
				_update_data(s)

		_update_data(data)
		return result


	# -------------------------
	# Upsert document (Insert / Update)
	# -------------------------

	def upsert(
			self,
			data:        Dict[str, Any],
			word_chunks: Dict[str, List[WordChunk]],
			embeddings:  Dict[str, np.ndarray],
	):
		self.graph.upsert(data, word_chunks)
		self.database.upsert(data, embeddings, False)


	# -------------------------
	# Delete document
	# -------------------------


	# ==========================================================================
	# Вспомогательные методы
	# ==========================================================================

	# def add_texts(self, ids: Sequence[str]) -> None:
	# 	"""Добавляет тексты в список поиска."""
	#
	# 	self.storage.set_active(ids, active=True)
	# 	self._mark_dirty()
	# 	self._clear_candidate_cache()



	def _mark_dirty(self) -> None:
		with self._lock:
			self._global_dirty = True

	def _clear_candidate_cache(self) -> None:
		with self._lock:
			self._candidate_cache.clear()



		# # ======================================================================
		# # Шаг 1: Графовый поиск
		# # ======================================================================
		#
		# result: List[Dict[str, Any]] = self.graph.request(word_chunks)
		#
		# contains: Dict[str, Any] = {}
		# for chunk in result:
		# 	for key, value in chunk["contains"].items():
		# 		if key in contains:
		# 			__append_unique__(contains[key], value)
		# 		else:
		# 			contains[key] = value
		#
		# for key, value in contains.items():
		# 	self.database.set_active(key, value, True)
		#
		# res = self.database.search(embedding, active_only=True)
		# self.database.clear_active()
		#
		# # ======================================================================
		# # Шаг 2: Embedding + BM25
		# # ======================================================================
