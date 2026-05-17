from pathlib import Path
from typing import List, Dict, Any, Tuple, Union, Iterable, Optional

import numpy as np
from spacy.tokens import Doc

from backend.src.common.encoder.encoder_wrapper import EncoderProcessor
from backend.src.common.spacy.spacy_wrapper import SpacyProcessor
from backend.src.common.annotation.nlp.extractors.extractor import WordChunkExtractor
from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk
from backend.src.config import SpacyConfig, EncoderConfig
from backend.src.docs.handler import DocumentHandler
from backend.src.storage.database.storage import Storage
from backend.src.storage.storage import AppStorage
from backend.src.storage.utils.utils import __report_progress__


class Annotator:
	def __init__(
			self,
			path_to_data: Path,
	):
		self.path_to_data: Path            = path_to_data
		self.storage: Optional[Storage]    = None

		self.handler: DocumentHandler      = DocumentHandler()
		self.spacy:   SpacyProcessor       = SpacyProcessor(SpacyConfig())
		self.encoder: EncoderProcessor     = EncoderProcessor(str(self.path_to_data), EncoderConfig())

		self.include_subchunks: bool = True
		self.include_markup: bool    = True

	def set_storage(
			self,
			storage: Storage,
	):
		self.storage = storage


	# ==========================================================================
	# Preprocessing
	# ==========================================================================

	def document_preprocessing(
			self,
			path_to_document: str,
			report_file:      str = "",
	):
		print("Document Preprocessing...")

		data: Dict[str, Any] = self.handler.parse(path_to_document)

		if report_file:
			__report_progress__(data, self.path_to_data, report_file)
		return data

	@staticmethod
	def request_preprocessing(
			query: str,
	) -> str:
		print("Request Preprocessing...")

		return query


	# ==========================================================================
	# Processing
	# ==========================================================================

	def document_processing(
			self,
			doc:         Dict[str, Any] = None,
			report_file: str            = "",
	) -> Tuple[
		Dict[str, List[WordChunk]],
		Dict[str, np.ndarray],
	]:
		print("Document Processing...")

		# print("Pipeline:", self.spacy.model.pipe_names)

		if doc is None:
			doc = self.handler.doc

		if "sections" in doc:
			data = self._processing_section(doc["sections"][0])
			self.handler.word_chunks = data[0]
			self.handler.embeddings  = data[1]

		# for chunk in word_chunks:
		# 	print(chunk, word_chunks[chunk])
		# print()
		#
		# for chunk in embeddings:
		# 	print(chunk, embeddings[chunk])
		# print()

		# displacy.serve(self.doc, style="dep", page=True)

		if report_file:
			__report_progress__(self.handler.doc, self.path_to_data, report_file)
		return (
			self.handler.word_chunks,
			self.handler.embeddings
		)

	def request_processing(
			self,
			query: str,
	) -> Tuple[
		List[WordChunk],
		np.ndarray,
	]:
		print("Request Processing...")

		# ----------------------------------------------------------------------
		# Шаг 1:
		# Выделение терминов и значений (WordChunk)
		# ----------------------------------------------------------------------

		word_chunks: List[WordChunk] = WordChunkExtractor(
			self.spacy.process(query),
			self.include_subchunks
		).extract()

		# ----------------------------------------------------------------------
		# Шаг 2:
		# Вычисление текстового вектора (Embedding)
		# ----------------------------------------------------------------------

		embedding: np.ndarray = self.encoder.process(
			query
		)

		return (
			word_chunks,
			embedding
		)


	# ==========================================================================
	# Postprocessing
	# ==========================================================================

	def document_postprocessing(
			self,
			doc:         Dict[str, Any]             = None,
			word_chunks: Dict[str, List[WordChunk]] = None,
			embeddings:  Dict[str, np.ndarray]      = None,
	):
		print("Document Postprocessing...")

		if doc is None:
			doc = self.handler.doc
		if word_chunks is None:
			word_chunks = self.handler.word_chunks
		if embeddings is None:
			embeddings = self.handler.embeddings

		self.storage.upsert(
			doc,
			word_chunks,
			embeddings,
		)




	def request_postprocessing(
			self,
			word_chunks: List[WordChunk],
			embedding:   np.ndarray,
	) -> Dict[str, Any]:
		# print("Request Postprocessing...")



		#
		# res = app.storage.database.search(embedding, active_only=False)
		# print(res)
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
		count: int = self.handler.update_flags(
			target_id,
			include = include,
			process = process,
			merge   = merge,
			clear   = clear,
		)

		if report_file:
			__report_progress__(self.handler.doc, self.path_to_data, report_file)
		return count

	def clean(
			self,
			report_file: str = "",
	):
		self.handler.clean()

		if report_file:
			__report_progress__(self.handler.doc, self.path_to_data, report_file)
		return


	# ==========================================================================
	# Вспомогательные методы
	# ==========================================================================

	def _processing_section(
			self,
			cur: Dict[str, Any],
	) -> Tuple[
		Dict[str, List[WordChunk]],
		Dict[str, np.ndarray],
	]:
		word_chunks: Dict[str, List[WordChunk]] = {}
		embeddings:  Dict[str, np.ndarray]      = {}

		paragraphs = cur.get("paragraphs", [])
		if paragraphs:
			texts: List[str] = [p.get("text", "") for p in paragraphs]

			# title: str   = cur.get("title", "")
			# content: str = "\n".join(texts)
			# if title or content:
			# 	embeddings[cur.get("id") + "|" + "title"]   = self.encoder.process(title)
			# 	embeddings[cur.get("id") + "|" + "content"] = self.encoder.process(content)
			#
			# 	if self.include_markup:
			# 		cur["embedding"] = {
			# 			"title":   embeddings[cur.get("id") + "|" + "title"].tolist(),
			# 			"content": embeddings[cur.get("id") + "|" + "content"].tolist(),
			# 		}
			# elif self.include_markup:
			# 	cur["embedding"] = {
			# 		"title":   self.encoder.process("").tolist(),
			# 		"content": self.encoder.process("").tolist(),
			# 	}

			docs: List[Doc]        = list(self.spacy.pipe(texts))
			embs: List[np.ndarray] = list(self.encoder.pipe(texts))
			for it, doc, embedding in zip(
					paragraphs, docs, embs
			):
				chunks = WordChunkExtractor(doc, self.include_subchunks).extract()

				word_chunks[it.get("id")] = chunks
				embeddings[it.get("id")]  = embedding

				if self.include_markup:
					it["embedding"] = embedding.tolist()
					it["stack"]["chunks"] = [
						f"({chunk.start}:{chunk.end}) {chunk.text}"
						for chunk in chunks
					]

		sections = cur.get("sections", [])
		if sections:
			for it in sections:
				data = self._processing_section(it)
				word_chunks.update(data[0])
				embeddings.update(data[1])

		return (
			word_chunks,
			embeddings
		)
