import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Iterable
import os

import numpy as np
from docx import Document
from docx.document import Document as DocxDocument

from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.docs.file.file_utils import FileIO
from app.docs.parser.docx_parser import DocxParser


class DocumentHandler:
	def __init__(self):
		self.file_path:   str                        = ""
		self.doc:         Dict[str, Any]             = {}
		self.word_chunks: Dict[str, List[WordChunk]] = {}
		# self.embeddings:  Dict[str, np.ndarray]      = {}

	def clear(self):
		self.file_path   = ""
		self.doc         = {}
		self.word_chunks = {}
		# self.embeddings  = {}


	# ==========================================================================
	# Основные методы
	# ==========================================================================

	def parse(
			self,
			data: str | dict[str, Any]
	) -> Dict[str, Any]:
		if isinstance(data, str):
			self.file_path = data

			match os.path.splitext(os.path.basename(self.file_path))[1].strip():
				case ".docx":
					document: DocxDocument = Document(self.file_path)
					self.doc = DocxParser(
						uuid.uuid4(), self.file_path, self.file_type(self.file_path), self.now_str(), document
					).parse()
				case ".json":
					self.doc = FileIO.read(self.file_path)
				case _:
					self.doc = {}
		else:
			self.doc = DocxParser(
				data["id"], data["name"], data["type"], data["created_at"],data["document"]
			).parse()

		return self.doc


	# ==========================================================================
	# Вспомогательные методы
	# ==========================================================================

	@staticmethod
	def file_type(filename: str) -> str:
		if "." not in filename:
			return "FILE"
		return filename.rsplit(".", 1)[-1].upper()

	@staticmethod
	def format_size(size_bytes: int) -> str:
		if size_bytes < 1024:
			return f"{size_bytes} B"
		if size_bytes < 1024 * 1024:
			return f"{round(size_bytes / 1024)} KB"
		return f"{size_bytes / (1024 * 1024):.1f} MB"

	@staticmethod
	def now_str() -> str:
		return datetime.now().strftime("%Y-%m-%d %H:%M")

	def update_flags(
			self,
			target_id: Union[str, Iterable[str]],
			include:   Optional[bool] = None,
			process:   Optional[bool] = None,
			merge:     bool = False,
			clear:     bool = False
	) -> int:
		if isinstance(target_id, str):
			target_ids = {target_id}
		else:
			target_ids = set(target_id)

		updated_count = 0

		# ----------------------------------------------------------------------
		# Вспомогательные методы
		# ----------------------------------------------------------------------

		def _apply_to_paragraph(p: Dict[str, Any]):
			if p.get("type") != "PARAGRAPH":
				return

			# --- MERGE ---
			if merge:
				lines = p.get("stack", {}).get("lines", [])

				if not lines:
					return

				bold_all      = all(l["style"].get("bold", False) for l in lines)
				italic_all    = all(l["style"].get("italic", False) for l in lines)
				underline_all = all(l["style"].get("underline", False) for l in lines)

				p["style"]["bold"]      = bold_all
				p["style"]["italic"]    = italic_all
				p["style"]["underline"] = underline_all
				p["stack"]["lines"]     = []

			# --- CLEAR ---
			if clear:
				p["style"]["bold"]      = False
				p["style"]["italic"]    = False
				p["style"]["underline"] = False
				p["stack"]["lines"]     = []

		def _apply_recursive(node: Dict[str, Any]):
			for p in node.get("paragraphs", []):
				_apply_to_paragraph(p)

			for s in node.get("sections", []):
				_apply_recursive(s)

		# ----------------------------------------------------------------------
		# Основной метод
		# ----------------------------------------------------------------------

		def _update(node: Dict[str, Any]):
			nonlocal updated_count

			node_id = node.get("id")
			if node_id in target_ids:
				updated_count += 1

				if include is not None:
					node["_include"] = include
				if process is not None:
					node["_process"] = process

				# Merge / Clear
				if merge or clear:
					node_type = node.get("type")

					if node_type == "SECTION":
						_apply_recursive(node)
					elif node_type == "PARAGRAPH":
						_apply_to_paragraph(node)

			# Paragraph
			for p in node.get("paragraphs", []):
				_update(p)

			# Table
			for t in node.get("stack", {}).get("tables", []):
				_update(t)

			# Section
			for s in node.get("sections", []):
				_update(s)

		_update(self.doc)
		return updated_count

	def clear(self) -> None:

		def _clean_node(node: Dict[str, Any]) -> None:

			# Paragraph
			if "paragraphs" in node:
				node["paragraphs"] = [
					p for p in node["paragraphs"]
					if p.get("_include", True)
				]

			# Table
			if "stack" in node and "tables" in node["stack"]:
				node["stack"]["tables"] = [
					t for t in node["stack"]["tables"]
					if t.get("_include", True)
				]

			# Section
			if "sections" in node:
				node["sections"] = [
					s for s in node["sections"]
					if s.get("_include", True)
				]

				for s in node["sections"]:
					_clean_node(s)

			# --- content_stack ---
			if "stack" in node and "content_stack" in node["stack"]:
				valid_ids = set()

				for p in node.get("paragraphs", []):
					valid_ids.add(p["id"])
				for s in node.get("sections", []):
					valid_ids.add(s["id"])
				for t in node.get("stack", {}).get("tables", []):
					valid_ids.add(t["id"])

				node["stack"]["content_stack"] = [
					cid for cid in node["stack"]["content_stack"]
					if cid in valid_ids
				]

		_clean_node(self.doc)
