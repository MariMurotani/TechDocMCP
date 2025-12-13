# TechDocMCP

技術ドキュメントをベクトル検索できるMCPサーバー。Markdown/HTMLファイルからテキストを抽出し、埋め込みベクトルを使った類似度検索を提供します。

## 特徴

- 複数のドキュメントディレクトリをインデックス化
- カテゴリ別（TypeScript/Python/CDK/Vue等）の検索
- ベクトル検索による意味的類似度マッチング
- MCP（Model Context Protocol）対応

## 必要要件

- Python 3.9以上
- Git LFS（大容量DBファイルの管理用）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/MariMurotani/TechDocMCP.git
cd TechDocMCP

# 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または .venv\Scripts\activate  # Windows

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
```

これにより `src/techdocs.db` が生成されます。

**プレビルトDB**: [techdocs.db](https://drive.google.com/file/d/1AQlQbadGWaWdjWxpyzQGUPx5kRiVXvVh/view?usp=sharing)

## MCPサーバーの起動

### Cursorでの設定

#### 1. mcp.jsonファイルを開く

macOSの場合:
```bash
open ~/.cursor/mcp.json
```

Windowsの場合:
```bash
notepad %USERPROFILE%\.cursor\mcp.json
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

#### 3. Cursorを再起動

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

### 利用可能なツール

FastMCPを使用した5つの専用検索ツールがあります：

- **`pytool`** - Python専用ドキュメント検索
- **`tytool`** - TypeScript専用ドキュメント検索
- **`cdktool`** - AWS CDK専用ドキュメント検索
- **`vuetool`** - Vue.js専用ドキュメント検索
- **`awstool`** - AWS Design専用ドキュメント検索

Cursorが質問内容から自動的に適切なツールを選択します。

<img src="https://private-user-images.githubusercontent.com/4035504/526131809-930bbb3a-0974-41cb-b93d-d1bb81cc645b.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjU1OTAzOTcsIm5iZiI6MTc2NTU5MDA5NywicGF0aCI6Ii80MDM1NTA0LzUyNjEzMTgwOS05MzBiYmIzYS0wOTc0LTQxY2ItYjkzZC1kMWJiODFjYzY0NWIucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI1MTIxMyUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTEyMTNUMDE0MTM3WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9ZjUzMDQ4N2IyZWRjZDhhYjI5NTNhNmFkZTI4OGJiNTk0ZTQ1OTgzN2U3ZjI3YWM2YmY3ZDM1NGQwODhkNGZmMCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.Tb1kwBSRbRQFVPHises5Gx188HPt_R0IWI2kL3SwjNg" />

### 質問例

MCPサーバーが起動していれば、以下のような自然な質問で検索できます：

**TypeScriptの質問（`tytool`が呼ばれる）:**
```
TypeScriptのGenericsについて教えて
```

```
TypeScriptでinterfaceとtypeの違いは？
```

**Pythonの質問（`pytool`が呼ばれる）:**
```
Pythonでデコレータを使う方法は？
```

```
Pythonのasync/awaitについて教えて
```

**AWS CDKの質問（`cdktool`が呼ばれる）:**
```
CDKでLambda関数を作成するには？
```

```
CDKのConstructについて説明して
```

**Vue.jsの質問（`vuetool`が呼ばれる）:**
```
Vueのcomposablesの使い方を知りたい
```

```
VueのComposition APIについて
```

**AWS Designの質問（`awstool`が呼ばれる）:**
```
AWSのWell-Architected Frameworkについて教えて
```

```
AWSのアーキテクチャパターンを知りたい
```

Cursorが自動的に適切なツールを選択して呼び出します。

### 全カテゴリから検索

**注意**: 現在の実装では各ツールがカテゴリ専用です。複数カテゴリを横断検索する場合は、個別に質問してください。

### 明示的なツール呼び出し

ツールを直接指定することもできます：

**TypeScript検索:**
```
tytoolでGenericsについて検索して
```

**Python検索:**
```
pytoolでデコレータについて教えて
```

**CDK検索:**
```
cdktoolでLambda関数の作り方を検索
```

**Vue検索:**
```
vuetoolでComposablesについて調べて
```

**AWS Design検索:**
```
awstoolでWell-Architected Frameworkについて検索
```

### 検索結果数の指定

```
TypeScriptのGenericsについて、詳しく知りたいので10件検索して
```

各ツールは `top_k` パラメータで結果数を調整できます（1-10件、デフォルト: 5件）。

### ChatGPTからの呼び出し例

ChatGPT（GPT-4やGPT-4o）でMCPサーバーを設定している場合：

**例1: TypeScriptの型について**
```
TypeScriptのUtility Typesについて、tytoolで検索して詳しく教えて
```

**例2: Pythonの非同期処理**
```
pytoolを使って、Pythonのasyncioについて調べてください
```

**例3: CDKのベストプラクティス**
```
cdktoolでAWS CDKのベストプラクティスを検索
```

**例4: Vueのリアクティビティ**
```
vuetoolを使ってVue 3のreactivityシステムについて説明して
```

ChatGPTが自動的にMCPツールを呼び出し、ローカルドキュメントの内容に基づいて回答します。

### ツールパラメータ

各ツール（`pytool`, `tytool`, `cdktool`, `vuetool`）は以下のパラメータを受け取ります：

- `query` (必須): 検索クエリ（例: "generics", "decorators", "lambda function"）
- `top_k` (オプション): 返す結果数（1-10、デフォルト: 5）

**例:**
```
tytool(query="generics", top_k=10)
```

## 開発

```bash
# コードフォーマット
black src/
isort src/

# 型チェック
mypy src/

# Linter
flake8 src/
```

## ライセンス

MIT
