from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import IntEnum

from backend.src.common.annotation.nlp.utils.text_chunk import TextChunk, TokenSnapshot


class LexType(IntEnum):
	NULL  = -1
	NONE  = 0

	# Базовые (лексические)
	NOUN  = 1
	VERB  = 2
	ADJ   = 3
	ADV   = 4
	NUM   = 5
	OTHER = 6


class ChunkType(IntEnum):
	NULL  = -1
	NONE  = 0

	# Структурные
	TYPE_1 = 1
	TYPE_2 = 2
	TYPE_3 = 3


@dataclass
class WordChunk:
	source:   TextChunk
	link:     Optional[WordChunk] = None
	parent:   Optional[WordChunk] = None
	children: List[WordChunk]     = field(default_factory=list)

	chunk_type: ChunkType = ChunkType.NULL
	lex_type:   LexType   = LexType.NULL
	level:      int       = -1

	def __post_init__(self) -> None:
		if not self.source:
			raise ValueError("WordChunk - source must not be empty")
		# if self.link is None and self.source.link != -1:
		# 	raise ValueError("WordChunk - link must not be empty (link is specified in source)")

		if self.parent is not None and self not in self.parent.children:
			self.parent.children.append(self)

	def __repr__(self) -> str:
		return (
			f"WordChunk("
			f"{self.source.text!r}, "
			f"norm={self.source.norm!r}, "
			f"start={self.start}, end={self.end}"
			f")"
		)

	@property
	def start(self) -> int:
		return self.source.start

	@property
	def end(self) -> int:
		return self.source.end

	@property
	def text(self) -> str:
		return self.source.text

	@property
	def norm(self) -> str:
		return self.source.norm

	@property
	def tokens(self) -> Tuple[TokenSnapshot, ...]:
		return self.source.tokens

	@property
	def is_root(self) -> bool:
		return self.link is None and self.parent is None


# 	def set_parent(self, parent: Optional[WordChunk]) -> None:
# 		if parent is not None and self.link is not None:
# 			raise ValueError("Нельзя одновременно задать parent и link.")
#
# 		if self.parent is parent:
# 			return
#
# 		if self.parent is not None and self in self.parent.children:
# 			self.parent.children.remove(self)
#
# 		self.parent = parent
#
# 		if parent is not None and self not in parent.children:
# 			parent.children.append(self)
#
# 	def can_merge_with(self, other: WordChunk) -> bool:
# 		if self.source.tokens and other.source.tokens:
# 			same_doc_order = True
# 		else:
# 			same_doc_order = False
#
# 		linked = (self.link is other) or (other.link is self)
# 		same_parent = self.parent is not None and self.parent is other.parent
# 		overlap_or_touch = not (self.end < other.start or other.end < self.start)
#
# 		return same_doc_order and (linked or same_parent or overlap_or_touch)
#
# 	def merge(self, other: WordChunk) -> WordChunk:
# 		"""
# 		Объединяет данные двух чанков.
# 		Если чанки не соседние, токены просто объединяются в один снимок.
# 		"""
# 		if not self.can_merge_with(other):
# 			raise ValueError("Эти WordChunk нельзя объединить.")
#
# 		source_tokens = tuple(
# 			{t.i: t for t in (*self.source.tokens, *other.source.tokens)}
# 			.values()
# 		)
# 		source_tokens = tuple(sorted(source_tokens, key=lambda t: t.i))
#
# 		norm_tokens = tuple(
# 			{t.i: t for t in (*self.normalized.tokens, *other.normalized.tokens)}
# 			.values()
# 		)
# 		norm_tokens = tuple(sorted(norm_tokens, key=lambda t: t.i))
#
# 		merged_internal_links: List[InternalLink] = []
# 		for chunk, offset in ((self, 0), (other, 0)):
# 			for link in chunk.internal_links:
# 				merged_internal_links.append(link.shift(offset))
#
# 		# Удаляем дубликаты
# 		uniq = []
# 		seen = set()
# 		for link in sorted(merged_internal_links, key=lambda x: (x.start, x.end, x.label)):
# 			key = (link.start, link.end, link.label)
# 			if key not in seen:
# 				seen.add(key)
# 				uniq.append(link)
#
# 		merged = WordChunk(
# 			source=TextChunk(source_tokens, mode="text"),
# 			normalized=TextChunk(norm_tokens, mode="lemma"),
# 			internal_links=tuple(uniq),
# 			c_type=min(self.c_type, other.c_type),
# 			c_level=min(self.c_level, other.c_level),
# 		)
#
# 		if self.parent is not None and self.parent is other.parent:
# 			merged.set_parent(self.parent)
#
# 		return merged
#
# 	def split(self, boundaries: Optional[Iterable[int]] = None) -> List["WordChunk"]:
# 		"""
# 		Разделяет чанк на отдельные WordChunk.
#
# 		boundaries — локальные позиции разреза внутри source.tokens.
# 		Если не переданы, берутся start/end внутренних ссылок.
# 		"""
# 		n = len(self.source.tokens)
# 		if n == 0:
# 			return []
#
# 		if boundaries is None:
# 			cuts = {l.start for l in self.internal_links if 0 < l.start < n}
# 			cuts |= {l.end for l in self.internal_links if 0 < l.end < n}
# 		else:
# 			cuts = {int(x) for x in boundaries if 0 < int(x) < n}
#
# 		cuts = sorted(cuts)
# 		if not cuts:
# 			return [self.clone()]
#
# 		result: List[WordChunk] = []
# 		lefts = [0] + cuts
# 		rights = cuts + [n]
#
# 		for left, right in zip(lefts, rights):
# 			if left >= right:
# 				continue
#
# 			source_part = self.source.slice(left, right)
# 			norm_part = self.normalized.slice(left, right)
#
# 			links: List[InternalLink] = []
# 			for link in self.internal_links:
# 				clipped = link.clip(left, right)
# 				if clipped is not None:
# 					links.append(clipped)
#
# 			part = WordChunk(
# 				source=source_part,
# 				normalized=norm_part,
# 				internal_links=tuple(links),
# 				c_type=self.c_type,
# 				c_level=self.c_level,
# 			)
#
# 			if self.parent is not None:
# 				part.set_parent(self.parent)
# 			elif self.link is not None:
# 				part.link = self.link
#
# 			result.append(part)
#
# 		return result
#
# 	def clone(self) -> WordChunk:
# 		return WordChunk(
# 			source=self.source,
# 			normalized=self.normalized,
# 			link=self.link,
# 			internal_links=self.internal_links,
# 			parent=None,
# 			c_type=self.c_type,
# 			c_level=self.c_level,
# 		)
#
# 	def add_internal_link(self, start: int, end: int, label: str = "internal") -> None:
# 		if not (0 <= start < end <= len(self.source.tokens)):
# 			raise ValueError("Неверные границы внутренней ссылки.")
# 		self.internal_links = tuple((*self.internal_links, InternalLink(start, end, label)))








