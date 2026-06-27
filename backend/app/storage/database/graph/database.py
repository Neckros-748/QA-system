from __future__ import annotations

from typing import Dict, List, Any, Optional, Tuple, Union
import json
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

from backend.app.config import settings


class PostgresGraphStore:
    """
    PostgreSQL хранилище для графа знаний.
    Хранит:
        - документы (таблица documents)
        - узлы графа (таблица nodes) с типами TYPE_1, TYPE_2, TYPE_3
        - рёбра (таблица edges) с типами 'link', 'parent', 'contains'
        - связи узлов с документами и фрагментами (таблица node_document_fragment)
    """

    def __init__(self):
        self._connect()
        self._create_tables()

    # --------------------------------------------------------------------------
    # Подключение
    # --------------------------------------------------------------------------

    def _connect(self):
        self.conn = psycopg2.connect(
            dbname=settings.POSTGRES_DATABASE,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host="127.0.0.1",   # или из настроек
            port="5432"
        )
        self.conn.autocommit = True
        register_vector(self.conn)  # если используется

    def close(self):
        if self.conn:
            self.conn.close()

    # --------------------------------------------------------------------------
    # Создание таблиц
    # --------------------------------------------------------------------------

    def _create_tables(self):
        with self.conn.cursor() as cur:
            # Расширение для векторов (необязательно, но оставим)
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # Таблица документов
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id         BIGSERIAL PRIMARY KEY,
                    ext_id     TEXT      NOT NULL UNIQUE,
                    title      TEXT      NOT NULL,
                    status     TEXT      NOT NULL DEFAULT 'Ожидание',
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    metadata   JSONB     NOT NULL DEFAULT '{}'
                );
            """)

            # Таблица узлов графа
            cur.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id       BIGSERIAL PRIMARY KEY,
                    label    TEXT      NOT NULL,
                    norm     TEXT      NOT NULL UNIQUE,   -- нормализованное представление
                    type     INTEGER   NOT NULL,           -- 1,2,3
                    level    INTEGER   NOT NULL DEFAULT 0,
                    lex_type INTEGER   NOT NULL DEFAULT 0,
                    metadata JSONB     NOT NULL DEFAULT '{}'
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_nodes_norm ON nodes(norm);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);")

            # Таблица рёбер
            cur.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id              BIGSERIAL PRIMARY KEY,
                    source_node_id  BIGINT  NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                    target_node_id  BIGINT  NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                    relation        TEXT    NOT NULL,   -- 'link', 'parent', 'contains'
                    metadata        JSONB   NOT NULL DEFAULT '{}',
                    UNIQUE (source_node_id, target_node_id, relation)
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation);")

            # Таблица связи узлов с документами и фрагментами
            cur.execute("""
                CREATE TABLE IF NOT EXISTS node_document_fragment (
                    node_id     BIGINT  NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                    document_id BIGINT  NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    fragment    TEXT    NOT NULL,
                    PRIMARY KEY (node_id, document_id, fragment)
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ndf_node ON node_document_fragment(node_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ndf_document ON node_document_fragment(document_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ndf_fragment ON node_document_fragment(fragment);")

    # --------------------------------------------------------------------------
    # Вспомогательные методы разрешения ID
    # --------------------------------------------------------------------------

    def _resolve_document_id(self, ext_id: Union[int, str]) -> int:
        """Возвращает числовой ID документа по ext_id."""
        if isinstance(ext_id, int):
            return ext_id
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM documents WHERE ext_id = %s", (ext_id,))
            row = cur.fetchone()
        if not row:
            raise ValueError(f"Документ с ext_id '{ext_id}' не найден")
        return row[0]

    def _resolve_node_id(self, norm: str) -> int:
        """Возвращает ID узла по нормализованному имени."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM nodes WHERE norm = %s", (norm,))
            row = cur.fetchone()
        if not row:
            raise ValueError(f"Узел с нормой '{norm}' не найден")
        return row[0]

    # --------------------------------------------------------------------------
    # Работа с документами
    # --------------------------------------------------------------------------

    def upsert_document(self, doc: Dict[str, Any]) -> int:
        """
        Добавляет или обновляет документ.
        doc должен содержать ключи: id (ext_id), title, status, metadata (опционально).
        Возвращает числовой ID документа.
        """
        ext_id = doc.get("id")
        title = doc.get("title", "")
        status = doc.get("status", "Ожидание")
        metadata = doc.get("metadata", {})
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (ext_id, title, status, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (ext_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata
                RETURNING id
            """, (ext_id, title, status, json.dumps(metadata)))
            return cur.fetchone()[0]

    def remove_document(self, ext_id: Union[int, str]) -> None:
        """Удаляет документ и все связанные с ним записи (каскадно)."""
        doc_id = self._resolve_document_id(ext_id)
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))

    # --------------------------------------------------------------------------
    # Работа с узлами
    # --------------------------------------------------------------------------

    def add_node(
        self,
        label: str,
        norm: str,
        node_type: int,
        level: int = 0,
        lex_type: int = 0,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Добавляет узел графа. Если узел с таким norm уже существует, возвращает его ID.
        """
        metadata = metadata or {}
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nodes (label, norm, type, level, lex_type, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (norm)
                DO UPDATE SET
                    label = EXCLUDED.label,
                    type = EXCLUDED.type,
                    level = EXCLUDED.level,
                    lex_type = EXCLUDED.lex_type,
                    metadata = EXCLUDED.metadata
                RETURNING id
            """, (label, norm, node_type, level, lex_type, json.dumps(metadata)))
            return cur.fetchone()[0]

    def get_node(self, norm: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию об узле по норме."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, label, norm, type, level, lex_type, metadata
                FROM nodes WHERE norm = %s
            """, (norm,))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "label": row[1],
            "norm": row[2],
            "type": row[3],
            "level": row[4],
            "lex_type": row[5],
            "metadata": row[6],
        }

    # --------------------------------------------------------------------------
    # Работа с рёбрами
    # --------------------------------------------------------------------------

    def add_edge(
        self,
        source_norm: str,
        target_norm: str,
        relation: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Добавляет ребро между двумя узлами (по их норме).
        Если ребро уже существует, обновляет метаданные.
        """
        source_id = self._resolve_node_id(source_norm)
        target_id = self._resolve_node_id(target_norm)
        metadata = metadata or {}
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO edges (source_node_id, target_node_id, relation, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_node_id, target_node_id, relation)
                DO UPDATE SET metadata = EXCLUDED.metadata
                RETURNING id
            """, (source_id, target_id, relation, json.dumps(metadata)))
            return cur.fetchone()[0]

    def get_edges(self, node_norm: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Возвращает все рёбра, или рёбра, инцидентные заданному узлу.
        """
        with self.conn.cursor() as cur:
            if node_norm:
                node_id = self._resolve_node_id(node_norm)
                cur.execute("""
                    SELECT source_node_id, target_node_id, relation, metadata
                    FROM edges
                    WHERE source_node_id = %s OR target_node_id = %s
                """, (node_id, node_id))
            else:
                cur.execute("""
                    SELECT source_node_id, target_node_id, relation, metadata
                    FROM edges
                """)
            rows = cur.fetchall()
        return [
            {
                "source": row[0],
                "target": row[1],
                "relation": row[2],
                "metadata": row[3],
            }
            for row in rows
        ]

    # --------------------------------------------------------------------------
    # Связь узлов с документами и фрагментами
    # --------------------------------------------------------------------------

    def add_node_document_fragment(
        self,
        node_norm: str,
        document_ext_id: Union[int, str],
        fragment: str
    ) -> None:
        """
        Привязывает узел к конкретному фрагменту документа.
        """
        node_id = self._resolve_node_id(node_norm)
        doc_id = self._resolve_document_id(document_ext_id)
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO node_document_fragment (node_id, document_id, fragment)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (node_id, doc_id, fragment))

    def remove_node_document_fragment(
        self,
        node_norm: str,
        document_ext_id: Union[int, str],
        fragment: Optional[str] = None
    ) -> None:
        """
        Удаляет связь узла с документом/фрагментом.
        Если fragment не указан, удаляются все связи узла с этим документом.
        """
        node_id = self._resolve_node_id(node_norm)
        doc_id = self._resolve_document_id(document_ext_id)
        with self.conn.cursor() as cur:
            if fragment:
                cur.execute("""
                    DELETE FROM node_document_fragment
                    WHERE node_id = %s AND document_id = %s AND fragment = %s
                """, (node_id, doc_id, fragment))
            else:
                cur.execute("""
                    DELETE FROM node_document_fragment
                    WHERE node_id = %s AND document_id = %s
                """, (node_id, doc_id))

    # --------------------------------------------------------------------------
    # Загрузка всего графа в память (для построения in-memory индекса)
    # --------------------------------------------------------------------------

    def load_graph(self) -> Dict[str, Any]:
        """
        Загружает все узлы и рёбра из базы в структуру, пригодную для GraphIndex.
        Возвращает словарь с ключами 'nodes' и 'edges'.
        """
        # Загружаем все узлы
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, label, norm, type, level, lex_type, metadata
                FROM nodes
            """)
            nodes_rows = cur.fetchall()
            nodes = {}
            for row in nodes_rows:
                nodes[row[2]] = {   # ключ – norm
                    "id": row[0],
                    "label": row[1],
                    "norm": row[2],
                    "type": row[3],
                    "level": row[4],
                    "lex_type": row[5],
                    "metadata": row[6],
                }

        # Загружаем рёбра
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.source_node_id, e.target_node_id, e.relation, e.metadata,
                       n1.norm AS source_norm, n2.norm AS target_norm
                FROM edges e
                JOIN nodes n1 ON e.source_node_id = n1.id
                JOIN nodes n2 ON e.target_node_id = n2.id
            """)
            edges_rows = cur.fetchall()
            edges = []
            for row in edges_rows:
                edges.append({
                    "source": row[4],
                    "target": row[5],
                    "relation": row[2],
                    "metadata": row[3],
                })

        # Загружаем связи с документами (для каждого узла)
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT n.norm, d.ext_id, ndf.fragment
                FROM node_document_fragment ndf
                JOIN nodes n ON ndf.node_id = n.id
                JOIN documents d ON ndf.document_id = d.id
            """)
            doc_links = cur.fetchall()

        # Группируем по узлу (по norm)
        node_docs = {}
        for norm, doc_ext, frag in doc_links:
            node_docs.setdefault(norm, []).append({"doc_id": doc_ext, "fragment": frag})

        return {
            "nodes": nodes,
            "edges": edges,
            "node_docs": node_docs,
        }

    # --------------------------------------------------------------------------
    # Очистка
    # --------------------------------------------------------------------------

    def clear(self) -> None:
        """Удаляет все данные из таблиц (сброс всех сущностей)."""
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE node_document_fragment, edges, nodes, documents RESTART IDENTITY CASCADE;")

    # --------------------------------------------------------------------------
    # Массовые вставки (для производительности)
    # --------------------------------------------------------------------------

    def add_nodes_batch(self, nodes: List[Dict[str, Any]], batch_size: int = 1000) -> None:
        """
        Массовое добавление узлов.
        Каждый словарь должен содержать поля: label, norm, type, level, lex_type, metadata.
        """
        rows = []
        for node in nodes:
            rows.append((
                node["label"],
                node["norm"],
                node["type"],
                node.get("level", 0),
                node.get("lex_type", 0),
                json.dumps(node.get("metadata", {}))
            ))
        with self.conn.cursor() as cur:
            for i in range(0, len(rows), batch_size):
                chunk = rows[i:i+batch_size]
                execute_values(
                    cur,
                    """
                    INSERT INTO nodes (label, norm, type, level, lex_type, metadata)
                    VALUES %s
                    ON CONFLICT (norm) DO UPDATE SET
                        label = EXCLUDED.label,
                        type = EXCLUDED.type,
                        level = EXCLUDED.level,
                        lex_type = EXCLUDED.lex_type,
                        metadata = EXCLUDED.metadata
                    """,
                    chunk,
                    page_size=batch_size,
                )

    def add_edges_batch(self, edges: List[Dict[str, Any]], batch_size: int = 1000) -> None:
        """
        Массовое добавление рёбер.
        Каждый словарь должен содержать: source_norm, target_norm, relation, metadata.
        """
        rows = []
        for edge in edges:
            source_id = self._resolve_node_id(edge["source_norm"])
            target_id = self._resolve_node_id(edge["target_norm"])
            rows.append((
                source_id,
                target_id,
                edge["relation"],
                json.dumps(edge.get("metadata", {}))
            ))
        with self.conn.cursor() as cur:
            for i in range(0, len(rows), batch_size):
                chunk = rows[i:i+batch_size]
                execute_values(
                    cur,
                    """
                    INSERT INTO edges (source_node_id, target_node_id, relation, metadata)
                    VALUES %s
                    ON CONFLICT (source_node_id, target_node_id, relation) DO UPDATE SET
                        metadata = EXCLUDED.metadata
                    """,
                    chunk,
                    page_size=batch_size,
                )

    def add_node_document_fragments_batch(self, links: List[Dict[str, Any]], batch_size: int = 1000) -> None:
        """
        Массовое добавление связей узлов с документами и фрагментами.
        Каждый словарь: node_norm, document_ext_id, fragment.
        """
        rows = []
        for link in links:
            node_id = self._resolve_node_id(link["node_norm"])
            doc_id = self._resolve_document_id(link["document_ext_id"])
            rows.append((node_id, doc_id, link["fragment"]))
        with self.conn.cursor() as cur:
            for i in range(0, len(rows), batch_size):
                chunk = rows[i:i+batch_size]
                execute_values(
                    cur,
                    """
                    INSERT INTO node_document_fragment (node_id, document_id, fragment)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    chunk,
                    page_size=batch_size,
                )



# Создание экземпляра
store = PostgresGraphStore()

# Добавление документа
doc_id = store.upsert_document({
    "id": "my-doc-001",
    "title": "Техническое задание",
    "status": "Обработан"
})

# Добавление узлов
node1 = store.add_node("перелом", "перелом", node_type=1, level=0, lex_type=1)
node2 = store.add_node("шейка бедра", "шейка бедра", node_type=2, level=1, lex_type=1)

# Добавление ребра
store.add_edge("перелом", "шейка бедра", "parent")

# Привязка узла к фрагменту
store.add_node_document_fragment("перелом", "my-doc-001", "prg_1_[sct_h1:3]")

# Загрузка графа для построения индекса
graph_data = store.load_graph()

# Очистка
store.clear()
store.close()