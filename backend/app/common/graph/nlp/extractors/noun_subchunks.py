from typing import List

from app.common.graph.nlp.config import NOMINAL_POS, HARD_SPLIT_DEPS
from app.common.graph.nlp.utils.base import is_valid_token
from app.common.graph.nlp.utils.graph import is_connected, has_internal_head
from app.common.graph.nlp.utils.noun_chunk import NounChunk
from app.common.graph.nlp.utils.text_chunk import TextChunk


class NounSubchunkExtractor:
	def __init__(
			self,
			chunk:                 NounChunk,
			include_single_tokens: bool = True,
	):
		self.chunk = chunk
		self.include_single_tokens = include_single_tokens

	def extract(self) -> List[NounChunk]:
		subchunks: List[NounChunk] = []

		if len(self.chunk.source.tokens) == 1:
			return subchunks
		else:
			source: TextChunk = self.chunk.source
			n: int = len(source.tokens)

		for i in range(n):
			for j in range(i + 1, n + 1):
				text_chunk: TextChunk = TextChunk(tokens=source.tokens[i:j])

				# Фильтр 1: Должен содержать номинальный токен
				if not any(t.pos in NOMINAL_POS for t in text_chunk.tokens):
					continue

				# Фильтр 2: Проверка границ
				if text_chunk.tokens[0].dep in HARD_SPLIT_DEPS or not is_valid_token(text_chunk.tokens[0]):
					continue
				if text_chunk.tokens[-1].dep in HARD_SPLIT_DEPS or not is_valid_token(text_chunk.tokens[-1]):
					continue
				if text_chunk.start == source.start and text_chunk.end == source.end:
					continue

				# Фильтр 3: Проверка графовой связанности
				if not is_connected(text_chunk) or not has_internal_head(text_chunk):
					continue

				# Фильтр: Одиночные чанки
				if not self.include_single_tokens and len(text_chunk.tokens) == 1:
					continue

				if len(text_chunk.tokens) > 1:
					chunk = NounChunk(
						source  = text_chunk,
						parent  = self.chunk,
						c_level = self.chunk.c_level + 1,
						c_type  = 2,
					)
				else:
					chunk = NounChunk(
						source  = text_chunk,
						parent  = self.chunk,
						c_level = self.chunk.c_level + 1,
						c_type  = 3,
					)
				subchunks.append(chunk)

		return self._dedupe(subchunks)

	@staticmethod
	def _dedupe(
			chunks: List[NounChunk]
	) -> List[NounChunk]:
		seen = set()
		out = []

		for ch in chunks:
			key = (ch.source.start, ch.source.end)
			if key not in seen:
				seen.add(key)
				out.append(ch)

		out.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return out
