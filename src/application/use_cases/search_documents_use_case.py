"""
検索ドキュメントユースケース
"""
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.entities import SearchResult
from domain.repositories import DocumentRepository
from infrastructure.models import EmbeddingModel


@dataclass
class SearchDocumentsRequest:
    """検索リクエストDTO"""
    query: str
    category: Optional[str] = None
    top_k: int = 5


@dataclass
class SearchDocumentsResponse:
    """検索レスポンスDTO"""
    results: List[SearchResult]
    query: str
    category: Optional[str]
    total_results: int


class SearchDocumentsUseCase:
    """ドキュメント検索のユースケース"""

    def __init__(
        self,
        repository: DocumentRepository,
        embedding_model: EmbeddingModel
    ):
        self.repository = repository
        self.embedding_model = embedding_model

    def execute(self, request: SearchDocumentsRequest) -> SearchDocumentsResponse:
        """
        検索を実行
        
        Args:
            request: 検索リクエスト
            
        Returns:
            検索レスポンス
        """
        # クエリをベクトルにエンコード
        query_vector = self.embedding_model.encode(request.query)

        # リポジトリで検索
        results = self.repository.search_by_vector(
            query_vector,
            category=request.category,
            top_k=request.top_k
        )

        # SearchResult に変換
        search_results = [
            SearchResult.from_document(doc, score)
            for doc, score in results
        ]

        return SearchDocumentsResponse(
            results=search_results,
            query=request.query,
            category=request.category,
            total_results=len(search_results)
        )
