from __future__ import annotations

from typing import Dict, List, Any, Iterable, Tuple, Optional

import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector
from psycopg2.extras import execute_values

from backend.src.config import settings


class PostgresStore:
	def __init__(
			self,
	):
		self._connect()
		self._create_tables()


	# -------------------------
	# Connection
	# -------------------------

	def _connect(self):
		self.conn = psycopg2.connect(
			dbname   = settings.POSTGRES_DATABASE,
			user     = settings.POSTGRES_USER,
			password = settings.POSTGRES_PASSWORD,
			host     = "127.0.0.1",
			port     = "5432"
		)

		self.conn.autocommit = True
		register_vector(self.conn)

	# IVF параметр
	# with self.conn.cursor() as cur:
	# 	cur.execute("SET ivfflat.probes = 10;")


	# -------------------------
	# Schema
	# -------------------------

	def _create_tables(self):
		with self.conn.cursor() as cur:
			cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS documents (
				    id         BIGSERIAL PRIMARY KEY,
				    ext_id     TEXT      NOT NULL UNIQUE,
				    title      TEXT      NOT NULL,
				    created_at TIMESTAMP NOT NULL DEFAULT NOW()
				);
				"""
			)

			cur.execute(
				"""
				CREATE TABLE IF NOT EXISTS embeddings (
					document_id BIGINT      NOT NULL,
					fragment    TEXT        NOT NULL,
				    embedding   vector(384) NOT NULL,
				    active      BOOLEAN     NOT NULL DEFAULT FALSE,
				    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),

				    PRIMARY KEY (document_id, fragment),
			
					CONSTRAINT fk_embeddings_document
					    FOREIGN KEY (document_id)
					    REFERENCES documents(id)
					    ON DELETE CASCADE
				);
				"""
			)

			cur.execute(
				"""
				CREATE INDEX IF NOT EXISTS idx_embeddings_active_vector
				ON embeddings
				USING ivfflat (embedding vector_cosine_ops)
				WITH (lists = 100)
				WHERE active = TRUE;
				"""
			)

			cur.execute(
				"""
				CREATE INDEX IF NOT EXISTS idx_embeddings_active
				ON embeddings(active);
				"""
			)


	# -------------------------
	# Utils
	# -------------------------

	def _analyze(self):
		with self.conn.cursor() as cur:
			cur.execute("ANALYZE embeddings;")

	def _resolve_document(
			self,
			document_id: int | str,
	) -> int:
		if isinstance(document_id, int):
			return document_id

		with self.conn.cursor() as cur:
			cur.execute(
				"""
				SELECT id
				FROM documents
				WHERE ext_id = %s
				""",
				(document_id,),
			)
			row = cur.fetchone()

		if not row:
			raise ValueError(f"Document not found: {document_id}")

		return row[0]


	# -------------------------
	# Control
	# -------------------------

	def set_active(
			self,
			document_id: Optional[int | str],
			fragments:   List[str],
			active:      bool,
			batch_size:  int = 1000,
	) -> int:
		if not fragments:
			return 0

		doc_id: Optional[int] = (
			self._resolve_document(document_id)
			if document_id else None
		)
		total_update: int = 0

		with self.conn.cursor() as cur:
			for i in range(0, len(fragments), batch_size):
				chunk = fragments[i:i + batch_size]

				if doc_id is not None:
					cur.execute(
						"""
						UPDATE embeddings
						SET active = %s
						WHERE document_id = %s AND fragment = ANY(%s)
						""",
						(active, doc_id, chunk),
					)
				else:
					cur.execute(
						"""
						UPDATE embeddings
						SET active = %s
						WHERE fragment = ANY(%s)
						""",
						(active, chunk),
					)

				total_update += cur.rowcount

		return total_update

	def clear_active(self):
		with self.conn.cursor() as cur:
			cur.execute(
				"""
				UPDATE embeddings
				SET active = FALSE
				"""
			)

	def clear(self):
		with self.conn.cursor() as cur:
			cur.execute("TRUNCATE TABLE embeddings, documents RESTART IDENTITY CASCADE;")


	# -------------------------
	# Upsert document (Insert / Update)
	# -------------------------

	def upsert(
			self,
			doc:         Dict[str, Any],
			embeddings:  Dict[str, np.ndarray],
	        active:      bool = True,
	        batch_size:  int  = 1000,
	) -> int:
		with self.conn.cursor() as cur:
			cur.execute(
				"""
				INSERT INTO documents (ext_id, title)
				VALUES (%s, %s)
				ON CONFLICT (ext_id)
				DO UPDATE SET
					title = EXCLUDED.title
				RETURNING id
				""",
				(doc.get("id"), doc.get("title")),
			)
			doc_id: int = cur.fetchone()[0]

		self.upsert_embeddings(
			doc_id, embeddings, active, batch_size
		)

		return doc_id

	def upsert_embeddings(
			self,
			doc_id:     int,
			embeddings: Dict[str, np.ndarray],
			active:     bool = True,
			batch_size: int  = 1000,
	):
		rows = [
			(doc_id, fragment, emb.tolist(), active)
			for fragment, emb in embeddings.items()
		]

		self._batch_upsert(rows, batch_size)
		self._analyze()

	def _batch_upsert(
			self,
			rows:       List[Tuple[Any, ...]],
			batch_size: int,
	):
		if not rows:
			return

		with self.conn.cursor() as cur:
			for i in range(0, len(rows), batch_size):
				chunk = rows[i:i + batch_size]

				execute_values(
					cur,
					"""
					INSERT INTO embeddings (document_id, fragment, embedding, active)
					VALUES %s
					ON CONFLICT (document_id, fragment)
					DO UPDATE SET
						embedding = EXCLUDED.embedding,
						active    = EXCLUDED.active
					""",
					chunk,
					page_size=batch_size,
				)


	# -------------------------
	# Delete document
	# -------------------------

	def delete(
			self,
			document_id: int | str,
	):
		doc_id: int = self._resolve_document(document_id)

		with self.conn.cursor() as cur:
			cur.execute(
				"""
				DELETE FROM documents
				WHERE id = %s
				""",
				(doc_id,),
			)


	# -------------------------
	# Search document
	# -------------------------

	def search(
			self,
			query_vec:   np.ndarray,
			active_only: bool = True,
			limit:       int  = 10,
	) -> List[Tuple[Any, ...]]:
		query_vec = query_vec.astype(np.float32).tolist()

		with self.conn.cursor() as cur:
			if active_only:
				cur.execute(
					"""
					SELECT
						d.ext_id,
						e.fragment,
						e.embedding,
						1 - (e.embedding <=> (%s::vector)) AS score
					FROM embeddings e
					JOIN documents d
						ON d.id = e.document_id
					WHERE e.active = TRUE
					ORDER BY e.embedding <=> (%s::vector)
					LIMIT %s
					""",
					(query_vec, query_vec, limit),
				)
			else:
				cur.execute(
					"""
					SELECT
						d.ext_id,
						e.fragment,
						e.embedding,
						1 - (e.embedding <=> (%s::vector)) AS score
					FROM embeddings e
					JOIN documents d
						ON d.id = e.document_id
					ORDER BY e.embedding <=> (%s::vector)
					LIMIT %s
					""",
					(query_vec, query_vec, limit),
				)

			rows = cur.fetchall()

		# return [
		# 	(
		# 		ext_id,
		# 		fragment,
		# 		np.array(embedding, dtype=np.float32),
		# 		float(score),
		# 	)
		# 	for ext_id, fragment, embedding, score in rows
		# ]

		return [
			(
				ext_id,
				fragment,
				float(score),
			)
			for ext_id, fragment, embedding, score in rows
		]

	def search_embeddings(
			self,
			active_only: bool = True,
	) -> List[Tuple[Any, ...]]:
		with self.conn.cursor() as cur:
			if active_only:
				cur.execute(
					"""
					SELECT
						d.ext_id,
						e.fragment,
						e.embedding
					FROM embeddings e
					JOIN documents d
						ON d.id = e.document_id
					WHERE e.active = TRUE
					""",
				)
			else:
				cur.execute(
					"""
					SELECT
						d.ext_id,
						e.fragment,
						e.embedding
					FROM embeddings e
					JOIN documents d
						ON d.id = e.document_id
					""",
				)

			rows = cur.fetchall()

		# return [
		# 	(
		# 		ext_id,
		# 		fragment,
		# 		np.array(embedding, dtype=np.float32),
		# 	)
		# 	for ext_id, fragment, embedding in rows
		# ]

		return [
			(
				ext_id,
				fragment,
			)
			for ext_id, fragment, embedding in rows
		]
