## クイックスタート

### 1. 環境設定

```bash
# プロジェクトのクローン
git clone <repository-url>
cd tuukaa

# 環境変数の設定（開発環境用の最小構成）
cat > .env << EOF
OPENAI_API_KEY=your_actual_api_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=tuukaa
DEBUG=true
EOF
```

**⚠️ 本番環境の設定は必ず以下のドキュメントを参照してください:**

- [セキュリティガイド](docs/SECURITY.md) - デプロイ前チェックリスト
- [バックエンド環境変数テンプレート](docs/env.example) - バックエンドの環境変数設定
- [フロントエンド環境変数テンプレート](docs/frontend.env.local.example) - フロントエンドの環境変数設定
- [環境変数移行ガイド](docs/ENV_MIGRATION.md) - 既存の.env.example からの移行方法
- [フロントエンド環境変数ガイド](docs/FRONTEND_ENV.md) - フロントエンド設定の詳細

### 2. サービス起動（Docker Compose）

```bash
# フルスタックアプリケーションを一括起動
docker-compose up --build

# バックグラウンド起動の場合
docker-compose up -d --build
```

### 3. 動作確認

- **メインアプリ**: http://localhost:3000（Next.js フロントエンド）
- **API 文書**: http://localhost:8000/docs（FastAPI Swagger）
- **ヘルスチェック**: http://localhost:8000/health（バックエンド状態）

## 使用方法（各フェーズの比較）

### フェーズ 1（Streamlit UI）

```bash
# ブラウザでシンプルなUI操作
# http://localhost:8501
```

### フェーズ 2（REST API）

```bash
# curlコマンドによるAPI操作（現行ルート）
curl -X POST "http://localhost:8000/api/v1/pdf/upload" \
  -F "file=@document.pdf"

curl -X POST "http://localhost:8000/api/v1/pdf/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "命名規則は？"}'
```

### フェーズ 3（Web アプリケーション）

```bash
# モダンなWebブラウザUI
# http://localhost:3000
# - ファイルドラッグ&ドロップ
# - リアルタイム検索
# - レスポンシブデザイン
# - TypeScript型安全
```

## 技術スタック

### フロントエンド

- **フレームワーク**: Next.js 15.4.5（App Router）
- **言語**: TypeScript 5
- **スタイリング**: Tailwind CSS 4
- **開発環境**: ESLint + Prettier
- **ビルドツール**: Turbopack

### バックエンド

- **フレームワーク**: FastAPI 0.104.1
- **言語**: Python 3.11
- **AI/ML**: LangChain 0.3.25 + OpenAI
- **ベクトル DB**: ChromaDB 1.0.12
- **開発環境**: Poetry + Black + isort

### インフラ・DevOps

- **コンテナ**: Docker + Docker Compose
- **リバースプロキシ**: 将来的に Nginx 対応予定
- **環境管理**: .env + pydantic-settings

## セキュリティ

### 脆弱性スキャン

プロジェクトの依存関係に脆弱性がないか定期的にチェックしてください：

```bash
# 自動スキャン（バックエンド + フロントエンド）
./scripts/security-check.sh

# 手動スキャン
cd backend && poetry run safety check
cd frontend && npm run audit:production
```

詳細は[セキュリティガイド](docs/SECURITY.md)を参照してください。

### デプロイ前チェックリスト

本番環境へのデプロイ前に以下を確認してください：

- [ ] 環境変数が適切に設定されている（`.env.example`参照）
- [ ] `DEBUG=false`に設定されている
- [ ] 強力なシークレットが設定されている（32 文字以上）
- [ ] CORS 設定がホワイトリスト方式になっている
- [ ] 依存関係の脆弱性スキャンを実行した
- [ ] Redis に認証が設定されている

## 開発者向け情報

### ローカル開発（個別起動）

#### フロントエンド開発

