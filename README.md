
## クイックスタート

### 1. 環境設定
```bash
# プロジェクトのクローン
git clone <repository-url>
cd tuukaa

# 環境変数の設定
cat > .env << EOF
OPENAI_API_KEY=your_actual_api_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=LPナレッジ検索
EOF
```

### 2. サービス起動（Docker Compose）
```bash
# フルスタックアプリケーションを一括起動
docker-compose up --build

# バックグラウンド起動の場合
docker-compose up -d --build
```

### 3. 動作確認
- **メインアプリ**: http://localhost:3000（Next.jsフロントエンド）
- **API文書**: http://localhost:8000/docs（FastAPI Swagger）
- **ヘルスチェック**: http://localhost:8000/health（バックエンド状態）

## 使用方法（各フェーズの比較）

### フェーズ1（Streamlit UI）
```bash
# ブラウザでシンプルなUI操作
# http://localhost:8501
```

### フェーズ2（REST API）
```bash
# curlコマンドによるAPI操作
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@document.pdf"

curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "命名規則は？"}'
```

### フェーズ3（Webアプリケーション）
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
- **ベクトルDB**: ChromaDB 1.0.12
- **開発環境**: Poetry + Black + isort

### インフラ・DevOps
- **コンテナ**: Docker + Docker Compose
- **リバースプロキシ**: 将来的にNginx対応予定
- **環境管理**: .env + pydantic-settings

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

### Docker開発環境

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
- **フロントエンド**: ファイル保存で自動リロード（Next.js開発サーバー）
- **バックエンド**: ファイル保存で自動再起動（uvicorn --reload）

## 継承機能（フェーズ1・2から）

### 完全継承される機能
- ✅ PDF文書処理（PyPDF2）
- ✅ RAG処理（LangChain + OpenAI）
- ✅ ベクトルストア（ChromaDB永続化）
- ✅ REST API（全エンドポイント）
- ✅ Docker環境（マルチコンテナ対応）

### 新機能（フェーズ3で追加）
- 🆕 モダンWebUI（Next.js + TypeScript）
- 🆕 レスポンシブデザイン（モバイル対応）
- 🆕 リアルタイムUI更新
- 🆕 型安全なフロントエンド開発
- 🆕 本格的なWebアプリケーション体験

## API仕様（フェーズ2互換）

フェーズ2のREST APIは完全に互換性を保持：

### エンドポイント一覧
- `POST /api/v1/upload` - PDF文書アップロード
- `POST /api/v1/ask` - 質問・回答生成
- `POST /api/v1/search` - 文書検索のみ
- `GET /api/v1/system/info` - システム情報取得
- `GET /health` - ヘルスチェック

### 利用例
```javascript
// フロントエンドからのAPI呼び出し例
const response = await fetch('/api/v1/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'クラスの命名規則は？',
    top_k: 3
  })
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

#### バックエンドAPIに接続できない
```bash
# バックエンドサービス状態確認
curl http://localhost:8000/health

# 環境変数確認
echo $OPENAI_API_KEY
```

#### ChromaDBエラー
```bash
# ベクトルストアのリセット
docker-compose down
docker volume rm tuukaa_vectorstore
docker-compose up --build
```

---

**フェーズ3の特徴**: フルスタックWebアプリケーションとして、エンドユーザーが使いやすいモダンなUIと、堅牢なAPI基盤を両立したシステムです。