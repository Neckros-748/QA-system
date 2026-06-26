import os
from typing import Any, Dict, List, Tuple, Optional
import re

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn


class DocxParser:
	def __init__(
			self,
			doc_id:         str,
			doc_name:       str,
			doc_type:       str,
			doc_created_at: str,
			doc:            DocxDocument,
	):
		self.doc: DocxDocument = doc

		self.document: Dict[str, Any] = self._document_empty(
			doc_id, doc_name, doc_type, doc_created_at)
		self.stack: List[Tuple[Dict[str, Any], int]] = [
			(self.document, 0), (self._preface_section(), 0)
		]


	# ==========================================================================
	# Parsing
	# ==========================================================================

	def parse(self) -> Dict[str, Any]:
		for child in self.doc.element.body:
			tag = child.tag.split("}")[-1]

			match tag:
				case "p":
					paragraph = Paragraph(child, self.doc)
					self._parse_paragraph(paragraph)
				case "tbl":
					table = Table(child, self.doc)
					self._parse_table(table)
				case _:
					pass

		return self.document

	def _parse_paragraph(
			self,
			cur: Paragraph,
	) -> None:
		el = cur._element
		if self._is_table_signature(el):
			prev_el, next_el = self._get_siblings(el)
			if self._is_table_element(prev_el) or self._is_table_element(next_el):
				return
		text  = self._paragraph_text(cur)
		level = self._get_heading_level(cur)

		# PARAGRAPH
		if text:
			lines = []
			for run in cur.runs:
				run_text = run.text or ""
				if not run_text:
					continue
				lines.append({
					"text": run.text,
					"style": {
						"bold":      run.bold if run.bold else False,
						"italic":    run.italic if run.italic else False,
						"underline": run.underline if run.underline else False,
					},
				})

			style = {
				"list_level": self._get_list_level(cur),
				"alignment":  self._get_alignment(cur),
			}

			if level > 0:
				self._insert_section(
					self._make_section(text), level
				)
				self.stack.append((
					self._current_section()["sections"][-1], level
				))
			else:
				self._insert_paragraph(
					self._make_paragraph(text, lines, style)
				)

		# BREAK
		else:
			self._insert_break(
				self._make_break()
			)

	def _parse_table(
			self,
			cur: Table,
	) -> None:
		signature: str | None               = self._table_signature(cur)
		headers: List[List[Dict[str, Any]]] = []
		rows: List[List[Dict[str, Any]]]    = []

		for i, row in enumerate(cur.rows):
			row_data: List[Dict[str, Any]] = []
			for j, cell in enumerate(row.cells):
				text_parts: List[str] = []
				for p in cell.paragraphs:
					txt = self._paragraph_text(p)
					if txt:
						text_parts.append(txt)
				row_data.append({
					"row": i, "rowspan": 1,
					"col": j, "colspan": 1,
					"text": text_parts
				})
			if signature and i == 0:
				headers.append(row_data)
			else:
				rows.append(row_data)

		self._insert_table(
			self._make_table(signature, headers, rows)
		)


	# ==========================================================================
	# Creators
	# ==========================================================================
	
	@staticmethod
	def _document_empty(
			doc_id:         str,
			doc_name:       str,
			doc_type:       str,
			doc_created_at: str,
	) -> Dict[str, Any]:
		return {
			"id":         f"{doc_id}",
			"title":      f"{os.path.splitext(os.path.basename(doc_name))[0].strip()}",
			"type":       f"DOCUMENT: {doc_type}",
			"created_at": f"{doc_created_at}",
			"sections":   [],
		}

	def _preface_section(self) -> Dict[str, Any]:
		root = self.document
		if not root["sections"]:
			preface = self._make_section()
			preface["id"] = "sct_h0:1"
			root["sections"].insert(0, preface)
		return root["sections"][0]

	@staticmethod
	def _make_break() -> Dict[str, Any]:
		return {
			"id":       "",
			"type":     "BREAK",
			"_include": False,
			"_process": False,
		}

	def _insert_break(
			self,
			node: Dict[str, Any],
	) -> None:
		section = self._current_section()
		if not section["paragraphs"] or section["paragraphs"][-1]["type"] == "BREAK":
			return

		node["id"] = self._paragraph_id()
		section["stack"]["content_stack"].append(node["id"])
		section["paragraphs"].append(node)

	@staticmethod
	def _make_section(
			title: str | None = None,
	) -> Dict[str, Any]:
		return {
			"id":    "",
			"title": title or "",
			"type":  "SECTION",

			"paragraphs": [],
			"sections":   [],
			"stack": {
				"content_stack": [],
				"images":        [],
				"tables":        [],
			},
			"_include": True,
			"_process": False,
		}

	def _section_id(
			self,
			level: int,
	) -> str:
		section = self._current_section()
		section["stack"]["_counters"] = (
			section["stack"].get("_counters", {}))
		section["stack"]["_counters"][level] = (
			section["stack"]["_counters"].get(level, 0) + 1)

		parent_id = section.get("id", self.document["id"])
		index     = section["stack"]["_counters"][level]
		if parent_id.startswith("sct_") and not parent_id.startswith("sct_h0"):
			parent_path = parent_id.split(":")[1]
			path = f"{parent_path}_{index}"
		else:
			path = f"{index}"

		return f"sct_h{level}:{path}"

	def _insert_section(
			self,
			node:  Dict[str, Any],
			level: int,
	) -> None:
		while len(self.stack) > 1 and self._current_level() >= level:
			self.stack.pop()
		section = self._current_section()

		node["id"] = self._section_id(level)
		section["stack"]["content_stack"].append(node["id"])
		section["sections"].append(node)

	@staticmethod
	def _make_paragraph(
			text:  str | None,
			lines: List[Dict[str, Any]],
			style: Dict[str, Any],
	) -> Dict[str, Any]:
		node = {
			"id":    "",
			"type":  "PARAGRAPH",

			"text": text or "",
			"stack": {
				"lines": [],
			},
			"style": {
				"alignment":  style["alignment"],
				"list_level": style["list_level"],
			},
			"_include": True,
			"_process": False,
		}

		for line in lines:
			if node["stack"]["lines"]:
				line_last: Dict[str, Any] = node["stack"]["lines"][-1]
				if (
					line["style"]["bold"]      == line_last["style"]["bold"]   and
					line["style"]["italic"]    == line_last["style"]["italic"] and
					line["style"]["underline"] == line_last["style"]["underline"]
				):
					line_last["text"] = line_last["text"] + line["text"]
					continue
			node["stack"]["lines"].append(line)

		if len(node["stack"]["lines"]) == 1:
			line: Dict[str, Any] = node["stack"]["lines"][0]
			node["style"]["bold"]      = line["style"]["bold"]
			node["style"]["italic"]    = line["style"]["italic"]
			node["style"]["underline"] = line["style"]["underline"]
			node["stack"]["lines"]     = []

		return node

	def _paragraph_id(self) -> str:
		section = self._current_section()
		section["stack"]["_pcount"] = (
			section["stack"].get("_pcount", 0) + 1)

		return f"prg_{section['stack']['_pcount']}_[{section['id']}]"

	def _insert_paragraph(
			self,
			node: Dict[str, Any],
	) -> None:
		section = self._current_section()

		node["id"] = self._paragraph_id()
		section["stack"]["content_stack"].append(node["id"])
		section["paragraphs"].append(node)

	@staticmethod
	def _make_table(
			title:   str | None,
			headers: List[List[Dict[str, Any]]],
			rows:    List[List[Dict[str, Any]]],
	) -> Dict[str, Any]:
		return {
			"id":    "",
			"title": title or "",
			"type":  "TABLE",

			"content": {
				"headers": headers,
				"rows":    rows
			},
			"_include": False,
			"_process": False,
		}

	def _table_id(self) -> str:
		section = self._current_section()
		section["stack"]["_tcount"] = (
			section["stack"].get("_tcount", 0) + 1)

		return f"tbl_{section['stack']['_tcount']}_[{section['id']}]"

	def _insert_table(
			self,
			node: Dict[str, Any],
	) -> None:
		section = self._current_section()

		node["id"] = self._table_id()
		section["stack"]["content_stack"].append(node["id"])
		section["stack"]["tables"].append(node)


	# ==========================================================================
	# Helpers
	# ==========================================================================

	def _current_section(self) -> Dict[str, Any]:
		return self.stack[-1][0]

	def _current_level(self) -> int:
		return self.stack[-1][1]

	@staticmethod
	def _paragraph_text(
			cur: Paragraph,
	) -> str:
		if not cur.text:
			return ""
		else:
			text = cur.text
		text = re.sub(r"\s+", " ", text)
		text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
		return text.strip()

	@staticmethod
	def _is_paragraph_element(
			element,
	) -> bool:
		return element is not None and element.tag.split("}")[-1] == "p"

	@staticmethod
	def _is_table_element(
			element,
	) -> bool:
		return element is not None and element.tag.split("}")[-1] == "tbl"

	@staticmethod
	def _get_siblings(
			element,
	):
		parent = element.getparent()
		idx    = parent.index(element)
		prev_el = parent[idx - 1] if idx > 0 else None
		next_el = parent[idx + 1] if idx + 1 < len(parent) else None
		return prev_el, next_el

	@staticmethod
	def _get_heading_level(
			cur: Paragraph,
	) -> int:
		try:
			style_name = getattr(cur.style, "name", None)
			if style_name and style_name.lower().startswith("heading"):
				m = re.search(r"(\d+)", style_name)
				if m:
					return int(m.group(1))
		except Exception:
			pass

		try:
			outline_lvl = cur._element.xpath(".//w:outlineLvl")
			if outline_lvl:
				val = outline_lvl[0].get(qn("w:val"))
				if val is not None:
					return int(val) + 1
		except Exception:
			pass

		return 0

	@staticmethod
	def _get_list_level(
			cur: Paragraph,
	) -> int:
		try:
			num_pr = cur._element.xpath(".//w:numPr")
			if num_pr:
				ilvl = num_pr[0].xpath(".//w:ilvl")
				if ilvl:
					return int(ilvl[0].val) + 1
		except Exception:
			pass
		return 0

	@staticmethod
	def _get_alignment(
			cur: Paragraph,
	) -> str:
		align_map = {
			WD_ALIGN_PARAGRAPH.LEFT:    "left",
			WD_ALIGN_PARAGRAPH.CENTER:  "center",
			WD_ALIGN_PARAGRAPH.RIGHT:   "right",
			WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
		}
		return align_map.get(cur.alignment, "justify")

	def _table_signature(
			self,
			cur: Table,
	) -> Optional[str]:
		try:
			signatures = self._get_siblings(cur._element)
			for e in signatures:
				if self._is_table_signature(e):
					return self._get_table_signature(e)
		except Exception as e:
			print(f"""Ошибка при проверке подписи таблицы: {e}""")

	def _is_table_signature(
			self,
			element,
	) -> bool:
		try:
			tag = element.tag.split("}")[-1]
			if tag != "p":
				return False

			text = self._get_table_signature(element).lower().strip()
			if not text:
				return False

			# patterns = [
			# 	r"^(подпись|таблица|табл\.?)\s*\d+",
			# 	r"^(signature|table|tbl\.?)\s*\d+",
			# ]
			# if any(re.match(p, text) for p in patterns):
			# 	return True

			style_elem = element.xpath(".//w:pStyle")
			if style_elem:
				style_id = style_elem[0].get(qn("w:val"))

				if style_id:
					for style in self.doc.styles:
						if style.style_id == style_id:
							style_name = (style.name or "").lower()
							break
					else:
						style_name = ""

					if any(s in style_name for s in [
						"caption", "signature", "tablesignature"
					]):
						return True

		except:
			pass

		return False

	@staticmethod
	def _get_table_signature(
			element,
	) -> str:
		try:
			text = []
			elems = element.xpath(".//w:t")
			for e in elems:
				if e.text:
					text.append(e.text)
			return " ".join(text).strip()
		except:
			return ""
