from pathlib import Path
from typing import List, Dict, Tuple, Any, Union, Iterable, cast, Optional

import numpy as np
from spacy.tokens import Doc

from backend.src.common.annotation.llm.llm_client import OpenAIClient
from backend.src.common.annotation.nlp.extractors.extractor import ChunkExtractor
from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk
from backend.src.common.encoder.encoder import EncoderWrapper
from backend.src.common.extractor.extractor import ExtractorWrapper
from backend.src.config import AnnotatorConfig
from backend.src.docs.handler import DocumentHandler
from backend.src.storage.database.storage import Storage
from backend.src.storage.utils.utils import __report_progress__


class Annotator:
	def __init__(
			self,
			path_to_data: Path,
			client:       Optional[OpenAIClient] = None,
			storage:      Optional[Storage]      = None,
			config:       AnnotatorConfig        = AnnotatorConfig(),
	):
		"""

		:param path_to_data:
		:param storage:
		:param config:
		"""

		self.handler:   DocumentHandler  = DocumentHandler()
		self.extractor: ExtractorWrapper = ExtractorWrapper(config)
		self.encoder:   EncoderWrapper   = EncoderWrapper(config)

		self.config:  AnnotatorConfig        = config
		self.client:  Optional[OpenAIClient] = client
		self.storage: Optional[Storage]      = storage
		self.config.path_to_data = path_to_data

	def set_client(
			self,
			client: OpenAIClient,
	):
		self.client = client

	def set_storage(
			self,
			storage: Storage,
	):
		self.storage = storage


	# ==========================================================================
	# Preprocessing
	# ==========================================================================

	def preprocessing_document(
			self,
			path_to_document: str,
			report_file:      str = "",
	) -> Dict[str, Any]:
		"""

		:param path_to_document:
		:param report_file:
		:return:
		"""

		data: Dict[str, Any] = self.handler.parse(
			path_to_document,
		)

		if report_file:
			__report_progress__(
				data,
				self.config.path_to_data,
				report_file,
			)
		return data

	@staticmethod
	def preprocessing_request(
			query: str,
	) -> str:
		"""

		:param query:
		:return:
		"""

		return query

	@staticmethod
	def request_preprocessing(
			query: str,
	) -> str:
		"""

		:param query:
		:return:
		"""

		return Annotator.preprocessing_request(
			query,
		)


	# ==========================================================================
	# Processing
	# ==========================================================================

	def processing_document(
			self,
			data:        Dict[str, Any] = None,
			report_file: str            = "",
	) -> Tuple[
		Dict[str, List[WordChunk]],
		Dict[str, np.ndarray],
	]:
		"""

		:param data:
		:param report_file:
		:return:
		"""

		if data is not None:
			self.handler.doc = data

		if "sections" in self.handler.doc:
			section = self.handler.doc["sections"][0]

			(
				self.handler.word_chunks,
				self.handler.embeddings,
			) = self._processing(
				section
			)

		if report_file:
			__report_progress__(
				self.handler.doc,
				self.config.path_to_data,
				report_file,
			)
		return (
			self.handler.word_chunks,
			self.handler.embeddings,
		)

	def processing_request(
			self,
			query: str,
	) -> Tuple[
		List[WordChunk],
		np.ndarray,
	]:
		"""

		:param query:
		:return:
		"""

		# ======================================================================
		# Выделение терминов и значений (WordChunk)
		# ======================================================================

		word_chunks: List[WordChunk] = ChunkExtractor(
			self.extractor.process(query),
			self.config.include_subchunks,
		).extract()

		# ======================================================================
		# Вычисление текстового вектора (Embedding)
		# ======================================================================

		embedding: np.ndarray = self.encoder.process(
			query,
		)

		return (
			word_chunks,
			embedding,
		)

	def request_processing(
			self,
			query: str,
	) -> Tuple[
		List[WordChunk],
		np.ndarray,
	]:
		"""

		:param query:
		:return:
		"""

		return self.processing_request(
			query,
		)


	# ==========================================================================
	# Postprocessing
	# ==========================================================================

	def postprocessing_document(
			self,
			data:        Dict[str, Any]             = None,
			word_chunks: Dict[str, List[WordChunk]] = None,
			embeddings:  Dict[str, np.ndarray]      = None,
	):
		"""

		:param data:
		:param word_chunks:
		:param embeddings:
		:return:
		"""

		if data is not None:
			self.handler.doc = data
		if word_chunks is not None:
			self.handler.word_chunks = word_chunks
		if embeddings is not None:
			self.handler.embeddings = embeddings

		self.storage.upsert(
			self.handler.doc,
			self.handler.word_chunks,
			self.handler.embeddings,
		)

	def postprocessing_request(
			self,
			word_chunks: List[WordChunk],
			embedding:   np.ndarray,
	) -> Dict[str, Any]:
		"""

		:param word_chunks:
		:param embedding:
		:return:
		"""

		pass

	def request_postprocessing(
			self,
			word_chunks: List[WordChunk],
			embedding:   np.ndarray,
	) -> Dict[str, Any]:
		"""

		:param word_chunks:
		:param embedding:
		:return:
		"""

		pass


	# ==========================================================================
	# Работа с документами
	# ==========================================================================

	def get_handler(self) -> DocumentHandler:
		return self.handler

	def update_flags(
			self,
			target_id:   Union[str, Iterable[str]],
			include:     Optional[bool] = None,
			process:     Optional[bool] = None,
			merge:       bool           = False,
			clear:       bool           = False,
			report_file: str            = "",
	) -> int:
		"""

		:param target_id:
		:param include:
		:param process:
		:param merge:
		:param clear:
		:param report_file:
		:return:
		"""

		count: int = self.handler.update_flags(
			target_id,
			include = include,
			process = process,
			merge   = merge,
			clear   = clear,
		)

		if report_file:
			__report_progress__(
				self.handler.doc,
				self.config.path_to_data,
				report_file,
			)
		return count

	def clear(
			self,
			report_file: str = "",
	):
		"""

		:param report_file:
		:return:
		"""

		self.handler.clear()

		if report_file:
			__report_progress__(
				self.handler.doc,
				self.config.path_to_data,
				report_file,
			)
		return


	# ==========================================================================
	# Вспомогательные методы
	# ==========================================================================

	def _processing(
			self,
			section: Dict[str, Any],
	) -> Tuple[
		Dict[str, List[WordChunk]],
		Dict[str, np.ndarray],
	]:
		"""

		:param section:
		:return:
		"""

		word_chunks: Dict[str, List[WordChunk]] = {}
		embeddings:  Dict[str, np.ndarray]      = {}

		paragraphs = section.get("paragraphs", [])
		if paragraphs:
			self._processing_section(
				section,
				paragraphs,
				word_chunks,
				embeddings,
			)

		sections = section.get("sections", [])
		if sections:
			for it in sections:
				data = self._processing(it)
				word_chunks.update(data[0])
				embeddings.update(data[1])

		return (
			word_chunks,
			embeddings
		)

	def _processing_section(
			self,
			section:     Dict[str, Any],
			paragraphs:  List[Dict[str, Any]],
			word_chunks: Dict[str, List[WordChunk]],
			embeddings:  Dict[str, np.ndarray],
	):
		"""

		:param section:
		:param paragraphs:
		:param word_chunks:
		:param embeddings:
		:return:
		"""

		texts: List[str] = [
			p.get("text", "")
			for p in paragraphs
		]

		title:   str              = section.get("title", "")
		content: str              = "\n".join(texts)
		docs:    List[Doc]        = list(self.extractor.pipe(texts))
		embs:    List[np.ndarray] = list(self.encoder.pipe(texts))

		# ======================================================================
		# Выделение параграфов
		# ======================================================================

		if title or content:
			section_chunks:	List[WordChunk] \
				= []
			section_embedding: np.ndarray \
				= self.encoder.process(
				f"""
				{title}
				{content}
				"""
			)

			for it, doc, embedding in zip(paragraphs, docs, embs):
				chunks = ChunkExtractor(
					doc,
					self.config.include_subchunks
				).extract()
				section_chunks.extend(chunks)

				word_chunks[it.get("id")] = chunks
				embeddings[it.get("id")]  = embedding

				if self.config.include_markup:
					it["stack"]["chunks"] = [
						f"({chunk.start}:{chunk.end}) {chunk.text}"
						for chunk in chunks
					]
					it["embedding"] = embedding.tolist()

			word_chunks[section.get("id")] = section_chunks
			embeddings[section.get("id")]  = section_embedding

			if self.config.include_markup:
				section["embedding"] = section_embedding.tolist()


