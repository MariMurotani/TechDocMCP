"""
埋め込みモデルとDBを事前にダウンロードするスクリプト

初回起動時にモデルのダウンロードで時間がかかるのを避けるため、
事前にモデルをキャッシュしておくためのスクリプトです。
また、プレビルトのtechdocs.dbをダウンロードします。
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

try:
    import gdown
except ImportError:
    print("gdownライブラリが必要です。")
    print("インストールするには以下を実行してください:")
    print("  pip install gdown")
    exit(1)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DB_FILE_ID = "1AQlQbadGWaWdjWxpyzQGUPx5kRiVXvVh"
DB_PATH = Path(__file__).parent / "techdocs.db"


def download_model():
    """埋め込みモデルをダウンロード"""
    print(f"Downloading embedding model: {MODEL_NAME}")
    print("This may take a few minutes on first run...")
    
    # モデルをダウンロード（キャッシュに保存される）
    model = SentenceTransformer(MODEL_NAME)
    
    print(f"\n✓ Model successfully downloaded and cached!")
    print(f"  Model name: {MODEL_NAME}")
    print(f"  Embedding dimension: {model.get_sentence_embedding_dimension()}")


def download_db():
    """techdocs.dbをGoogle Driveからダウンロード"""
    if DB_PATH.exists():
        print(f"\n✓ Database already exists at {DB_PATH}")
        return
    
    print(f"\nDownloading database from Google Drive...")
    print(f"  File ID: {DB_FILE_ID}")
    
    try:
        url = f"https://drive.google.com/uc?id={DB_FILE_ID}"
        gdown.download(url, str(DB_PATH), quiet=False)
        print(f"\n✓ Database successfully downloaded!")
        print(f"  Location: {DB_PATH}")
    except Exception as e:
        print(f"\n✗ Failed to download database: {e}")
        print(f"  Please download manually from:")
        print(f"  https://drive.google.com/file/d/{DB_FILE_ID}/view?usp=sharing")
        print(f"  and save it to: {DB_PATH}")


def main():
    download_model()
    download_db()
    print("\n✓ All downloads completed!")


if __name__ == "__main__":
    main()
