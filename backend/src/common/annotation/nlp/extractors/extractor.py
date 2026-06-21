from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set, Tuple, Any

from spacy.tokens import Doc, Token

from backend.src.common.annotation.nlp.nlp_utils import NLPUtils
from backend.src.common.annotation.nlp.utils.noun_chunk import NounChunk
from backend.src.common.annotation.nlp.utils.text_chunk import TextChunk, TokenSnapshot
from backend.src.common.annotation.nlp.utils.word_chunk import WordChunk, LexType, ChunkType


class ChunkExtractor:

	def __init__(self, doc: Doc, include_subchunks: bool = False):
		self.doc  = doc
		self.include_subchunks = include_subchunks

	def extract(
			self
	) -> List[WordChunk]:
		nodes:       List[WordChunk]                  = []
		node_by_key: Dict[Tuple[int, ...], WordChunk] = {}

		# ======================================================================
		# 1) Обработка noun_chunk
		# ======================================================================

		noun_chunks: List[NounChunk] = self._extract_noun_chunks()
		covered:     Set[int]        = set()

		for chunk in sorted(
			noun_chunks, key=lambda c: (
						c.source.start,
						-(c.source.end - c.source.start)
				),
		):
			key = self._chunk_key(chunk.source)

			parent_node = None
			if chunk.parent is not None:
				pkey        = self._chunk_key(chunk.parent.source)
				parent_node = node_by_key.get(pkey)

			node: WordChunk = self._make_word_chunk(
				source     = chunk.source,
				parent     = parent_node,
				chunk_type = self._chunk_type_of(chunk),
				lex_type   = self._lex_type_of(chunk.source),
				level      = self._chunk_level_of(chunk),
			)

			nodes.append(node)
			covered.update(t.i for t in chunk.source.tokens)
			node_by_key[key] = node

		# ======================================================================
		# 2) Обработка внешних токенов
		# ======================================================================

		nodes.extend(
			self._fallback_tokens(
				covered
			))

		# ======================================================================
		# 3) Обработка связей
		# ======================================================================

		self._resolve_links(
			nodes
		)

		# ======================================================================
		# Вывод результата
		# ======================================================================

		nodes.sort(key=lambda c: (
			c.start,
			-(c.source.end - c.source.start)
		))
		return nodes

	def _extract_noun_chunks(
			self
	) -> List[NounChunk]:
		if not hasattr(NLPUtils, "extract_noun_chunks"):
			return []
		try:
			return NLPUtils.extract_noun_chunks(self.doc, self.include_subchunks) or []
		except TypeError:
			try:
				return NLPUtils.extract_noun_chunks(self.doc) or []
			except Exception:
				return []
		except Exception:
			return []

	def _fallback_tokens(
			self,
			covered: Set[int],
	) -> List[WordChunk]:
		nodes: List[WordChunk] = []

		for token in self.doc:

			# Пропуск стоп-слов и пунктуации
			if token.is_stop or token.is_punct or token.is_space:
				continue

			# Обработка токенов (Входящие в noun_chunk / noun_subchunk)
			if token.i in covered:
				continue

			source = TextChunk(
				tokens=tuple([self._snapshot(token)])
			)
			nodes.append(
				self._make_word_chunk(
					source     = source,
					parent     = None,
					chunk_type = ChunkType.NONE,
					lex_type   = self._lex_type_of(source),
					level      = -1,
				)
			)

		return nodes

	@staticmethod
	def _resolve_links(
			nodes: List[WordChunk],
	) -> None:
		token_to_nodes: DefaultDict[int, List[WordChunk]] = defaultdict(list)

		def _pick_target_node(
				token_i: int,
				exclude: WordChunk,
		) -> Optional[WordChunk]:
			candidates = [
				n
				for n in token_to_nodes.get(token_i, [])
				if n is not exclude
			]
			if not candidates:
				return None

			return min(
				candidates,
				key=lambda n: (n.end - n.start, n.level, n.start, n.end),
			)

		# ======================================================================
		# 1) Обработка внешних связей (link)
		# ======================================================================

		for node in nodes:
			if node.parent is not None:
				continue
			for token in node.tokens:
				token_to_nodes[token.i].append(node)

		for node in nodes:
			if node.parent is not None:
				continue

			link_i = node.source.link
			if link_i == -1:
				continue

			target = _pick_target_node(link_i, exclude=node)
			if target is not None:
				node.link = target

		# ======================================================================
		# 2) Обработка иерархических связей (parent / children)
		# ======================================================================

		pass

	@staticmethod
	def _make_word_chunk(
			source:     TextChunk,
			parent:     Optional[WordChunk],
			chunk_type: ChunkType = ChunkType.NULL,
			lex_type:   LexType   = LexType.NULL,
			level:      int       = -1,
	) -> WordChunk:
		wc = WordChunk(
			source     = source,
			link       = None,
			parent     = parent,
			children   = [],
			chunk_type = chunk_type,
			lex_type   = lex_type,
			level      = level,
		)
		return wc

	@staticmethod
	def _snapshot(
			token: Token
	) -> TokenSnapshot:
		return TokenSnapshot(
			i        = token.i,
			text     = token.text,
			lemma    = token.lemma_ or token.text,
			morph    = token.morph.to_dict(),
			head_i   = token.head.i,
			dep      = token.dep_ or "",
			pos      = token.pos_ or "",
			tag      = token.tag_ or "",
			is_stop  = bool(token.is_stop),
			is_punct = bool(token.is_punct),
			is_space = bool(token.is_space),
		)

	@staticmethod
	def _chunk_key(
			source: TextChunk | Tuple[TokenSnapshot, ...]
	) -> Tuple[int, ...]:
		tokens = source.tokens if isinstance(source, TextChunk) else source
		return tuple(t.i for t in tokens)

	@staticmethod
	def _chunk_type_of(
			it: NounChunk | Any
	) -> ChunkType:
		def resolve_from_token(chunk: NounChunk) -> ChunkType:
			if chunk.c_type == 1:
				return ChunkType.TYPE_1
			elif chunk.c_type == 2:
				return ChunkType.TYPE_2
			elif chunk.c_type == 3:
				return ChunkType.TYPE_3
			else:
				return ChunkType.NONE

		# --- NounChunk ---
		if isinstance(it, NounChunk):
			return resolve_from_token(it)

		else:
			return ChunkType.NONE

	@staticmethod
	def _chunk_level_of(
			it: NounChunk | Any
	) -> int:
		def resolve_from_token(chunk: NounChunk) -> int:
			return chunk.c_level

		# --- NounChunk ---
		if isinstance(it, NounChunk):
			return resolve_from_token(it)

		else:
			return -1

	@staticmethod
	def _lex_type_of(
			it: TextChunk | Tuple[TokenSnapshot, ...] | TokenSnapshot | Any
	) -> LexType:
		def resolve_from_token(t: TokenSnapshot) -> LexType:
			if t.pos in {"NOUN", "PROPN", "PRON"}:  # существительное, имя собственное, местоимение
				return LexType.NOUN
			elif t.pos in {"VERB", "AUX"}:          # глагол, вспомогательный глагол
				return LexType.VERB
			elif t.pos in {"ADJ"}:                  # прилагательное
				return LexType.ADJ
			elif t.pos in {"ADV"}:                  # наречие
				return LexType.ADV
			elif t.pos in {"NUM"}:                  # числительное
				return LexType.NUM
			return LexType.OTHER

		# --- TokenSnapshot ---
		if isinstance(it, TokenSnapshot):
			return resolve_from_token(it)

		# --- TextChunk ---
		elif isinstance(it, TextChunk):
			if len(it.tokens) == 1:
				return resolve_from_token(it.tokens[0])
			else:
				return LexType.NONE

		# --- Tuple[TokenSnapshot] ---
		elif isinstance(it, tuple):
			if len(it) == 1:
				return resolve_from_token(it[0])
			else:
				return LexType.NONE

		else:
			raise TypeError(f"Unsupported type: {type(it)}")
