NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "yourpassword"

# 料理研究とは別のデータベース名
NEO4J_DATABASE = "techdocs"

# テキスト抽出時に除去するノイズパターン
NOISE_PATTERNS = [
    r'Was this page helpful\?',
    r'Was this helpful\?',
    r'Is this page helpful\?',
    r'Rate this page',
    r'Feedback',
    r'Edit this page',
    r'Edit on GitHub',
    r'Share on Twitter',
    r'Share on Facebook',
    r'Copy link',
    r'Table of contents',
    r'On this page',
    r'In this article',
    r'Skip to .*',
    r'Jump to .*',
    r'Back to top',
    r'Next chapter',
    r'Previous chapter',
    r'Print this page',
    r'Download PDF',
    r'={3,}',  # 区切り線（===== など）
    r'-{3,}',  # 区切り線（----- など）
    # Contributor/著者情報の除去
    r'Contributors?:.*',
    r'Authors?:.*',
    r'Written by.*',
    r'Edited by.*',
    r'Reviewed by.*',
    r'Maintainers?:.*',
    r'Last updated by.*',
    r'Last modified by.*',
    r'Created by.*',
]

# ローカルパスのベースディレクトリ
LOCAL_DOCS_BASE = "/Users/marimurotani/docs/"

# 埋め込み生成時に使用する本文の最大文字数
# 長すぎる場合は処理が重くなるため上限を設ける
# 既定: 15000 文字（必要に応じて増減可）
MAX_EMBED_TEXT_LEN = 15000

# ブロックするドメイン（広告、トラッキング、分析系など）
# 以下に一致するドメインは処理から除外
DOMAIN_BLOCKLIST = [
    # 広告・広告ネットワーク
    "googlesyndication.com",
    "googleadservices.com",
    "adservice.google.com",
    "ads.google.com",
    "pagead2.googlesyndication.com",
    "doubleclick.net",
    "amazon-adsystem.com",
    "adnxs.com",
    "appnexus.com",
    "criteo.com",
    "rubiconproject.com",
    "openx.com",
    "pubmatic.com",
    "conversantmedia.com",
    "contextweb.com",
    
    # トラッキング・分析
    "google-analytics.com",
    "analytics.google.com",
    "googletagmanager.com",
    "mixpanel.com",
    "amplitude.com",
    "hotjar.com",
    "intercom.com",
    "inspectlet.com",
    "mouseflow.com",
    "userreplay.net",
    "fullstory.com",
    "loggly.com",
    "newrelic.com",
    "segment.com",
    
    # CDN・リソース配信（不要な外部リソース）
    "cdn.optimizely.com",
    "cdn.segment.com",
    "platform.twitter.com",
    "connect.facebook.net",
    
    # ソーシャルメディア埋め込み
    "instagram.com",
    
    # 外部チャット・サポート
    "liveperson.net",
    "surveymonkey.com",
    "typeform.com",
]

# 行単位で除去する軽微ノイズ（完全一致/短い見出し類）
PER_LINE_NOISE_PATTERNS = [
    r"^Try$",
    r"^Footnotes$",
    r"^Source code:\s*$",
    r"^Was this page helpful\?\s*$",
    r"^Powered by GitBook$",
    r"^On this page$",
    r"^Copy$",
    r"^Ctrl\s+k$",
    r"^README$",
    r"^Getting Started$",
    r"^TypeScript Deep Dive$",
    r"^Future JavaScript Now$",
    r"^TypeScript's Type System$",
    r"^Project$",
    r"^Node\.js QuickStart$",
    r"^Browser QuickStart$",
    r"^Library QuickStart$",
    r"^JS Migration Guide$",
    r"^Errors in TypeScript$",
    r"^TypeScript Compiler Internals$",
    r"^Options$",
    r"^Testing$",
    r"^Tools$",
    r"^TIPs$",
    r"^NPM$",
]
