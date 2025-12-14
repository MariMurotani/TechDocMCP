"""
ドキュメント索引構築ユースケース
"""
from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path
import sys

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.entities import Document
from domain.repositories import DocumentRepository
from infrastructure.models import EmbeddingModel
from policies.content_policy import ContentPolicy


@dataclass
class BuildIndexRequest:
    """索引構築リクエスト"""
    files: list  # ファイルパスのリスト
    category: str = ""
    max_text_length: int = 120000


@dataclass
class BuildIndexResponse:
    """索引構築レスポンス"""
    new_documents: int
    updated_documents: int
    skipped_documents: int


class BuildIndexUseCase:
    """ドキュメント索引構築のユースケース"""

    def __init__(
        self,
        repository: DocumentRepository,
        embedding_model: EmbeddingModel,
        content_policy: ContentPolicy,
        extract_text_func: Callable,
        path_to_url_func: Callable,
        logger: Optional[Callable] = None
    ):
        """
        Args:
            repository: ドキュメントリポジトリ
            embedding_model: 埋め込みモデル
            content_policy: コンテンツポリシー
            extract_text_func: テキスト抽出関数
            path_to_url_func: パスをURLに変換する関数
            logger: ログ出力関数
        """
        self.repository = repository
        self.embedding_model = embedding_model
        self.content_policy = content_policy
        self.extract_text_func = extract_text_func
        self.path_to_url_func = path_to_url_func
        self._logger = logger or print

    def execute(self, request: BuildIndexRequest) -> BuildIndexResponse:
        """
        索引を構築
        
        Args:
            request: 索引構築リクエスト
            
        Returns:
            索引構築レスポンス
        """
        new_count = 0
        updated_count = 0
        skipped_count = 0

        for file_path in request.files:
            self._logger(f"Processing: {file_path}")

            # テキストを抽出
            try:
                text = self.extract_text_func(file_path)
            except Exception as e:
                self._logger(f"  ⊘ Failed to extract text: {e}")
                skipped_count += 1
                continue

            if not text.strip():
                self._logger(f"  ⊘ No text content")
                skipped_count += 1
                continue

            # コンテンツが有意義かチェック
            if not self.content_policy.is_meaningful_for(file_path, text):
                self._logger(f"  ⊘ Not meaningful content")
                skipped_count += 1
                continue

            # ドキュメントエンティティを作成
            url = self.path_to_url_func(file_path)
            document = Document(
                path=file_path,
                url=url,
                text=text,
                category=request.category
            )

            # リポジトリに保存
            try:
                saved_doc = self.repository.save(document)
                
                # 埋め込みを生成して保存
                embedding_text = text[:request.max_text_length]
                embedding = self.embedding_model.encode(embedding_text)
                self.repository.save_embedding(saved_doc.id, embedding)

                if document.id is None:
                    new_count += 1
                    self._logger(f"  ✓ Indexed (new)")
                else:
                    updated_count += 1
                    self._logger(f"  ✓ Updated")
            except Exception as e:
                self._logger(f"  ⊘ Failed to save: {e}")
                skipped_count += 1

        return BuildIndexResponse(
            new_documents=new_count,
            updated_documents=updated_count,
            skipped_documents=skipped_count
        )
