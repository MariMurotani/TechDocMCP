# TechDocMCP

技術ドキュメントをベクトル検索できるMCPサーバー。Markdown/HTMLファイルからテキストを抽出し、埋め込みベクトルを使った類似度検索を提供します。

## 特徴

- 複数のドキュメントディレクトリをインデックス化
- カテゴリ別（TypeScript/Python/CDK/Vue等）の検索
- ベクトル検索による意味的類似度マッチング
- MCP（Model Context Protocol）対応

## 必要要件

- Python 3.9以上
- Node.js v22.6.0（MCP Inspector のインストール/利用に推奨）
 
## インストール

```bash
# リポジトリをクローン
git clone https://github.com/MariMurotani/TechDocMCP.git
cd TechDocMCP

# 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 依存パッケージをインストール
pip install -r src/requirements.txt

# 埋め込みモデルを事前ダウンロード（初回のみ、起動を高速化）
python src/download_model.py

# MCP Inspector（デバッグ用）をインストール
npm install -g @modelcontextprotocol/inspector
```

## DBのセットアップ

### オプション1: スクリプトで自動ダウンロード

モデルとデータベースの両方を自動的にダウンロードできます：

```bash
# 埋め込みモデルとプレビルトDBをダウンロード
python src/download_model.py
```

このコマンドにより以下がダウンロードされます：
- 埋め込みモデル（`sentence-transformers/all-MiniLM-L6-v2`）
- プレビルトデータベース（`src/techdocs.db`）

### オプション2: 自分でDBをビルド

ドキュメントをインデックス化してデータベースを構築します。

```bash
# src/build_index.py の TARGET_DIRS を編集してドキュメントパスを指定
# 例: /Users/yourname/docs/typescript など

# インデックスをビルド
python src/build_index.py

# 特定カテゴリのみ（typescript/python/cdk/vue/aws_design）
python src/build_index.py --category vue
```

これにより `src/techdocs.db` が生成されます。

