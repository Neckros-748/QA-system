import os
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rank_bm25 import BM25Okapi

from app.config import Config


class LexIndex:
    def __init__(
            self,
            config: Config,
    ):
        self.index:  Optional[BM25Okapi] = None
        self.config: Config              = config

        self.corpus:       List[List[str]] = []
        self.doc_metadata: List[Dict[str, Any]] = []
        self.doc_ids:      List[str] = []

    def add_texts(self, texts: List[Dict[str, Any]], text_field: str = "text"):
        if not texts:
            return

        documents = []
        for item in texts:
            text = item.get(text_field, "")
            if not text:
                continue
            tokens = self.tokenize(text)
            if not tokens:
                continue
            documents.append({
                "id": item.get("id"),
                "text": text,
                "tokens": tokens,
                "metadata": {k: v for k, v in item.items() if k not in [text_field, "id"]}
            })

        if not documents:
            return

        new_texts = [d["tokens"] for d in documents]
        new_metas = [d["metadata"] for d in documents]
        new_ids = [d["id"] for d in documents]

        if self.index is not None:
            # Объединяем с существующим корпусом
            all_texts = self.corpus + new_texts
            self.index = BM25Okapi(all_texts)
            self.corpus = all_texts
            self.doc_metadata.extend(new_metas)
            self.doc_ids.extend(new_ids)
        else:
            self.index = BM25Okapi(new_texts)
            self.corpus = new_texts
            self.doc_metadata = new_metas
            self.doc_ids = new_ids

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if self.index is None or not self.corpus:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self.index.get_scores(query_tokens)
        # Получаем индексы топ-k документов
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0:
                results.append({
                    "id": self.doc_ids[idx],
                    "metadata": self.doc_metadata[idx],
                    "score": score,
                })
        return results

    def remove_by_doc_id(self, doc_id: str):
        if self.index is None:
            return

        to_remove = []
        for i, meta in enumerate(self.doc_metadata):
            if meta.get("doc_id") == doc_id:
                to_remove.append(i)

        if not to_remove:
            return

        # Удаляем в обратном порядке, чтобы не сбивать индексы
        for idx in sorted(to_remove, reverse=True):
            del self.corpus[idx]
            del self.doc_metadata[idx]
            del self.doc_ids[idx]

        # Перестраиваем индекс, если остались документы
        if self.corpus:
            self.index = BM25Okapi(self.corpus)
        else:
            self.index = None

    def save(self, path: Optional[Path] = None):
        if self.index is None:
            return
        save_path = path or Path(self.config.storage_path).parent / "indices"
        if save_path is None:
            return

        os.makedirs(save_path, exist_ok=True)
        with open(save_path / "bm25_index.pkl", "wb") as f:
            pickle.dump({
                "corpus": self.corpus,
                "doc_metadata": self.doc_metadata,
                "doc_ids": self.doc_ids,
            }, f)

    def load(self, path: Optional[Path] = None):
        load_path = path or Path(self.config.storage_path).parent / "indices"
        if load_path is None:
            return
        pkl_file = load_path / "bm25_index.pkl"
        if not pkl_file.exists():
            return

        with open(pkl_file, "rb") as f:
            data = pickle.load(f)

        self.corpus = data.get("corpus", [])
        self.doc_metadata = data.get("doc_metadata", [])
        self.doc_ids = data.get("doc_ids", [])

        if self.corpus:
            self.index = BM25Okapi(self.corpus)
        else:
            self.index = None

    def clear(self):
        self.index = None
        self.corpus = []
        self.doc_metadata = []
        self.doc_ids = []

    def tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        # Удаляем пунктуацию, оставляем буквы, цифры и пробелы
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [word for word in text.split() if word]

    def size(self) -> int:
        return len(self.doc_ids)

    def __len__(self):
        return self.size()
