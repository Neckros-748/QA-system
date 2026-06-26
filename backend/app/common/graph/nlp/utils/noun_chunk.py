from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.common.graph.nlp.utils.text_chunk import TextChunk


@dataclass
class NounChunk:
	source:  TextChunk
	parent:  Optional[NounChunk] = None
	c_type:  int = -1    # 1 = noun_chunk; 2, 3 = subchunk; 4 = not subchunk
	c_level: int = -1    # глубина (0 — корневой chunk)

	# Type = 1 : noun_chunk     - основной чанк текста / термин
	# Type = 2 : subchunk       - подчанк основного чанка (Type = 1) текста
	# Type = 3 : subchunk       - подчанк нижнего уровня
	# Type = 4 : not subchunk   - подчанк основного чанка текста (Type = 2), но не входящий в основной чанк (Type = 1)

	def __repr__(self):
		if self.c_type == 1:
			return f"{self.source.text}"
		return f"T{self.c_type} : L{self.c_level} : {self.source.text}"
