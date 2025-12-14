"""
SearchResult エンティティ
"""
from dataclasses import dataclass


@dataclass
class SearchResult:
    """検索結果を表すエンティティ"""
    path: str
    url: str
    category: str
    text: str
    score: float

    @staticmethod
    def from_document(document, score: float = 0.0):
        """Document エンティティから SearchResult を作成"""
        return SearchResult(
            path=document.path,
            url=document.url,
            category=document.category,
            text=document.text,
            score=score
        )