```bash
cd frontend
npm install
npm run dev          # 開発サーバー（ホットリロード）
npm run build        # 本番ビルド
npm run lint         # コード品質チェック
npm run type-check   # TypeScript型チェック
```

#### バックエンド開発

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 開発環境

#### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# 個別サービスのログ
docker-compose logs -f frontend
docker-compose logs -f backend
```

#### デバッグ

```bash
# フロントエンドコンテナにアクセス
docker-compose exec frontend sh

# バックエンドコンテナにアクセス
docker-compose exec backend bash
```

#### ホットリロード

- **フロントエンド**: ファイル保存で自動リロード（Next.js 開発サーバー）
- **バックエンド**: ファイル保存で自動再起動（uvicorn --reload）

## 継承機能（フェーズ 1・2 から）

### 完全継承される機能

- ✅ PDF 文書処理（PyPDF2）
- ✅ RAG 処理（LangChain + OpenAI）
- ✅ ベクトルストア（ChromaDB 永続化）
- ✅ REST API（全エンドポイント）
- ✅ Docker 環境（マルチコンテナ対応）

### 新機能（フェーズ 3 で追加）

- 🆕 モダン WebUI（Next.js + TypeScript）
- 🆕 レスポンシブデザイン（モバイル対応）
- 🆕 リアルタイム UI 更新
- 🆕 型安全なフロントエンド開発
- 🆕 本格的な Web アプリケーション体験

## API 仕様（現行）

### エンドポイント一覧（PDF / LP / Embed）

- PDF
  - `POST /api/v1/pdf/upload` - PDF 文書アップロード
  - `POST /api/v1/pdf/ask` - 質問・回答生成
  - `POST /api/v1/pdf/search` - 文書検索のみ
  - `GET /api/v1/pdf/system/info` - システム情報取得
  - `POST /api/v1/pdf/system/reset` - ベクトルストアリセット
- LP（雛形）
  - `GET /api/v1/lp/`
  - `POST /api/v1/lp/generate`
  - `POST /api/v1/lp/proofread`
- Embed（雛形）
  - `GET /api/v1/embed/`
  - `POST /api/v1/embed/ingest`
  - `POST /api/v1/embed/chat`

既存の `/api/v1/{upload,ask,search}` は廃止済みです。

### 利用例

```javascript
// フロントエンドからのAPI呼び出し例
const response = await fetch("/api/v1/pdf/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "クラスの命名規則は？",
    top_k: 2,
  }),
});
const data = await response.json();
```

## デプロイメント

### 開発環境

```bash
docker-compose up --build
```

### 本番環境（予定）

```bash
# 本番ビルド
docker-compose -f docker-compose.prod.yml up --build

# または個別デプロイ
# フロントエンド: Vercel
# バックエンド: AWS/GCP
```

## プロジェクト構造

```
tuukaa/
├── frontend/ # Next.jsフロントエンド
│ ├── src/
│ │ ├── app/ # App Router
│ │ └── lib/ # ユーティリティ
│ ├── public/ # 静的ファイル
│ └── package.json
├── backend/ # FastAPIバックエンド
│ ├── app/
│ │ ├── api/ # APIエンドポイント
│ │ ├── core/ # コアロジック（RAG等）
│ │ └── models/ # データモデル
│ └── pyproject.toml
├── docker-compose.yml # マルチサービス構成
└── README.md # このファイル
```

## 移行ログ（段階移行）

このリポジトリは「最小差分 / アダプタ先行 / ロールバック容易」を前提に段階的に再編しています。

- STEP 1: 雛形の追加（ディレクトリと空ファイル）
  - 追加: `backend/app/domains/{pdf,lp,embed}/`、`backend/app/core/{prompts,vector}/`、`backend/app/common/`
  - 追加: `frontend/src/app/(apps)/{pdf,lp,embed-admin}/`、`frontend/public/embed.js`
  - 既存の import / ルーティングに変更なし
- STEP 2: PDF ドメインの薄いアダプタ追加
  - `domains/pdf/service.py` に既存 `DocumentProcessor` / `RAGEngine` を薄く呼ぶ関数を定義
  - API は未差し替え（振る舞い互換を担保）
- STEP 3: API ルーターの分離 ①（PDF の `/upload` のみ移譲）
  - 追加: `backend/app/api/pdf.py`（`/api/v1/pdf/upload`）
  - 既存エンドポイント `/api/v1/upload` は維持（互換性確保）
- STEP 5: LP / Embed の空ルーター追加
  - 追加: `backend/app/api/{lp.py, embed.py}`（`/api/v1/lp`、`/api/v1/embed`）
  - いずれも 200 を返す疎通確認用の空ルートのみ

各 STEP は 1 コミットに分割しており、`git revert` により個別ロールバック可能です。

### 環境変数（.env.sample 推奨）

以下を参考にリポジトリ直下に `.env` を作成してください（`.env.sample` は将来の配布対象）。

```env
# ===== Backend =====
OPENAI_API_KEY=
DEBUG=true
APP_NAME=tuukaa API
APP_VERSION=0.1.0

