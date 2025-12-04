import os
import sqlite3

from sentence_transformers import SentenceTransformer

from utils.extract_text import extract_text

DB_PATH = os.path.join(os.path.dirname(__file__), "techdocs.db")

# ⭐ ここに対象ディレクトリを指定する
TARGET_DIRS = [
    "/Users/marimurotani/docs/typescript",
    "/Users/marimurotani/docs/python",
    "/Users/marimurotani/docs/cdk",
    "/Users/marimurotani/docs/vue",
]

# ⭐ カテゴリとして認識するフォルダ名
KNOWN_CATEGORIES = ["typescript", "python", "cdk", "vue"]


def detect_category(path: str) -> str:
    """
    ファイルパスからカテゴリを推定する（フォルダ名ベース）
    """
    parts = path.lower().split("/")
    for cat in KNOWN_CATEGORIES:
        if cat in parts:
            return cat
    return "unknown"


def create_db():
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    
    # Load sqlite-vec extension
    import sqlite_vec
    sqlite_vec.load(conn)
    
    conn.enable_load_extension(False)

    # documents テーブル（カテゴリを追加）
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            text TEXT,
            category TEXT
        );
    """
    )

    # ベクトル格納テーブル (vec0を使用)
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS doc_embeddings USING vec0(
            embedding FLOAT[384]
        );
    """
    )

    conn.commit()
    return conn


def walk_files(dirs):
    for base in dirs:
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith(".html") or f.endswith(".md"):
                    yield os.path.join(root, f)


def main():
    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    conn = create_db()
    count = 0

    for path in walk_files(TARGET_DIRS):
        print(f"Processing: {path}")

        text = extract_text(path)
        if not text.strip():
            continue

        category = detect_category(path)

        # Insert text + category
        cur = conn.execute(
            "INSERT OR IGNORE INTO documents (path, text, category) VALUES (?, ?, ?)",
            (path, text, category),
        )

        doc_id = cur.lastrowid
        # 既存データ（重複）はスキップ
        if doc_id is None:
            continue

        # Embedding 作成（長文は 2000 文字カット）
        emb = model.encode(text[:2000]).astype("float32")

        conn.execute(
            "INSERT INTO doc_embeddings (rowid, embedding) VALUES (?, ?)",
            (doc_id, emb.tobytes()),
        )

        count += 1

    conn.commit()
    conn.close()

    print("\n============================")
    print(f"Index build complete! ({count} docs)")
    print(f"DB file: {DB_PATH}")
    print("============================")


if __name__ == "__main__":
    main()
