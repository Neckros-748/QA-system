from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Any

# from extractor.tokens import MorphAnalysis


@dataclass(frozen=False, slots=True)
class TokenSnapshot:
	i:        int
	text:     str
	lemma:    str
	morph:    Dict[str, Any]
	head_i:   int
	dep:      str  = ""
	pos:      str  = ""
	tag:      str  = ""
	is_stop:  bool = False
	is_punct: bool = False
	is_space: bool = False


@dataclass(frozen=False, slots=True)
class TextChunk:
	tokens: Tuple[TokenSnapshot, ...]
	link:   int = -1

	def __post_init__(self) -> None:
		if not self.tokens:
			raise ValueError("TextChunk - tokens must not be empty")

		if self.link == -1:
			index = [t.i for t in self.tokens]

			for token in self.tokens:
				if token.i == token.head_i:
					break
				elif token.head_i not in index:
					self.link = token.head_i
					break

	@property
	def start(self) -> int:
		return self.tokens[0].i if self.tokens else -1

	@property
	def end(self) -> int:
		return self.tokens[-1].i + 1 if self.tokens else -1

	@property
	def index(self) -> Tuple[int, ...]:
		return tuple(t.i for t in self.tokens)

	@property
	def text(self) -> str:
		return " ".join(t.text.lower().strip() for t in self.tokens if not t.is_space)

	@property
	def norm(self) -> str:
		return " ".join(t.lemma.lower().strip() for t in self.tokens if not t.is_space)

	@property
	def text_tokens(self) -> Tuple[str, ...]:
		return tuple(t.text.lower().strip() for t in self.tokens if not t.is_space)

	@property
	def norm_tokens(self) -> Tuple[str, ...]:
		return tuple(t.lemma.lower().strip() for t in self.tokens if not t.is_space)

	def concat(self, other: TextChunk) -> TextChunk:
		merged = {t.i: t for t in (*self.tokens, *other.tokens)}
		tokens = tuple(v for _, v in sorted(merged.items(), key=lambda x: x[0]))
		return TextChunk(tokens=tokens)

	def slice(self, left: int, right: int) -> TextChunk:
		return TextChunk(tokens=self.tokens[left:right])
