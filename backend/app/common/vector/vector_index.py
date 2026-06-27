import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterable

import faiss
from faiss import IndexFlatIP
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import Config


class VecIndex:
	def __init__(
			self,
			config: Config
	):
		self.index:  IndexFlatIP = faiss.IndexFlatIP(config.embedding_dim)
		self.config: Config      = config

		cache_folder = Path(self.config.storage_path).parent / "models"
		self.model = SentenceTransformer(
			self.config.model_name["sentence_transformer"],
			cache_folder=str(cache_folder),
			# local_files_only=True,
		)

		self.doc_to_indices: Dict[str, List[int]] = {}
		self.metadata:       List[Dict[str, Any]] = []

	def process(
			self,
			text: str,
	) -> np.ndarray:
		if not text:
			return np.zeros(
				self.config.embedding_dim,
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
			batch_size           = self.config.batch_size,
			show_progress_bar    = False,
			convert_to_numpy     = True,
			normalize_embeddings = self.config.normalize_embeddings,
		)
		vectors = np.asarray(vectors, dtype=np.float32)
		if vectors.ndim == 1:
			vectors = vectors.reshape(1, -1)
		return vectors

	def add_texts(self, texts: List[Dict[str, Any]], text_field: str = "text") -> None:
		if not texts:
			return
		text_list = []
		metadata_list = []
		for item in texts:
			text = item.get(text_field)
			if not text:
				continue
			text_list.append(text)
			meta = {k: v for k, v in item.items() if k != text_field}
			metadata_list.append(meta)

		if not text_list:
			return

		vectors = self.pipe(text_list)
		if isinstance(vectors, list):
			vectors = np.array(vectors, dtype=np.float32)
		if vectors.ndim == 1:
			vectors = vectors.reshape(1, -1)

		self.add(vectors, metadata_list)

	def add(self, vectors: np.ndarray, metadatas: List[Dict[str, Any]]) -> None:
		if len(vectors) != len(metadatas):
			raise ValueError("Количество векторов и метаданных не совпадает")
		if vectors.shape[1] != self.config.embedding_dim:
			raise ValueError(f"Размерность вектора {vectors.shape[1]} != {self.config.embedding_dim}")

		if self.config.normalize_embeddings:
			faiss.normalize_L2(vectors)

		start_idx = self.index.ntotal
		self.index.add(vectors)
		self.metadata.extend(metadatas)

		for i, meta in enumerate(metadatas):
			doc_id = meta.get('doc_id')
			if doc_id:
				self.doc_to_indices.setdefault(doc_id, []).append(start_idx + i)

	def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
		if self.index.ntotal == 0:
			return []
		if query_vector.shape[0] != self.config.embedding_dim:
			raise ValueError(f"Размерность запроса {query_vector.shape[0]} != {self.config.embedding_dim}")

		q = query_vector.reshape(1, -1).astype(np.float32)
		if self.config.normalize_embeddings:
			faiss.normalize_L2(q)

		scores, indices = self.index.search(q, min(top_k, self.index.ntotal))
		results = []
		for idx, score in zip(indices[0], scores[0]):
			if idx >= 0:
				meta = self.metadata[idx].copy()
				meta['score'] = float(score)
				results.append(meta)
		return results

	def remove_document(self, doc_id: str) -> None:
		indices_to_remove = self.doc_to_indices.pop(doc_id, [])
		if not indices_to_remove:
			return

		if len(indices_to_remove) == self.index.ntotal:
			self.index.reset()
			self.metadata = []
			self.doc_to_indices.clear()
			return

		all_vectors = np.zeros((self.index.ntotal, self.config.embedding_dim), dtype=np.float32)
		self.index.reconstruct_n(0, self.index.ntotal, all_vectors)

		keep_mask = np.ones(self.index.ntotal, dtype=bool)
		keep_mask[indices_to_remove] = False
		kept_vectors = all_vectors[keep_mask]
		kept_metadata = [self.metadata[i] for i, keep in enumerate(keep_mask) if keep]

		self.index.reset()
		if self.config.normalize_embeddings:
			faiss.normalize_L2(kept_vectors)
		self.index.add(kept_vectors)
		self.metadata = kept_metadata

		new_doc_to_indices = {}
		for i, meta in enumerate(self.metadata):
			d_id = meta.get('doc_id')
			if d_id:
				new_doc_to_indices.setdefault(d_id, []).append(i)
		self.doc_to_indices = new_doc_to_indices

	def save(self, path: Optional[Path] = None) -> None:
		save_path = path or Path(self.config.storage_path).parent / "indices"
		if save_path is None:
			return
		os.makedirs(save_path, exist_ok=True)
		faiss.write_index(self.index, str(save_path / "vector.index"))
		with open(save_path / "metadata.pkl", "wb") as f:
			pickle.dump({
				'metadata': self.metadata,
				'doc_to_indices': self.doc_to_indices,
				'dim': self.config.embedding_dim,
				'normalize': self.config.normalize_embeddings,
			}, f)

	def load(self, path: Optional[Path] = None) -> None:
		load_path = path or Path(self.config.storage_path).parent / "indices"
		if load_path is None:
			return
		index_file = load_path / "vector.index"
		meta_file = load_path / "metadata.pkl"
		if not index_file.exists() or not meta_file.exists():
			return
		self.index = faiss.read_index(str(index_file))
		with open(meta_file, "rb") as f:
			data = pickle.load(f)
		self.metadata = data.get('metadata', [])
		self.doc_to_indices = data.get('doc_to_indices', {})
		self.config.embedding_dim = data.get('dim', self.config.embedding_dim)
		self.config.normalize_embeddings = data.get('normalize', self.config.normalize_embeddings)

	def clear(self) -> None:
		self.index.reset()
		self.metadata = []
		self.doc_to_indices.clear()

	def __len__(self) -> int:
		return self.index.ntotal