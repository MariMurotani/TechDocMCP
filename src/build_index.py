import os
import sqlite3
import sys

from sentence_transformers import SentenceTransformer

from config import LOCAL_DOCS_BASE, MAX_EMBED_TEXT_LEN, DOMAIN_BLOCKLIST
from policies.content_policy import ContentPolicy
from utils.extract_text import extract_text

DB_PATH = os.path.join(os.path.dirname(__file__), "techdocs.db")

# ⭐ ここに対象ディレクトリを指定する
TARGET_DIRS = [
    "/Users/marimurotani/docs/typescript",
    "/Users/marimurotani/docs/python",
    "/Users/marimurotani/docs/cdk",
    "/Users/marimurotani/docs/vue",
    "/Users/marimurotani/docs/aws_design",
]

# ⭐ カテゴリとして認識するフォルダ名
KNOWN_CATEGORIES = ["typescript", "python", "cdk", "vue", "aws_design"]


def detect_category(path: str) -> str:
    """
    ファイルパスからカテゴリを推定する（フォルダ名ベース）
    """
    parts = path.lower().split("/")
    for cat in KNOWN_CATEGORIES:
        if cat in parts:
            return cat
    return "unknown"


def path_to_url(path: str) -> str:
    """
    ローカルファイルパスを元のウェブURLに変換する
    例: /Users/marimurotani/docs/cdk/docs.aws.amazon.com/cdk/api/...
        → https://docs.aws.amazon.com/cdk/api/...
    """
    if not path.startswith(LOCAL_DOCS_BASE):
        return path
    
    # ベースパス以降を取得
    relative = path[len(LOCAL_DOCS_BASE):]
    
    # カテゴリディレクトリを除去（最初のディレクトリ）
    parts = relative.split("/", 1)
    if len(parts) < 2:
        return path
    
    # カテゴリを除いた残りの部分
    url_part = parts[1]
    
    # ドメイン部分を抽出（最初の部分）
    domain_parts = url_part.split("/", 1)
    if len(domain_parts) < 1:
        return path
    
    domain = domain_parts[0]
    rest = domain_parts[1] if len(domain_parts) > 1 else ""
    
    # .html や .md 拡張子を除去
    if rest.endswith(".html"):
        rest = rest[:-5]
    elif rest.endswith(".md"):
        rest = rest[:-3]
    
    # URLを構築
    url = f"https://{domain}/{rest}"
    return url


def backfill_urls(conn: sqlite3.Connection):
    """documents.url が NULL/空のレコードに対して URL を補完する。"""
    rows = conn.execute(
        "SELECT id, path FROM documents WHERE url IS NULL OR url = ''"
    ).fetchall()
    if not rows:
        return 0
    updated = 0
    for doc_id, path in rows:
        url = path_to_url(path)
        conn.execute("UPDATE documents SET url = ? WHERE id = ?", (url, doc_id))
        updated += 1
    conn.commit()
    return updated


def prune_disallowed_domains(conn: sqlite3.Connection):
    """
    既存のdocumentsから許可ドメイン外のレコードを削除し、対応する埋め込みも削除する。
    """
    rows = conn.execute("SELECT id, path FROM documents").fetchall()
    to_delete = []
    for doc_id, path in rows:
        try:
            if not is_allowed_domain(path):
                to_delete.append((doc_id,))
        except Exception:
            # パス解析に失敗したものは安全側で残す
            pass

    if not to_delete:
        return 0

    # doc_embeddings -> documents の順で削除
    for (doc_id,) in to_delete:
        conn.execute("DELETE FROM doc_embeddings WHERE rowid = ?", (doc_id,))
    for (doc_id,) in to_delete:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    return len(to_delete)


def prune_skip_files(conn: sqlite3.Connection):
    """
    既存のdocumentsからスキップすべきファイル（索引ページ等）を削除する。
    """
    rows = conn.execute("SELECT id, path FROM documents").fetchall()
    to_delete = []
    for doc_id, path in rows:
        try:
            # パスからファイル名を取得
            filename = path.split("/")[-1] if "/" in path else path
            if should_skip_file(filename, path):
                to_delete.append((doc_id,))
        except Exception:
            pass

    if not to_delete:
        return 0

    # doc_embeddings -> documents の順で削除
    for (doc_id,) in to_delete:
        conn.execute("DELETE FROM doc_embeddings WHERE rowid = ?", (doc_id,))
    for (doc_id,) in to_delete:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    return len(to_delete)


def create_db():
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    
    # Load sqlite-vec extension
    import sqlite_vec
    sqlite_vec.load(conn)
    
    conn.enable_load_extension(False)

    # documents テーブル（カテゴリとURLを追加）
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

    # 既存DBのマイグレーション: url列が無い場合は追加
    try:
        cols = conn.execute("PRAGMA table_info(documents)").fetchall()
        col_names = {c[1] for c in cols}
        if "url" not in col_names:
            conn.execute("ALTER TABLE documents ADD COLUMN url TEXT")
    except sqlite3.OperationalError:
        # PRAGMA / ALTER が失敗した場合でも続行（新規作成時など）
        pass

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


