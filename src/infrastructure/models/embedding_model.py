"""
埋め込みモデル管理サービス
"""
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingModel:
    """埋め込みモデルの初期化と管理"""

    _instance: 'EmbeddingModel' = None  # シングルトン
    _model: SentenceTransformer = None

    def __new__(cls):
        """シングルトンパターン - モデルを1回だけ読み込む"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """モデルを初期化"""
        print("Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("Model loaded successfully")

    def encode(self, text: str) -> np.ndarray:
        """テキストをベクトルにエンコード"""
        return self._model.encode(text).astype("float32")

    def encode_batch(self, texts: list) -> np.ndarray:
        """複数のテキストをバッチでエンコード"""
        return self._model.encode(texts).astype("float32")
