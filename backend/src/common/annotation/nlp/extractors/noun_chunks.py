from functools import lru_cache
from typing import List, Set, Optional, Tuple
from spacy.tokens import Doc, Token

from backend.src.common.annotation.nlp.config import NOMINAL_POS, HARD_SPLIT_DEPS, NOUN_EXPAND_DEPS, NOUN_SUBTREE_DEPS
from backend.src.common.annotation.nlp.utils.base import is_valid_token, split_chunk_ids
from backend.src.common.annotation.nlp.utils.noun_chunk import NounChunk
from backend.src.common.annotation.nlp.utils.text_chunk import TextChunk, TokenSnapshot


class NounChunkExtractor:
	def __init__(
			self,
			doc: Doc,
	):
		self.doc = doc

	def extract(self) -> List[NounChunk]:
		roots = [
			t for t in self.doc
			if t.pos_ in NOMINAL_POS and not self._has_nominal_ancestor(t)
		]

		chunks: List[NounChunk] = []
		for root in roots:
			chunks.extend(self._collect_chunks(root.i, parent=None))

		chunks.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return chunks

	@staticmethod
	def _has_nominal_ancestor(
			token: Token,
	) -> bool:
		cur = token
		while cur.dep_ != "ROOT":
			if cur.dep_ in HARD_SPLIT_DEPS or cur.dep_ not in NOUN_EXPAND_DEPS:
				return False
			cur = cur.head
			if cur.pos_ in NOMINAL_POS:
				return True
		return False

	@lru_cache(maxsize=None)
	def _collect_chunk_ids(
			self,
			token_i: int,
	) -> List[int]:
		token = self.doc[token_i]
		ids: Set[int] = {token.i}
		stack = [token]

		while stack:
			t = stack.pop()
			for t_ch in t.children:
				if t_ch.dep_ in NOUN_EXPAND_DEPS and is_valid_token(t_ch):
					ids.add(t_ch.i)
					if t_ch.pos_ in NOMINAL_POS and t_ch.dep_ in NOUN_SUBTREE_DEPS:
						stack.append(t_ch)

		return sorted(ids)

	def _collect_chunks(
			self,
			token_i: int,
			parent:  Optional[NounChunk] = None,
	) -> List[NounChunk]:
		chunks: List[NounChunk] = []

		ids: Set[int] = set(self._collect_chunk_ids(token_i))
		components: List[Tuple[int, int]] = split_chunk_ids(ids)

		for start, end in components:
			tokens = self._make_snapshots(start, end)

			if not any(t.pos in NOMINAL_POS for t in tokens):
				continue

			if parent is not None:
				if start >= parent.source.start and end <= parent.source.end:
					chunk_level = parent.c_level + 1
					chunk_type  = 2
				else:
					continue
			else:
				chunk_level = 0
				chunk_type  = 1

			chunk = NounChunk(
				source  = TextChunk(tokens=tokens),
				parent  = parent,
				c_level = chunk_level,
				c_type  = chunk_type,
			)
			chunks.append(chunk)

			# if self.include_subchunks and chunk_level < 3:
			# 	root_token = self._find_root_token(start, end)
			#
			# 	for t_ch in root_token.children:
			# 		if t_ch.dep_ in HARD_SPLIT_DEPS or not is_valid_token(t_ch):
			# 			continue
			#
			# 		if t_ch.pos_ in NOMINAL_POS and t_ch.dep_ in NOUN_SUBTREE_DEPS:
			# 			chunks.extend(
			# 				self._collect_chunks(t_ch.i, parent=chunk)
			# 			)

		chunks.sort(key=lambda c: (c.source.start, -(c.source.end - c.source.start)))
		return chunks

	def _make_snapshots(
			self,
			start: int,
			end:   int,
	) -> Tuple[TokenSnapshot, ...]:
		return tuple(
			TokenSnapshot(
				i        = t.i,
				text     = t.text,
				lemma    = t.lemma_ or t.text,
				morph    = t.morph.to_dict(),
				head_i   = t.head.i,
				dep      = t.dep_ or "",
				pos      = t.pos_ or "",
				tag      = t.tag_ or "",
				is_stop  = bool(t.is_stop),
				is_punct = bool(t.is_punct),
				is_space = bool(t.is_space),
			)
			for t in self.doc[start:end]
		)

	def _find_root_token(
			self,
			start: int,
			end:   int,
	) -> Token:
		tokens = self.doc[start:end]
		for t in tokens:
			if t.head.i < start or t.head.i >= end:
				return t
		return tokens[0]
