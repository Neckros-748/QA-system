from pathlib import Path
from typing import List, Dict, Tuple, Any, Union, Iterable, cast, Optional

import numpy as np
from spacy.tokens import Doc


from app.common.graph.nlp.extractors.extractor import ChunkExtractor
from app.common.graph.nlp.utils.word_chunk import WordChunk
# from backend.app.common.encoder.encoder import EncoderWrapper
# from backend.app.common.extractor.extractor import ExtractorWrapper
from app.docs.handler import DocumentHandler
from app.storage.storage import Storage
from app.config import AnnotatorConfig
from app.storage.utils.utils import __report_progress__



class Annotator:
	def __init__(
			self,
			path_to_data: Path,
			storage:      Optional[Storage] = None,
			config:       AnnotatorConfig   = AnnotatorConfig(),
	):
		"""

		:param path_to_data:
		:param storage:
		:param config:
		"""

		self.handler:   DocumentHandler  = DocumentHandler()
		# self.extractor: ExtractorWrapper = ExtractorWrapper(config)
		# self.encoder:   EncoderWrapper   = EncoderWrapper(config)

		self.config:  AnnotatorConfig        = config
		self.storage: Optional[Storage]      = storage
		self.config.path_to_data = path_to_data

	def set_storage(
			self,
			storage: Storage,
	):
		self.storage = storage

	def get_handler(self) -> DocumentHandler:
		return self.handler


	# ==========================================================================
	# Preprocessing
	# ==========================================================================

	def preprocessing_document(
			self,
			document:    str | dict[str, Any],
			report_file: str = "",
	) -> Dict[str, Any]:
		data: Dict[str, Any] = self.handler.parse(document)

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
		return query

	@staticmethod
	def request_preprocessing(
			query: str,
	) -> str:
		return Annotator.preprocessing_request(
			query,
		)

	def update_flags(
			self,
			target_id:   Union[str, Iterable[str]],
			include:     Optional[bool] = None,
			process:     Optional[bool] = None,
			merge:       bool           = False,
			clear:       bool           = False,
			report_file: str            = "",
	) -> int:
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
		self.handler.clear()

		if report_file:
			__report_progress__(
				self.handler.doc,
				self.config.path_to_data,
				report_file,
			)

	# ==========================================================================
	# Processing
	# ==========================================================================

	def processing_document(
			self,
			data:        Dict[str, Any] = None,
			report_file: str            = "",
	) -> Dict[str, List[WordChunk]]:
		if data is not None:
			self.handler.doc = data

		if "sections" in self.handler.doc:
			section                  = self.handler.doc["sections"][0]
			self.handler.word_chunks = self._processing_section(section)

		if report_file:
			__report_progress__(
				self.handler.doc,
				self.config.path_to_data,
				report_file,
			)
		return self.handler.word_chunks

	def processing_request(
			self,
			query: str,
	) -> List[WordChunk]:
		word_chunks: List[WordChunk] = ChunkExtractor(
			self.storage.graph_index.process(query),
			self.config.include_subchunks,
		).extract()

		return word_chunks

	def request_processing(
			self,
			query: str,
	) -> List[WordChunk]:
		return self.processing_request(query)

	def _processing_section(
			self,
			section: Dict[str, Any],
	) -> Dict[str, List[WordChunk]]:
		word_chunks: Dict[str, List[WordChunk]] = {}

		paragraphs = section.get("paragraphs", [])
		if paragraphs:
			self._processing_paragraph(
				section, paragraphs, word_chunks,
			)

		sections = section.get("sections", [])
		if sections:
			for it in sections:
				data = self._processing_section(it)
				word_chunks.update(data)

		return word_chunks

	def _processing_paragraph(
			self,
			section:     Dict[str, Any],
			paragraphs:  List[Dict[str, Any]],
			word_chunks: Dict[str, List[WordChunk]],
	):
		texts: List[str] = [
			p.get("text", "")
			for p in paragraphs
		]

		title: str = section.get("title", "")
		content: str = "\n".join(texts)
		docs: List[Doc] = list(self.storage.graph_index.pipe(texts))

		# ======================================================================
		# Выделение параграфов
		# ======================================================================

		if title or content:
			section_chunks: List[WordChunk] = []

			for it, doc in zip(paragraphs, docs):
				chunks = ChunkExtractor(
					doc,
					self.config.include_subchunks
				).extract()

				word_chunks[it.get("id")] = chunks
				section_chunks.extend(chunks)

				if self.config.include_markup:
					it["stack"]["chunks"] = [
						f"({chunk.start}:{chunk.end}) {chunk.text}"
						for chunk in chunks
					]

			if section["id"] != "sct_h0:1":
				word_chunks[section.get("id")] = section_chunks

	# ==========================================================================
	# Postprocessing
	# ==========================================================================

	def postprocessing_document(
			self,
			data:        Dict[str, Any]             = None,
			word_chunks: Dict[str, List[WordChunk]] = None,
	):
		if data is not None:
			self.handler.doc = data
		if word_chunks is not None:
			self.handler.word_chunks = word_chunks

		self.storage.upsert(
			self.handler.doc,
			self.handler.word_chunks,
		)






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












	#
	# def processing_document(
	# 		self,
	# 		data:        Dict[str, Any] = None,
	# 		report_file: str            = "",
	# ) -> Tuple[
	# 	Dict[str, List[WordChunk]],
	# 	Dict[str, np.ndarray],
	# ]:
	#
	# 	if data is not None:
	# 		self.handler.doc = data
	#
	# 	if "sections" in self.handler.doc:
	# 		section = self.handler.doc["sections"][0]
	# 		data    = self._processing_section(section)
	# 		self.handler.word_chunks = data[0]
	# 		self.handler.embeddings  = data[1]
	#
	# 	if report_file:
	# 		__report_progress__(
	# 			self.handler.doc,
	# 			self.config.path_to_data,
	# 			report_file,
	# 		)
	# 	return (
	# 		self.handler.word_chunks,
	# 		self.handler.embeddings,
	# 	)

	# 	def processing_request(
	# 			self,
	# 			query: str,
	# 	) -> Tuple[
	# 		List[WordChunk],
	# 		np.ndarray,
	# 	]:
	# 		"""
	#
	# 		:param query:
	# 		:return:
	# 		"""
	#
	# 		# ======================================================================
	# 		# Выделение терминов и значений (WordChunk)
	# 		# ======================================================================
	#
	# 		word_chunks: List[WordChunk] = ChunkExtractor(
	# 			self.extractor.process(query),
	# 			self.config.include_subchunks,
	# 		).extract()
	#
	# 		# ======================================================================
	# 		# Вычисление текстового вектора (Embedding)
	# 		# ======================================================================
	#
	# 		embedding: np.ndarray = self.encoder.process(
	# 			query,
	# 		)
	#
	# 		return (
	# 			word_chunks,
	# 			embedding,
	# 		)
	#
	# 	def request_processing(
	# 			self,
	# 			query: str,
	# 	) -> Tuple[
	# 		List[WordChunk],
	# 		np.ndarray,
	# 	]:
	# 		"""
	#
	# 		:param query:
	# 		:return:
	# 		"""
	#
	# 		return self.processing_request(
	# 			query,
	# 		)



