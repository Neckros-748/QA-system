import os
import pickle
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rank_bm25 import BM25Okapi


class BM25Index:
    """
    Индекс для лексического поиска на основе BM25.
    Хранит токенизированные тексты и метаданные, позволяет добавлять,
    искать, удалять и сохранять индекс на диск.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Инициализация BM25 индекса.
        :param storage_path: путь для сохранения/загрузки индекса (опционально)
        """
        self.storage_path = storage_path
        self.index: Optional[BM25Okapi] = None
        self.corpus: List[List[str]] = []               # список токенов для BM25
        self.doc_metadata: List[Dict[str, Any]] = []   # метаданные каждого фрагмента
        self.doc_ids: List[str] = []                    # идентификаторы фрагментов

    # ------------------------- Токенизация -------------------------

    def tokenize(self, text: str) -> List[str]:
        """
        Токенизация текста для BM25.
        Приводит к нижнему регистру, удаляет пунктуацию, разбивает на слова.
        """
        if not text:
            return []
        # Удаляем пунктуацию, оставляем буквы, цифры и пробелы
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [word for word in text.split() if word]

    # ------------------------- Добавление текстов -------------------------

    def add_texts(self, texts: List[Dict[str, Any]], text_field: str = "text"):
        """
        Добавляет произвольные текстовые фрагменты в индекс.
        Каждый словарь должен содержать поля:
            - id (уникальный идентификатор фрагмента)
            - text (текст для индексации)
            - doc_id (опционально, ID документа)
            - type (например, "section", "paragraph")
            - parent (опционально, родительский ID)
        """
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

    # ------------------------- Поиск -------------------------

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Выполняет поиск по BM25.
        :param query: поисковый запрос
        :param top_k: количество результатов
        :return: список словарей с id, metadata и score
        """
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

    # ------------------------- Удаление по ID документа -------------------------

    def remove_by_doc_id(self, doc_id: str):
        """
        Удаляет все фрагменты, принадлежащие указанному документу (по doc_id в метаданных).
        """
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

    # ------------------------- Сохранение / Загрузка -------------------------

    def save(self, path: Optional[Path] = None):
        """Сохраняет индекс на диск в формате pickle."""
        if self.index is None:
            return
        save_path = path or self.storage_path
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
        """Загружает индекс с диска."""
        load_path = path or self.storage_path
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

    # ------------------------- Очистка -------------------------

    def clear(self):
        """Полностью очищает индекс."""
        self.index = None
        self.corpus = []
        self.doc_metadata = []
        self.doc_ids = []

    # ------------------------- Информация -------------------------

    def size(self) -> int:
        """Возвращает количество индексированных фрагментов."""
        return len(self.doc_ids)

    def __len__(self):
        return self.size()