# ======================================================================
# Выделение мелких фрагментов (абзац)
# ======================================================================
#
# docs: List[Doc]        = list(self.extractor.pipe(texts))
# embs: List[np.ndarray] = list(self.encoder.pipe(texts))
#
# for it, doc, embedding in zip(paragraphs, docs, embs):
# 	chunks = ChunkExtractor(
# 		doc,
# 		self.config.include_subchunks
# 	).extract()
#
# 	word_chunks[it.get("id")] = chunks
# 	embeddings[it.get("id")]  = embedding
#
# 	if self.config.include_markup:
# 		it["stack"]["chunks"] = [
# 			f"({chunk.start}:{chunk.end}) {chunk.text}"
# 			for chunk in chunks
# 		]
# 		it["embedding"] = embedding.tolist()
#
#
# ======================================================================
# Выделение крупных фрагментов (параграф)
# ======================================================================
#
# title:   str = section.get("title", "")
# content: str = "\n".join(texts)
#
# if title or content:
# 	embeddings[section.get("id") + "|" + "title"]   = self.encoder.process(title)
# 	embeddings[section.get("id") + "|" + "content"] = self.encoder.process(content)
#
# 	if self.config.include_markup:
# 		section["embedding"] = {
# 			"title":   embeddings[section.get("id") + "|" + "title"].tolist(),
# 			"content": embeddings[section.get("id") + "|" + "content"].tolist(),
# 		}
#
# elif self.config.include_markup:
# 	section["embedding"] = {
# 		"title":   self.encoder.process("").tolist(),
# 		"content": self.encoder.process("").tolist(),
# 	}