**プレビルトDB**: [techdocs.db](https://drive.google.com/file/d/1AQlQbadGWaWdjWxpyzQGUPx5kRiVXvVh/view?usp=sharing)

## MCPサーバーの起動

### CursorやVSCodeでの設定

#### 1. mcp.jsonファイルを開く

macOSの場合:
```bash
open ~/.cursor/mcp.json
```

ファイルが存在しない場合は、新規作成してください。

#### 2. 設定を追加

以下の設定を `mcp.json` に追加します（**パスは自分の環境に合わせて修正してください**）:

```json
{
  "mcpServers": {
    "techdoc": {
      "command": "/Users/yourname/Sources/TechDocMCP/.venv/bin/python",
      "args": ["/Users/yourname/Sources/TechDocMCP/src/mcp_server_fastmcp.py"]
    }
  }
}
```

既に他のMCPサーバーが設定されている場合は、`"techdoc"`の部分だけを追加してください。

#### 3. CursorやVSCodeを再起動

設定を保存してCursorを完全に再起動すると、技術ドキュメント検索ツールが利用可能になります。

#### 4. 動作確認

Cursorのステータスバーまたは設定画面で、`techdoc` MCPサーバーが "Running" 状態になっていることを確認してください。

### デバッグ

MCPサーバーをデバッグする場合は、以下のコマンドを実行してMCP Inspectorを使用できます：

```bash
npx @modelcontextprotocol/inspector \
  /Users/marimurotani/Sources/TechDocMCP/.venv/bin/python \
  src/mcp_server_fastmcp.py
```

**注意**: パスは自分の環境に合わせて修正してください。

このコマンドでブラウザベースのデバッグUIが起動し、MCPサーバーの動作状況や通信内容を確認できます。

## 使い方

Cursorのチャットで、MCPツールを使って検索できます。

## MCPサーバーの起動
1. Ctrl + Shit + P (MAC)
2. List MCP Servers
<img width="622" height="95" alt="Image" src="https://github.com/user-attachments/assets/d02586a3-afed-4985-8e9e-7cb627801c0a" />
3. Select MCP Servers
<img width="309" height="191" alt="Image" src="https://github.com/user-attachments/assets/4702a281-527b-46fc-ab0e-5b9092d2670c" />
4. Start
<img width="365" height="153" alt="Image" src="https://github.com/user-attachments/assets/a210f9b4-df34-4114-ae63-1cc660336f8d" />

### 利用可能なツール

FastMCPを使用した5つの専用検索ツールがあります：

- **`pytool`** - Python専用ドキュメント検索
- **`tytool`** - TypeScript専用ドキュメント検索
- **`cdktool`** - AWS CDK専用ドキュメント検索
- **`vuetool`** - Vue.js専用ドキュメント検索
- **`awstool`** - AWS Design専用ドキュメント検索

Cursor/Copilotが質問内容から自動的に適切なツールを選択します。

<img width="567" height="384" alt="Image" src="https://github.com/user-attachments/assets/c583a16d-cc55-4ea7-a2c2-930080139e20" />

### 質問例

MCPサーバーが起動していれば、以下のような自然な質問で検索できます：

リファクタリングアドバイスを受けてみましょう

<img width="567" height="384" alt="Image" src="https://github.com/user-attachments/assets/c583a16d-cc55-4ea7-a2c2-930080139e20" />
<img width="563" height="684" alt="Image" src="https://github.com/user-attachments/assets/10bafeac-5fce-400d-bdc7-17a782bbdde5" />

----
リファクタリングアドバイスを受けてから
コード修正案を出してもらいます

<img width="442" height="324" alt="Image" src="https://github.com/user-attachments/assets/a3ca5532-ef40-4565-94b7-704f3b5484ec" />
<img width="443" height="664" alt="Image" src="https://github.com/user-attachments/assets/aef76c0c-2894-45bc-a227-1da1d3c6766e" />

### 参照ドキュメント

各ツールが参照する主なドメインを一覧化します

- pytool
  - docs.python.org: Python公式ドキュメント
  - mypy.readthedocs.io: Mypy公式ドキュメント
  - black.readthedocs.io: Black公式ドキュメント
  - peps.python.org: PEP一覧/仕様
  - docs.pytest.org: Pytest公式ドキュメント
  - www.thedigitalcatbooks.com: Clean Architecture in Python（書籍サイト）
  - その他ブログなど

- tytool
  - www.typescriptlang.org: TypeScript公式ドキュメント
  - basarat.gitbook.io: TypeScript Deep Dive
  - eslint.org: ESLintドキュメント
  - jestjs.io: Jestドキュメント
  - dev.to: 記事（クリーンアーキテクチャ等）
  - typeorm.io: TypeORMドキュメント
  - playwright.dev: Playwrightドキュメント
　- その他ブログなど

- cdktool
  - docs.aws.amazon.com: AWS CDK API/ガイド

- vuetool
  - vuejs.org: Vue公式ドキュメント
  - ja.vuejs.org: Vue日本語ドキュメント

- awstool
  - aws.amazon.com: アーキテクチャベストプラクティス/ブログ
  - docs.aws.amazon.com: Well-Architected等の設計ガイド
  - ja.vuejs.org: 参考記事（AWS設計関連の和訳ドキュメントを追加）
  - refactoring.guru: デザインパターン（設計参考）
  - docs.aws.amazon.com/: デベロッパーズガイド 
    - aurora, aurora-dsql
    - serverless
    - amazondynamodb
    - step-functions
    - appsync
    - lambda
    - wellarchitected
    - prescriptive-guidance


### ツールパラメータ

各ツール（`pytool`, `tytool`, `cdktool`, `vuetool`）は以下のパラメータを受け取ります：

- `query` (必須): 検索クエリ（例: "generics", "decorators", "lambda function"）
- `top_k` (オプション): 返す結果数（1-10、デフォルト: 5）

**例:**
```
tytool(query="generics", top_k=10)
```
