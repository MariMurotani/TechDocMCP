"""
Document エンティティ - ドメイン層の中核
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Document:
    """
    技術ドキュメントを表すエンティティ
    """
    id: Optional[int] = None
    path: str = ""
    url: str = ""
    text: str = ""
    category: str = ""

    def is_valid(self) -> bool:
        """ドキュメントが有効かどうかを判定"""
        return bool(self.path and self.text and self.category)

    def has_content(self, min_length: int = 200) -> bool:
        """最小限のコンテンツを持っているかチェック"""
        return len(self.text.strip()) >= min_length

    def get_word_count(self) -> int:
        """単語数を取得"""
        return len(self.text.split())
