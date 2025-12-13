import sqlite3
import os

import sqlite_vec
from sentence_transformers import SentenceTransformer

DB_PATH = os.path.join(os.path.dirname(__file__), "techdocs.db")


class TechDocsSearch:
    def __init__(self):
        print("Loading model...")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def search(self, query: str, category: str = None, top_k: int = 5):
        q_vec = self.model.encode(query).astype("float32")

        conn = sqlite3.connect(DB_PATH)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)

        sql = """
            SELECT documents.url, documents.category, documents.path,
                   vec_distance_L2(doc_embeddings.embedding, ?) AS score
            FROM doc_embeddings
            JOIN documents ON doc_embeddings.rowid = documents.id
        """

        params = [q_vec.tobytes()]

        if category:
            sql += " WHERE documents.category = ?"
            params.append(category)

        sql += " ORDER BY score ASC LIMIT ?"
        params.append(top_k)

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        return rows


if __name__ == "__main__":
    engine = TechDocsSearch()

    # 例：python カテゴリだけ検索
    result = engine.search(
        query="lambda function and decorators", category="python", top_k=5
    )

    import re

    def _path_to_url(path: str) -> str:
        m = re.search(r"/docs/[^/]+/([^/]+)/(.*)$", path)
        if not m:
            return path
        domain, rest = m.group(1), m.group(2)
        if rest.endswith(".html"):
            rest = rest[:-5]
        elif rest.endswith(".md"):
            rest = rest[:-3]
        return f"https://{domain}/{rest}"

    for url, cat, path, score in result:
        print(f"[{cat}] {score:.4f} {url or _path_to_url(path)}")