# 永続化ディレクトリ（docker-compose と整合）
PERSIST_DIRECTORY=/app/vectorstore
UPLOAD_DIRECTORY=/app/uploads

# 安全な初期化・デバッグ向けフラグ
ALLOW_RESET=true

# ===== Frontend =====
# 既存互換: 既存フロント実装が参照
NEXT_PUBLIC_API_URL=http://localhost:8000

# 新: 今後は本変数を参照（段階移行）
NEXT_PUBLIC_API_BASE=http://localhost:8000

# ===== LP Domain (placeholders) =====
LP_MODEL=
LP_TONE=
LP_MAX_TOKENS=

# ===== Embed Domain (placeholders) =====
EMBED_COLLECTION_PREFIX=
EMBED_ALLOWED_ORIGINS=*
```

### 検証手順（Verify）

コンテナ起動後に以下を実行：

```bash
# 1) ヘルス・システム情報
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/pdf/system/info

# 2) PDF アップロード
curl -s -X POST "http://localhost:8000/api/v1/pdf/upload" \
  -F "file=@./sample.pdf"

# 3) 検索・質問
curl -s -X POST "http://localhost:8000/api/v1/pdf/search" \
  -H "Content-Type: application/json" \
  -d '{"question":"テスト","top_k":1}'
curl -s -X POST "http://localhost:8000/api/v1/pdf/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"このPDFの概要は？","top_k":1}'

# 4) LP/Embed（疎通）
curl -s http://localhost:8000/api/v1/lp/
curl -s http://localhost:8000/api/v1/embed/
```

期待値：すべて 200、LP/Embed は `{ "status": "ok" }`。

### ロールバック手順

各 STEP はコミット単位。`git log --oneline` でメッセージ `STEP X:` を確認し、対象のみ revert します。

```bash
git log --oneline | head -n 10
# 例) STEP 3 を取り消す
git revert <STEP_3_COMMIT_SHA>
```

## トラブルシューティング

### よくある問題

#### フロントエンドが起動しない

```bash
# Node.jsバージョン確認（18以上推奨）
node --version

# 依存関係の再インストール
cd frontend && rm -rf node_modules package-lock.json
npm install
```

#### バックエンド API に接続できない

```bash
# バックエンドサービス状態確認
curl http://localhost:8000/health

# 環境変数確認
echo $OPENAI_API_KEY
```

#### ChromaDB エラー

```bash
# ベクトルストアのリセット
docker-compose down
docker volume rm tuukaa_vectorstore
docker-compose up --build
```

---

**フェーズ 3 の特徴**: フルスタック Web アプリケーションとして、エンドユーザーが使いやすいモダンな UI と、堅牢な API 基盤を両立したシステムです。
