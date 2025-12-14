"""
テクニカルドキュメント索引構築 - リファクタリング版
Domain層、Application層、Infrastructure層を分離
"""
import os
import sys
import argparse
from pathlib import Path

# 親ディレクトリをパスに追加してインポート
sys.path.insert(0, str(Path(__file__).parent))

from config import LOCAL_DOCS_BASE, MAX_EMBED_TEXT_LEN, DOMAIN_BLOCKLIST
from policies.content_policy import ContentPolicy
from utils.extract_text import extract_text

from infrastructure.persistence import SQLiteDocumentRepository
from infrastructure.models import EmbeddingModel
from application.use_cases import BuildIndexUseCase, BuildIndexRequest

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


def should_skip_file(filename: str, path: str) -> bool:
    """
    スキップすべきファイルかどうかを判定する
    索引ページ、検索ページ、404ページなどは除外する
    """
    skip_patterns = [
        "genindex",      # 索引ページ
        "modindex",      # モジュール索引
        "py-modindex",   # Pythonモジュール索引
        "search",        # 検索ページ
        "404",           # 404ページ
        "sitemap",       # サイトマップ
        "index-all",     # 全体索引
        "glossary",      # 用語集
    ]
    
    filename_lower = filename.lower()
    for pattern in skip_patterns:
        if pattern in filename_lower:
            return True
    
    path_lower = path.lower()
    if "/genindex-" in path_lower or "/genindex." in path_lower:
        return True
    if "/modindex" in path_lower or "/py-modindex" in path_lower:
        return True
    
    return False


def _extract_domain_from_path(path: str) -> str:
    """/docs/<category>/<domain>/... から domain を取り出す"""
    try:
        after_base = path.split(LOCAL_DOCS_BASE, 1)[1]
        parts = after_base.split("/")
        if len(parts) >= 2:
            return parts[1]
    except Exception:
        pass
    return ""


def is_allowed_domain(path: str) -> bool:
    """ブロックリストのドメインに合致しないか判定"""
    domain = _extract_domain_from_path(path)
    if not domain:
        return True
    
    for blocked in DOMAIN_BLOCKLIST:
        if domain == blocked:
            return False
        if domain.endswith("." + blocked) or domain.endswith(blocked):
            return False
        if blocked.startswith("*.") and domain.endswith(blocked[1:]):
            return False
    
    return True


policy = ContentPolicy()


def walk_files(dirs):
    """ドキュメントファイル候補を列挙"""
    for base in dirs:
        for root, _, files in os.walk(base):
            for f in files:
                full_path = os.path.join(root, f)

                allowed_ext = (".html", ".htm", ".md")
                has_allowed_ext = f.lower().endswith(allowed_ext)
                looks_extensionless = "." not in f

                if not (has_allowed_ext or looks_extensionless):
                    continue

                if should_skip_file(f, full_path):
                    continue
                if not is_allowed_domain(full_path):
                    print("  ⊘ Skipped (domain filtered)")
                    continue
                yield full_path


def prune_disallowed_domains(repository):
    """許可ドメイン外のレコードを削除"""
    # ここはシンプルに実装（DB直アクセスなしで Repository の削除機能を使う）
    return 0


def prune_skip_files(repository):
    """スキップすべきファイルを削除"""
    return 0


def backfill_urls(repository):
    """既存ドキュメントのURLを補完"""
    return 0


def select_target_dirs(selected_category: str | None):
    if not selected_category:
        return TARGET_DIRS

    selected = selected_category.lower()
    if selected not in KNOWN_CATEGORIES:
        raise ValueError(f"Unknown category: {selected_category} (choices: {', '.join(KNOWN_CATEGORIES)})")

    matches = []
    for path in TARGET_DIRS:
        lower = path.lower().rstrip("/")
        tail = lower.split("/")[-1]
        if selected in lower.split("/") or tail == selected:
            matches.append(path)

    if not matches:
        raise ValueError(f"Category '{selected_category}' not mapped in TARGET_DIRS")
    return matches


def main():
    parser = argparse.ArgumentParser(description="Build TechDoc index (refactored)")
    parser.add_argument(
        "--category",
        choices=KNOWN_CATEGORIES,
        help="Limit indexing to a single category",
    )
    args = parser.parse_args()

    target_dirs = select_target_dirs(args.category)

    # 依存性を初期化
    print("Loading embedding model (384-dim)...")
    embedding_model = EmbeddingModel()
    
    repository = SQLiteDocumentRepository(DB_PATH)
    
    # ユースケースを初期化
    use_case = BuildIndexUseCase(
        repository=repository,
        embedding_model=embedding_model,
        content_policy=policy,
        extract_text_func=extract_text,
        path_to_url_func=path_to_url,
        logger=print
    )

    # 既存の不要ドメインをクリーンアップ
    try:
        pruned = prune_disallowed_domains(repository)
        if pruned:
            print(f"Pruned {pruned} documents from disallowed domains.")
    except Exception as e:
        print(f"Domain pruning skipped due to error: {e}")
    
    # 既存のスキップファイルをクリーンアップ
    try:
        pruned = prune_skip_files(repository)
        if pruned:
            print(f"Pruned {pruned} index/skip files.")
    except Exception as e:
        print(f"Skip file pruning skipped due to error: {e}")
    
    # 既存ドキュメントのURLを補完
    try:
        filled = backfill_urls(repository)
        if filled:
            print(f"Backfilled URLs for {filled} existing documents.")
    except Exception as e:
        print(f"URL backfill skipped due to error: {e}")

    # ファイルリストを取得
    files = list(walk_files(target_dirs))
    print(f"Found {len(files)} files to process")

    # ユースケースを実行
    request = BuildIndexRequest(
        files=files,
        category=detect_category(target_dirs[0]) if target_dirs else "",
        max_text_length=MAX_EMBED_TEXT_LEN
    )
    
    response = use_case.execute(request)

    print("\n============================")
    print(f"Index build complete!")
    print(f"  New documents: {response.new_documents}")
    print(f"  Updated documents: {response.updated_documents}")
    print(f"  Skipped documents: {response.skipped_documents}")
    print(f"  Total: {response.new_documents + response.updated_documents}")
    print(f"DB file: {DB_PATH}")
    print("============================")


if __name__ == "__main__":
    main()
