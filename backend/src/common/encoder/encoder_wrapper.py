from __future__ import annotations
import hashlib
import math
import os
import sqlite3
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.src.config import settings, EncoderConfig
# from backend.src.storage.sql.embedding_store import EmbeddingStore




class EncoderProcessor:
	def __init__(
			self, path_to_data: str, config: EncoderConfig
	) -> None:
		self.config: EncoderConfig = config

		self.model: SentenceTransformer = SentenceTransformer(
			self.config.model_name,
			cache_folder = path_to_data + "/prompts/models",
			local_files_only=True #, device="cpu"
		)
		self.dim: int = int(
			self.model.get_embedding_dimension()
		)

	def process(
			self,
			text: str,
	) -> np.ndarray:
		if not text:
			return np.zeros(
				int(self.model.get_embedding_dimension()),
				dtype=np.float32
			)

		vec = self.model.encode(
			text,
			convert_to_numpy     = True,
			normalize_embeddings = self.config.normalize_embeddings,
		)

		return vec.astype(np.float32)

	def pipe(
			self,
			texts: List[str],
	) -> Iterable[np.ndarray]:
		if not texts:
			return []

		vectors = self.model.encode(
			texts,
			batch_size           = self.config.encode_batch_size,
			show_progress_bar    = False,
			convert_to_numpy     = True,
			normalize_embeddings = self.config.normalize_embeddings,
		)

		vectors = np.asarray(vectors, dtype=np.float32)
		if vectors.ndim == 1:
			vectors = vectors.reshape(1, -1)

		# if vectors.shape[1] != self.dim:
		# 	raise ValueError(f"Неверная размерность эмбеддинга: {vectors.shape[1]} != {self.dim}")

		return vectors
