"""
SQLite DocumentRepository 実装
"""
import sqlite3
import os
from typing import List, Optional
import numpy as np
from pathlib import Path
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.entities import Document
from domain.repositories import DocumentRepository


class SQLiteDocumentRepository(DocumentRepository):
    """SQLiteベースのドキュメント永続化"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_created()

    def _get_connection(self):
        """DB接続を取得"""
        conn = sqlite3.connect(self.db_path)
        # sqlite-vec を有効化
        try:
            conn.enable_load_extension(True)
            import sqlite_vec
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
        except Exception:
            pass
        return conn

    def _ensure_db_created(self):
        """DB及びテーブルが存在することを保証"""
        conn = self._get_connection()
        
        try:
            # pragma設定
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA page_size=32768;")
                conn.execute("PRAGMA mmap_size=134217728;")
            except sqlite3.OperationalError:
                pass

            # documentsテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE,
                    url TEXT,
                    text TEXT,
                    category TEXT
                );
                """
            )

            # マイグレーション: url列の追加
            try:
                cols = conn.execute("PRAGMA table_info(documents)").fetchall()
                col_names = {c[1] for c in cols}
                if "url" not in col_names:
                    conn.execute("ALTER TABLE documents ADD COLUMN url TEXT")
            except sqlite3.OperationalError:
                pass

            # doc_embeddingsテーブル
            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS doc_embeddings USING vec0(
                        embedding FLOAT[384]
                    );
                    """
                )
            except Exception:
                pass

            conn.commit()
        finally:
            conn.close()

    def save(self, document: Document) -> Document:
        """ドキュメントを保存（作成または更新）"""
        conn = self._get_connection()
        try:
            existing = conn.execute(
                "SELECT id FROM documents WHERE path = ?", (document.path,)
            ).fetchone()

            if existing:
                doc_id = existing[0]
                conn.execute(
                    """
                    UPDATE documents 
                    SET url = ?, text = ?, category = ? 
                    WHERE id = ?
                    """,
                    (document.url, document.text, document.category, doc_id),
                )
                document.id = doc_id
            else:
                cur = conn.execute(
                    """
                    INSERT INTO documents (path, url, text, category) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (document.path, document.url, document.text, document.category),
                )
                document.id = cur.lastrowid

            conn.commit()
            return document
        finally:
            conn.close()

    def find_by_path(self, path: str) -> Optional[Document]:
        """パスでドキュメントを検索"""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT id, path, url, text, category FROM documents WHERE path = ?",
                (path,),
            ).fetchone()
            if row:
                return Document(id=row[0], path=row[1], url=row[2], text=row[3], category=row[4])
            return None
        finally:
            conn.close()

    def find_by_id(self, doc_id: int) -> Optional[Document]:
        """IDでドキュメントを検索"""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT id, path, url, text, category FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()
            if row:
                return Document(id=row[0], path=row[1], url=row[2], text=row[3], category=row[4])
            return None
        finally:
            conn.close()

    def delete_by_id(self, doc_id: int) -> bool:
        """IDでドキュメントを削除"""
        conn = self._get_connection()
        try:
            # 埋め込みを先に削除
            conn.execute("DELETE FROM doc_embeddings WHERE rowid = ?", (doc_id,))
            # ドキュメントを削除
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def search_by_vector(
        self, 
        vector: np.ndarray, 
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[tuple[Document, float]]:
        """ベクトル類似度検索"""
        conn = self._get_connection()
        try:
            sql = """
                SELECT documents.id, documents.path, documents.url, 
                       documents.text, documents.category,
                       vec_distance_L2(doc_embeddings.embedding, ?) AS score
                FROM doc_embeddings
                JOIN documents ON doc_embeddings.rowid = documents.id
            """
            params = [vector.tobytes()]

            if category:
                sql += " WHERE documents.category = ?"
                params.append(category)

            sql += " ORDER BY score ASC LIMIT ?"
            params.append(top_k)

            rows = conn.execute(sql, params).fetchall()
            
            results = []
            for row in rows:
                doc = Document(id=row[0], path=row[1], url=row[2], text=row[3], category=row[4])
                results.append((doc, float(row[5])))
            
            return results
        finally:
            conn.close()

    def find_all_by_category(self, category: str) -> List[Document]:
        """カテゴリで全ドキュメントを検索"""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT id, path, url, text, category FROM documents WHERE category = ?",
                (category,),
            ).fetchall()
            return [
                Document(id=row[0], path=row[1], url=row[2], text=row[3], category=row[4])
                for row in rows
            ]
        finally:
            conn.close()

    def delete_by_domain(self, domain: str) -> int:
        """特定ドメインの全ドキュメントを削除"""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT id, path FROM documents").fetchall()
            to_delete = []
            
            for doc_id, path in rows:
                try:
                    if domain in path:
                        to_delete.append(doc_id)
                except Exception:
                    pass

            for doc_id in to_delete:
                conn.execute("DELETE FROM doc_embeddings WHERE rowid = ?", (doc_id,))
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

            conn.commit()
            return len(to_delete)
        finally:
            conn.close()

    def save_embedding(self, doc_id: int, embedding: np.ndarray) -> None:
        """ドキュメントの埋め込みベクトルを保存"""
        conn = self._get_connection()
        try:
            # 既存の埋め込みを削除
            conn.execute("DELETE FROM doc_embeddings WHERE rowid = ?", (doc_id,))
            # 新しい埋め込みを挿入
            conn.execute(
                "INSERT INTO doc_embeddings (rowid, embedding) VALUES (?, ?)",
                (doc_id, embedding.tobytes()),
            )
            conn.commit()
        finally:
            conn.close()