# 	# ==========================================================================
# 	# Вспомогательные методы
# 	# ==========================================================================
#
# 	def _processing_section(
# 			self,
# 			section: Dict[str, Any],
# 	) -> Tuple[
# 		Dict[str, List[WordChunk]],
# 		Dict[str, np.ndarray],
# 	]:
# 		word_chunks: Dict[str, List[WordChunk]] = {}
# 		embeddings:  Dict[str, np.ndarray]      = {}
#
#
#
#
#
# 		paragraphs = section.get("paragraphs", [])
# 		if paragraphs:
# 			self._processing_paragraph(
# 				section,
# 				paragraphs,
# 				word_chunks,
# 			)
#
# 		sections = section.get("sections", [])
# 		if sections:
# 			for it in sections:
# 				data = self._processing_section(it)
# 				word_chunks.update(data[0])
# 				embeddings.update(data[1])
#
# 		return (
# 			word_chunks,
# 			embeddings
# 		)
#
# 	def _processing_paragraph(
# 			self,
# 			section:     Dict[str, Any],
# 			paragraphs:  List[Dict[str, Any]],
# 			word_chunks: Dict[str, List[WordChunk]],
# 	):
# 		texts: List[str] = [
# 			p.get("text", "")
# 			for p in paragraphs
# 		]
#
# 		title:   str              = section.get("title", "")
# 		content: str              = "\n".join(texts)
#
#
#
# 		docs:    List[Doc]        = list(self.extractor.pipe(texts))
# 		embs:    List[np.ndarray] = list(self.encoder.pipe(texts))
#
# 		# ======================================================================
# 		# Выделение параграфов
# 		# ======================================================================
#
# 		if title or content:
# 			section_chunks:	List[WordChunk] \
# 				= []
# 			section_embedding: np.ndarray \
# 				= self.encoder.process(
# 				f"""
# 				{title}
# 				{content}
# 				"""
# 			)
#
# 			for it, doc, embedding in zip(paragraphs, docs, embs):
# 				chunks = ChunkExtractor(
# 					doc,
# 					self.config.include_subchunks
# 				).extract()
# 				section_chunks.extend(chunks)
#
# 				word_chunks[it.get("id")] = chunks
# 				embeddings[it.get("id")]  = embedding
#
# 				if self.config.include_markup:
# 					it["stack"]["chunks"] = [
# 						f"({chunk.start}:{chunk.end}) {chunk.text}"
# 						for chunk in chunks
# 					]
# 					it["embedding"] = embedding.tolist()
#
# 			word_chunks[section.get("id")] = section_chunks
# 			embeddings[section.get("id")]  = section_embedding
#
# 			if self.config.include_markup:
# 				section["embedding"] = section_embedding.tolist()
# #
# #
# # # ======================================================================
# # # Выделение мелких фрагментов (абзац)
# # # ======================================================================
# # #
# # # docs: List[Doc]        = list(self.extractor.pipe(texts))
# # # embs: List[np.ndarray] = list(self.encoder.pipe(texts))
# # #
# # # for it, doc, embedding in zip(paragraphs, docs, embs):
# # # 	chunks = ChunkExtractor(
# # # 		doc,
# # # 		self.config.include_subchunks
# # # 	).extract()
# # #
# # # 	word_chunks[it.get("id")] = chunks
# # # 	embeddings[it.get("id")]  = embedding
# # #
# # # 	if self.config.include_markup:
# # 		it["stack"]["chunks"] = [
# # 			f"({chunk.start}:{chunk.end}) {chunk.text}"
# # 			for chunk in chunks
# # 		]
# # 		it["embedding"] = embedding.tolist()
# #
# #
# # ======================================================================
# # Выделение крупных фрагментов (параграф)
# # ======================================================================
# #
# # title:   str = section.get("title", "")
# # content: str = "\n".join(texts)
# #
# # if title or content:
# # 	embeddings[section.get("id") + "|" + "title"]   = self.encoder.process(title)
# # 	embeddings[section.get("id") + "|" + "content"] = self.encoder.process(content)
# #
# # 	if self.config.include_markup:
# # 		section["embedding"] = {
# # 			"title":   embeddings[section.get("id") + "|" + "title"].tolist(),
# # 			"content": embeddings[section.get("id") + "|" + "content"].tolist(),
# # 		}
# #
# # elif self.config.include_markup:
# # 	section["embedding"] = {
# # 		"title":   self.encoder.process("").tolist(),
# # 		"content": self.encoder.process("").tolist(),
# # 	}


#
#
#
# 	def postprocessing_request(
# 			self,
# 			word_chunks: List[WordChunk],
# 			embedding:   np.ndarray,
# 	) -> Dict[str, Any]:
# 		"""
#
# 		:param word_chunks:
# 		:param embedding:
# 		:return:
# 		"""
#
# 		pass
#
# 	def request_postprocessing(
# 			self,
# 			word_chunks: List[WordChunk],
# 			embedding:   np.ndarray,
# 	) -> Dict[str, Any]:
# 		"""
#
# 		:param word_chunks:
# 		:param embedding:
# 		:return:
# 		"""
#
# 		pass
#
#
#
#