def should_skip_file(filename: str, path: str) -> bool:
    """
    スキップすべきファイルかどうかを判定する
    索引ページ、検索ページ、404ページなどは除外する
    """
    # スキップするファイル名のパターン
    skip_patterns = [
        "genindex",      # 索引ページ（genindex-A.html, genindex-M.html など）
        "modindex",      # モジュール索引
        "py-modindex",   # Pythonモジュール索引
        "search",        # 検索ページ
        "404",           # 404ページ
        "sitemap",       # サイトマップ
        "index-all",     # 全体索引
        "glossary",      # 用語集（場合による）
    ]
    
    filename_lower = filename.lower()
    for pattern in skip_patterns:
        if pattern in filename_lower:
            return True
    
    # パスベースのチェック（Python docs の /genindex-X URL用）
    path_lower = path.lower()
    if "/genindex-" in path_lower or "/genindex." in path_lower:
        return True
    if "/modindex" in path_lower or "/py-modindex" in path_lower:
        return True
    
    return False


def _extract_domain_from_path(path: str) -> str:
    """/docs/<category>/<domain>/... から domain を取り出す。合わなければ空文字。"""
    try:
        after_base = path.split(LOCAL_DOCS_BASE, 1)[1]
        # after_base: "<category>/<domain>/..."
        parts = after_base.split("/")
        if len(parts) >= 2:
            return parts[1]
    except Exception:
        pass
    return ""


def is_allowed_domain(path: str) -> bool:
    """ブロックリストのドメインに合致しないか判定。広告やトラッキングドメインを除外。"""
    domain = _extract_domain_from_path(path)
    if not domain:
        return True
    
    # ブロックリストに合致するドメインは除外
    for blocked in DOMAIN_BLOCKLIST:
        # 完全一致
        if domain == blocked:
            return False
        # サブドメイン一致 (e.g., cdn.example.com が example.com をブロック)
        if domain.endswith("." + blocked) or domain.endswith(blocked):
            return False
        # ワイルドカード一致 (e.g., *.googleapis.com)
        if blocked.startswith("*.") and domain.endswith(blocked[1:]):
            return False
    
    return True


policy = ContentPolicy()


def walk_files(dirs):
    for base in dirs:
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith((".html", ".md")):
                    full_path = os.path.join(root, f)
                    if should_skip_file(f, full_path):
                        continue
                    if not is_allowed_domain(full_path):
                        print("  ⊘ Skipped (domain filtered)")
                        continue
                    yield full_path


def main():
    print("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    conn = create_db()
    # 既存の不要ドメインをクリーンアップ
    try:
        pruned = prune_disallowed_domains(conn)
        if pruned:
            print(f"Pruned {pruned} documents from disallowed domains.")
    except Exception as e:
        print(f"Domain pruning skipped due to error: {e}")
    # 既存のスキップファイル（索引ページ等）をクリーンアップ
    try:
        pruned = prune_skip_files(conn)
        if pruned:
            print(f"Pruned {pruned} index/skip files.")
    except Exception as e:
        print(f"Skip file pruning skipped due to error: {e}")
    # 既存ドキュメントのURLを補完（スキップ判定に左右されない）
    try:
        filled = backfill_urls(conn)
        if filled:
            print(f"Backfilled URLs for {filled} existing documents.")
    except Exception as e:
        print(f"URL backfill skipped due to error: {e}")
    count = 0
    updated = 0

    for path in walk_files(TARGET_DIRS):
        print(f"Processing: {path}")

        text = extract_text(path)
        if not text.strip():
            continue
        
        # 意味のあるコンテンツかチェック（ドメイン別の調整込み）
        if not policy.is_meaningful_for(path, text):
            print(f"  ⊘ Skipped (not meaningful content)")
            continue

        category = detect_category(path)
        url = path_to_url(path)

        # Check if document already exists
        existing = conn.execute(
            "SELECT id FROM documents WHERE path = ?", (path,)
        ).fetchone()

        if existing:
            # Update existing document
            doc_id = existing[0]
            conn.execute(
                "UPDATE documents SET url = ?, text = ?, category = ? WHERE id = ?",
                (url, text, category, doc_id),
            )
            # Delete old embedding
            conn.execute("DELETE FROM doc_embeddings WHERE rowid = ?", (doc_id,))
            updated += 1
        else:
            # Insert new document
            cur = conn.execute(
                "INSERT INTO documents (path, url, text, category) VALUES (?, ?, ?, ?)",
                (path, url, text, category),
            )
            doc_id = cur.lastrowid
            count += 1

        # Create and insert embedding（長文は MAX_EMBED_TEXT_LEN でカット）
        emb = model.encode(text[:MAX_EMBED_TEXT_LEN]).astype("float32")
        conn.execute(
            "INSERT INTO doc_embeddings (rowid, embedding) VALUES (?, ?)",
            (doc_id, emb.tobytes()),
        )

    conn.commit()
    conn.close()

    print("\n============================")
    print(f"Index build complete!")
    print(f"  New documents: {count}")
    print(f"  Updated documents: {updated}")
    print(f"  Total: {count + updated}")
    print(f"DB file: {DB_PATH}")
    print("============================")


if __name__ == "__main__":
    main()
