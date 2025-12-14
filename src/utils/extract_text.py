import re
import sys
from pathlib import Path

import frontmatter
import markdown

# 高品質な本文抽出のためのライブラリ（常に使用）
import trafilatura

# 親ディレクトリをパスに追加してconfigをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import NOISE_PATTERNS, PER_LINE_NOISE_PATTERNS


class ExtractTextError(Exception):
    """Base class for extract_text-related errors."""


class FileReadError(ExtractTextError):
    def __init__(self, path: str, original: Exception):
        super().__init__(f"Failed to read file: {path}")
        self.path = path
        self.original = original


class HtmlParseError(ExtractTextError):
    def __init__(self, path: str, original: Exception):
        super().__init__(f"Failed to parse HTML: {path}")
        self.path = path
        self.original = original


class MarkdownParseError(ExtractTextError):
    def __init__(self, path: str, original: Exception):
        super().__init__(f"Failed to parse Markdown: {path}")
        self.path = path
        self.original = original


def clean_text(text):
    """
    抽出したテキストから不要なノイズを除去する。
    """
    #print("[DEBUG] Original text length:", len(text))
    #print("[DEBUG] Original text preview:", text[:500])
    
    # CSS/HTMLの残骸パターンを除去
    css_patterns = [
        r'\b(font-family|font-size|font-weight|line-height|color|background|padding|margin):\s*[^;]+;?',
        r'\b(Roboto|Arial|Helvetica|Noto|Sans|Serif|Courier)\b',
        r'rgba?\([^)]+\)',
        r'#[0-9a-fA-F]{3,6}\b',
        r'\d+px\b',
        r'\d+em\b',
        r'\d+%\b',
    ]
    for pattern in css_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    #print("[DEBUG] After CSS removal length:", len(text))
    
    # UIフィードバックや一般的なノイズフレーズを削除
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 行単位ノイズを除去
    if PER_LINE_NOISE_PATTERNS:
        lines = text.split('\n')
        compiled = [re.compile(p, re.IGNORECASE) for p in PER_LINE_NOISE_PATTERNS]
        kept = []
        for line in lines:
            stripped = line.strip()
            if any(rx.search(stripped) for rx in compiled):
                continue
            kept.append(line)
        text = '\n'.join(kept)
    
    # Contributor/著者セクションを除去（複数行対応）
    # "Contributors:" のような見出しから次の見出しや空行が続くまでを削除
    contributor_patterns = [
        r'(?i)^contributors?:\s*$.*?(?=\n\s*\n|\n[A-Z]|\Z)',
        r'(?i)^authors?:\s*$.*?(?=\n\s*\n|\n[A-Z]|\Z)',
        r'(?i)^maintainers?:\s*$.*?(?=\n\s*\n|\n[A-Z]|\Z)',
        r'(?i)^written by.*?(?=\n\s*\n|\n[A-Z]|\Z)',
        r'(?i)^edited by.*?(?=\n\s*\n|\n[A-Z]|\Z)',
        r'(?i)^reviewed by.*?(?=\n\s*\n|\n[A-Z]|\Z)',
    ]
    for pattern in contributor_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
    
    # タイトル重複を除去（連続する同一行を削除）
    # 例: "Saga pattern\nSaga pattern" -> "Saga pattern"
    lines = text.split('\n')
    deduped_lines = []
    prev_line = None
    for line in lines:
        stripped = line.strip()
        # 空行は保持、同じ内容の連続は除去
        if not stripped:  # 空行
            deduped_lines.append(line)
            prev_line = None
        elif stripped != prev_line:
            deduped_lines.append(line)
            prev_line = stripped
        # else: 前の行と同じなのでスキップ
    text = '\n'.join(deduped_lines)
    
    #print("[DEBUG] After title dedup length:", len(text))
    
    # 改行で分断された単語を修復（例: "example\nve" -> "example"）
    # 小文字で終わり、次行が小文字で始まる場合は結合
    before_fix = text
    text = re.sub(r'([a-z])\n([a-z]{1,3}\b)', r'\1\2', text)
    
    #if before_fix != text:
        #print("[DEBUG] Line break fixes applied")
    
    # 連続する空白を1つに（改行以外）
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 適切な改行を挿入（文の終わりや大文字で始まる箇所で改行）
    # ピリオド+大文字、または既存の改行を保持
    text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)
    
    # 連続する空白行を圧縮（2行以上の空行を1行に）
    text = re.sub(r'\n\s*\n(\s*\n)+', '\n\n', text)
    
    # 行末の空白を削除
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    
    #print("[DEBUG] Final text length:", len(text))
    #print("[DEBUG] Final text preview:", text[:500])
    #print("[DEBUG] " + "="*50)
    
    return text.strip()


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError as exc:
        raise FileReadError(path, exc) from exc


def _is_html_like(path: str) -> bool:
    lower = path.lower()
    return lower.endswith((".html", ".htm"))


def _sniff_html(path: str) -> bool:
    try:
        snippet = _read_file(path)[:2048]
    except FileReadError:
        return False
    sniff = snippet.lower()
    return "<html" in sniff or "<!doctype" in sniff


def extract_from_html(path):
    """
    HTMLファイルから本文のみを抽出する。
    Trafilaturaで主要コンテンツを抽出し、ノイズを除去する。
    """
    try:
        html = _read_file(path)
        extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
    except FileReadError:
        raise
    except Exception as exc:  # Trafilatura parsing errors
        raise HtmlParseError(path, exc) from exc

    if extracted and extracted.strip():
        return clean_text(extracted)

    return ""


def extract_from_md(path):
    """
    Markdownファイルから本文のみを抽出する。
    Front matterを除外し、HTMLに変換後テキストを抽出。
    """
    try:
        raw = _read_file(path)
        md = frontmatter.loads(raw)
        body = md.content
        html = markdown.markdown(body)
    except FileReadError:
        raise
    except Exception as exc:
        raise MarkdownParseError(path, exc) from exc

    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    text = clean_text(text)
    return text


def extract_text(path):
    """Extract text from HTML/Markdown and html-like files without extensions."""
    lower = path.lower()
    try:
        if lower.endswith(".md"):
            return extract_from_md(path)
        if _is_html_like(path) or ("." not in path and _sniff_html(path)):
            return extract_from_html(path)
        return ""
    except ExtractTextError:
        # Fail-safe: skip problematic files to keep indexing running
        return ""
