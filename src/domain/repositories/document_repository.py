"""
DocumentRepository インターフェース - Repository パターン
外部実装（SQLite、PostgreSQL等）から独立させる
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from pathlib import Path
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.entities import Document, SearchResult


class DocumentRepository(ABC):
    """ドキュメント永続化のインターフェース"""

    @abstractmethod
    def save(self, document: Document) -> Document:
        """
        ドキュメントを保存（作成または更新）
        
        Args:
            document: 保存するドキュメント
            
        Returns:
            保存されたドキュメント（IDを含む）
        """
        pass

    @abstractmethod
    def find_by_path(self, path: str) -> Optional[Document]:
        """パスでドキュメントを検索"""
        pass

    @abstractmethod
    def find_by_id(self, doc_id: int) -> Optional[Document]:
        """IDでドキュメントを検索"""
        pass

    @abstractmethod
    def delete_by_id(self, doc_id: int) -> bool:
        """IDでドキュメントを削除"""
        pass

    @abstractmethod
    def search_by_vector(
        self, 
        vector: np.ndarray, 
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        ベクトル類似度検索
        
        Args:
            vector: クエリベクトル
            category: カテゴリでフィルタ（Noneの場合は全て）
            top_k: 返す結果数
            
        Returns:
            (Document, スコア)のタプルリスト、スコア昇順
        """
        pass

    @abstractmethod
    def find_all_by_category(self, category: str) -> List[Document]:
        """カテゴリで全ドキュメントを検索"""
        pass

    @abstractmethod
    def delete_by_domain(self, domain: str) -> int:
        """特定ドメインの全ドキュメントを削除，削除数を返す"""
        pass

    @abstractmethod
    def save_embedding(self, doc_id: int, embedding: np.ndarray) -> None:
        """ドキュメントの埋め込みベクトルを保存"""
        pass
