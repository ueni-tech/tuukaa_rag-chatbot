この手順書は、複数クライアント（テナント）向け PoC 運用において、テナント単位で「日次予算超過時にリクエストを拒否」する仕組みを導入するためのものです。初心者でも実装できるよう、段階的に解説します。

---

### ゴール

- テナント毎に、日付（JST）で区切った使用額の上限を設定する
- LLM 呼び出し前の事前チェック（最悪ケース見積もり）で超過を拒否（HTTP 402）
- LLM 呼び出し後の実績計上（概算でも可）で日次使用額を更新
- 可能なら Redis/DB で永続化し、原子的に集計する

---

### 導入ポリシー（過剰設計を避けた最小構成）

- まずは Redis には「テナント別・日次の使用額」だけを保存します。
  - キー: `cost:{YYYY-MM-DD}:{tenant}`（JST）
  - 値: 使用額（円）。精度を気にする場合はミリ円など整数にして保存
  - TTL: 翌日 JST 00:00:00 まで
- 予算上限は当初は .env 設定（`DAILY_BUDGET_JPY` / テナント別は `TENANT_BUDGETS`）で管理します
- EMBED_API_KEYS / ALLOWED_ORIGINS は .env のまま（即時反映ニーズが出たら DB ＋ Redis キャッシュへ移行）
- レート制限（RPM 等）は現状の実装のまま（必要になったら Redis 移行）

この最小構成で「悪用によるコスト暴走防止」の核心を満たしつつ、運用負荷を抑えます。

---

### 前提

- リポジトリ: `tuukaa/`
- 対象ファイル: `backend/app/api/embed_ingest.py`
- 既存のグローバル日次ブレーカ実装をテナント別へ拡張

---

### 手順 A: 最小実装（メモリ内・テナント別化）

1. 用語の確認

- 「テナント」= `x-embed-key` から導出される `tenant` 文字列
- 「日付」= JST の `YYYY-MM-DD`

1. コスト集計用マップをテナント別キーに変更

- 変更前: `_cost: dict[str, float]`（日付のみ）
- 変更後: `_cost: dict[tuple[str, str], float]`（(day, tenant)）

編集箇所（例）:

```diff
- _cost: dict[str, float] = {}
+ _cost: dict[tuple[str, str], float] = {}

```

1. 事前チェック（LLM 呼び出し前）をテナント別に

- 対象関数: `/embed/docs/ask` の `docs_ask`
- ポイント: `used = _cost.get((day, tenant), 0.0)` を用い、`(day, tenant)` をキーに取得

編集例:

```diff
   day = jst.strftime("%Y-%m-%d")
-  used = _cost.get(day, 0.0)
+  used = _cost.get((day, tenant), 0.0)
   pre_tokens = max(1, len((question_req.question or "")) // 4) + _RESP_MAX_TOKENS
   pre_est_cost = pre_tokens * _DEF_PRICE
   if settings.daily_budget_jpy > 0 and used + pre_est_cost > settings.daily_budget_jpy:
-      raise HTTPException(402, "daily budget exceeded")
+      raise HTTPException(402, "本日の予算を超過しました")

```

1. 事後計上（LLM 呼び出し後）をテナント別に

```diff
   day = jst.strftime("%Y-%m-%d")
-  used = _cost.get(day, 0.0)
+  used = _cost.get((day, tenant), 0.0)
   est_cost = tokens * _DEF_PRICE
   if settings.daily_budget_jpy > 0 and used + est_cost > settings.daily_budget_jpy:
-      raise HTTPException(402, "daily budget exceeded")
+      raise HTTPException(402, "本日の予算を超過しました")
-  _cost[day] = used + est_cost
+  _cost[(day, tenant)] = used + est_cost

```

1. 重要な注意

- この実装は「メモリ内」です。プロセス再起動や複数ワーカーでは共有されません
- まずは動作確認用として導入し、その後 手順 B に進んで永続化します

---

### 手順 B: Redis を用いた永続化（最小：コストのみ）

目的: 複数ワーカー/再起動でも正しく「テナント別・日次の使用額」を集計し、原子的に超過チェックできるようにします。

1. 依存の用意

- Redis サーバ（Docker 例）: `docker run -p 6379:6379 redis:7-alpine`
- Python クライアント追加（requirements.txt などに追加）
  - `redis>=5`

補足（依存の入れ方）:

- Poetry を利用してバックエンドをローカル実行する場合（例）

```bash
cd backend
poetry add "redis>=5"

```

- requirements.txt を使ってコンテナビルドする場合（例）

```bash
echo "redis>=5" >> backend/requirements.txt
# 以後、Dockerfile 内の pip install で取り込まれます

```

- どちらの方式でも「Python から Redis に接続するための redis パッケージを依存に含める」ことが目的です。Poetry は必須ではありません（コンテナで完結させるなら requirements.txt だけでも可）。

1. docker-compose と .env の最小変更

```yaml
# docker-compose.yml 抜粋（api と同階層に redis を追加、api に REDIS_URL を注入）
services:
  api:
    environment:
      - PYTHONPATH=/app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20

volumes:
  redis-data:
```

起動手順（Compose のみで両方立ち上げる場合）:

```bash
# リポジトリのルートで
docker compose up -d
# → api と redis が一緒に起動します（depends_on/healthcheck により redis 起動後に api が上がります）

# 状態確認
docker compose ps | cat

# Redis の疎通確認（コンテナ間）
docker compose exec redis redis-cli ping | cat
# ローカルホストから
redis-cli -h 127.0.0.1 -p 6379 ping | cat

```

`.env`（任意・compose に書いた場合は省略可能）

```
REDIS_URL=redis://redis:6379/0

```

1. 設定を追加（`backend/app/core/config.py`）

```python
# 例
redis_url: str | None = "redis://localhost:6379/0"

```

環境変数の与え方（例）:

```bash
# Compose: docker-compose.yml（上記例）に記述 / もしくは .env で注入
# ローカル実行（Poetry の場合）
export REDIS_URL="redis://localhost:6379/0"
poetry run uvicorn app.main:app --reload

```

1. 料金キー設計（最小）

- キー: `cost:{YYYY-MM-DD}:{tenant}`（JST）
- 値: 小数（円）をミリ円など整数化して保存するか、`FLOAT` を使う
- TTL: 翌日 JST 00:00:00 まで（初回アクセス時に設定）

1. 原子的なチェック＆加算（疑似コード）

- Redis の Lua もしくは MULTI/EXEC を利用
  - 事前チェック:
    - `GET key` → `used + pre_est_cost > budget` なら即時拒否（402）
  - 事後記録:
    - `INCRBYFLOAT key est_cost`（初回は `SETNX` で 0 を用意）
    - キーに TTL を設定（未設定時のみ）

1. コード組込ポイント（この手順では「コストのみ」を Redis 管理）

- `docs_ask` の事前チェック部と事後計上部を Redis 経由に差し替え
- エラーメッセージは「本日の予算を超過しました」で統一

1. フォールバック

- Redis 未設定時は手順 A のメモリ内実装を使用

---

### コード改修（具体例：最小構成で Redis を利用）

以下は `backend/app/api/embed_ingest.py` を最小限改修し、テナント別・日次コストを Redis に保存する例です。Redis が使えない場合はメモリ実装にフォールバックします。

1. 追加インポート

```diff
 from fastapi import (
     APIRouter,
     Depends,
     Header,
     HTTPException,
     UploadFile,
     File,
     Form,
     Request,
 )
 from fastapi.responses import StreamingResponse
 from pydantic import BaseModel
+from redis import Redis
+import os

```

1. ヘルパー関数を追加（ファイル上部のユーティリティ群の近くで OK）

```python
# JSTの翌日0時までの残秒数を返す
def _seconds_until_next_jst_midnight(now: dt.datetime | None = None) -> int:
    jst = dt.timezone(dt.timedelta(hours=9))
    now = now or dt.datetime.now(jst)
    next_day = (now + dt.timedelta(days=1)).date()
    next_midnight = dt.datetime.combine(next_day, dt.time(0, 0, 0), tzinfo=jst)
    return max(1, int((next_midnight - now).total_seconds()))

def _get_redis() -> Redis | None:
    url = getattr(settings, "redis_url", None) or os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        client = Redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None

```

1. 事前チェック（LLM 呼び出し前）を Redis 対応に（なければメモリ）

```diff
     # 日次ブレーカ（事前見積り）
     jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
     day = jst.strftime("%Y-%m-%d")
-    used = _cost.get((day, tenant), 0.0)
     pre_tokens = max(1, len((req.question or "")) // 4) + _RESP_MAX_TOKENS
     pre_est_cost = pre_tokens * _DEF_PRICE
-    if settings.daily_budget_jpy > 0 and used + pre_est_cost > settings.daily_budget_jpy:
-        raise HTTPException(402, "本日の予算を超過しました")
 +    rc = _get_redis()
 +    if rc:
 +        key = f"cost:{day}:{tenant}"
 +        used = float(rc.get(key) or 0.0)
 +    else:
 +        used = _cost.get((day, tenant), 0.0)
 +
 +    if settings.daily_budget_jpy > 0 and used + pre_est_cost > settings.daily_budget_jpy:
 +        raise HTTPException(402, "本日の予算を超過しました")

```

1. 事後計上（LLM 呼び出し後）を Redis 対応に（なければメモリ）

```diff
     # コスト（日次ブレーカ）
     answer_text = result.get("answer", "")
     tokens = max(1, len((req.question + "\\\\n" + answer_text)) // 4)
     jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
     day = jst.strftime("%Y-%m-%d")
     est_cost = tokens * _DEF_PRICE
-    used = _cost.get((day, tenant), 0.0)
-    if settings.daily_budget_jpy > 0 and used + est_cost > settings.daily_budget_jpy:
-        raise HTTPException(402, "本日の予算を超過しました")
-    _cost[(day, tenant)] = used + est_cost
 +    rc = _get_redis()
 +    if rc:
 +        key = f"cost:{day}:{tenant}"
 +        used = float(rc.get(key) or 0.0)
 +        if settings.daily_budget_jpy > 0 and used + est_cost > settings.daily_budget_jpy:
 +            raise HTTPException(402, "本日の予算を超過しました")
 +        pipe = rc.pipeline()
 +        pipe.incrbyfloat(key, est_cost)
 +        pipe.ttl(key)
 +        _, ttl = pipe.execute()
 +        if ttl == -1:
 +            rc.expire(key, _seconds_until_next_jst_midnight(jst))
 +    else:
 +        used = _cost.get((day, tenant), 0.0)
 +        if settings.daily_budget_jpy > 0 and used + est_cost > settings.daily_budget_jpy:
 +            raise HTTPException(402, "本日の予算を超過しました")
 +        _cost[(day, tenant)] = used + est_cost

```

補足:

- 原子的な「チェック → 加算」を厳密に行う場合は Lua スクリプトを使用してください（高度なため本書では割愛）。
- `settings.daily_budget_jpy` がテナント別の場合は、テナントごとの上限解決ヘルパーを用意してください。

よくある質問（手順 B に関して）:

- Q: Poetry でインストールする必要はありますか？
  - A: 必須ではありません。ローカルから Poetry でバックエンドを起動するなら `poetry add redis` が必要です。Docker/Compose で完結させるなら、イメージビルド時に `redis>=5` を依存へ追加すれば十分です。
- Q: `docker compose up` で一緒に立ち上がりますか？
  - A: はい。例のように `redis` サービスを追加し、`api` を `depends_on` で紐づければ `docker compose up -d` で同時起動します。

### 手順 C: モデル別単価と出力トークン上限（詳細）

目的: モデルごとの単価で課金見積り・記録を行い、出力トークンの上限をリクエスト単位で制御できるようにします。Redis 側の準備は不要で、見積もり・記録の「単価」と「トークン数」の算出を拡張します。

---

到達点:

- `MODEL_PRICING` 環境変数で「モデル → 円/トークン」を設定可能（未設定は `_DEF_PRICE` を使用）
- `QuestionRequest.max_output_tokens` で出力上限をクライアントが指定可能（未指定は設定既定値）
- 事前チェックは `入力推定 + max_output_tokens` に単価を掛けて見積り
- 事後計上は `(質問+回答)` の概算トークンに単価を掛けて加算

---

1. 設定を追加（`backend/app/core/config.py`）

```diff
 class Settings(BaseSettings):
@@
     rate_limit_rpm: int = 60
     daily_budget_jpy: float = 0.0
@@
     redis_url: str | None = "redis://localhost:6379/0"

+    # ===== 料金・トークン上限（手順C）=====
+    model_pricing: str | None = None  # 例: "gpt-4o-mini:0.002,gpt-4o:0.006"
+    default_max_output_tokens: int = 1024
@@
     def embed_allowed_origins_list(self) -> list[str]:
         raw = os.getenv("ALLOWED_ORIGINS") or (self.embed_allowed_origins or "*")
         items = [o.strip() for o in raw.split(",") if o.strip()]
         return items or ["*"]

+    @property
+    def model_pricing_map(self) -> dict[str, float]:
+        mapping: dict[str, float] = {}
+        raw = (self.model_pricing or "").strip()
+        if not raw:
+            return mapping
+        for pair in raw.split(","):
+            if ":" not in pair:
+                continue
+            name, price = pair.split(":", 1)
+            name, price = name.strip(), price.strip()
+            try:
+                if name:
+                    mapping[name] = float(price)
+            except Exception:
+                continue
+        return mapping
```

環境変数例（`.env` など）:

```
MODEL_PRICING="gpt-4o-mini:0.002,gpt-4o:0.006"
DEFAULT_MAX_OUTPUT_TOKENS=1024
```

---

2. リクエストに出力上限を追加（`backend/app/models/schemas.py`）

```diff
 class QuestionRequest(BaseModel):
@@
     temperature: float | None = Field(
         None, ge=0.0, le=0.5, description="生成温度(0.0～0.5)"
     )
+    max_output_tokens: int | None = Field(
+        None, ge=1, le=4096, description="出力トークンの上限（推定時に使用）"
+    )
```

ポイント:

- `max_output_tokens` は見積り用の上限。実際の生成上限は LLM クライアントの `max_tokens` 等で別途制御してください。
- 未指定時は `_RESP_MAX_TOKENS` または `settings.default_max_output_tokens` を使います。

---

3. 単価と出力上限を用いた見積り・計上に変更（`backend/app/api/embed_ingest.py`）

事前チェック（見積り）:

```diff
     # 日次ブレーカ（事前見積り）
     jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
     day = jst.strftime("%Y-%m-%d")
-    pre_tokens = max(1, len((question_req.question or "")) // 4) + _RESP_MAX_TOKENS
-    pre_est_cost = pre_tokens * _DEF_PRICE
+    selected_model = (question_req.model or settings.default_model or "").strip()
+    price_per_token = settings.model_pricing_map.get(selected_model, _DEF_PRICE)
+    max_out = (
+        question_req.max_output_tokens
+        or getattr(settings, "default_max_output_tokens", _RESP_MAX_TOKENS)
+    )
+    input_est = max(1, len((question_req.question or "")) // 4)
+    pre_tokens = input_est + max_out
+    pre_est_cost = pre_tokens * price_per_token
     rc = _get_redis()
     if rc:
         key = f"cost:{day}:{tenant}"
         used = float(rc.get(key) or 0.0)
     else:
         used = _cost.get((day, tenant), 0.0)
@@
-    if (
-        settings.daily_budget_jpy > 0
-        and used + pre_est_cost > settings.daily_budget_jpy
-    ):
+    if (settings.daily_budget_jpy > 0 and used + pre_est_cost > settings.daily_budget_jpy):
         raise HTTPException(402, "本日の使用上限に達しました")
```

事後計上（記録）:

```diff
     # コスト（日次ブレーカ）
     answer_text = result.get("answer", "")
     tokens = max(1, len((question_req.question + "\n" + answer_text)) // 4)
     jst = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
     day = jst.strftime("%Y-%m-%d")
-    est_cost = tokens * _DEF_PRICE
+    selected_model = (question_req.model or settings.default_model or "").strip()
+    price_per_token = settings.model_pricing_map.get(selected_model, _DEF_PRICE)
+    est_cost = tokens * price_per_token
     # used = _cost.get((day, tenant), 0.0)
     # est_cost = tokens * _DEF_PRICE
     # if settings.daily_budget_jpy > 0 and used + est_cost > settings.daily_budget_jpy:
     #     raise HTTPException(402, "本日の使用上限に達しました")
     # _cost[(day, tenant)] = used + est_cost
```

注意:

- 単価は `question_req.model`（なければ `settings.default_model`）で選択。未登録モデルは `_DEF_PRICE` を使用
- トークン数の推定は簡易式（文字数/4）。必要なら後日トークナイザで置換

---

4. 動作確認（手順 C）

1) 既定値の確認

- `.env` に `MODEL_PRICING` を設定しない場合、 `_DEF_PRICE` が使われます
- `.env` の `DEFAULT_MAX_OUTPUT_TOKENS` 未設定時は `_RESP_MAX_TOKENS` が既定

2. モデル別単価の反映

```bash
curl -sS -X POST \
  -H "x-embed-key: <あなたのキー>" \
  -H "Content-Type: application/json" \
  http://localhost:8000/embed/docs/ask \
  -d '{"question":"価格テスト","model":"gpt-4o-mini","top_k":3}' | jq .
```

- レスポンスの `cost_jpy` が `MODEL_PRICING` の単価に基づき変化すること

3. 出力上限の上書き

```bash
curl -sS -X POST \
  -H "x-embed-key: <あなたのキー>" \
  -H "Content-Type: application/json" \
  http://localhost:8000/embed/docs/ask \
  -d '{"question":"上限テスト","model":"gpt-4o-mini","max_output_tokens":256}' | jq .
```

- 事前見積りが `入力推定 + 256` に基づく値になること（超過時は 402）

---

5. よくあるつまづき

- `MODEL_PRICING` の書式は `model:price` をカンマ区切りで列挙（例: `gpt-4o-mini:0.002,gpt-4o:0.006`）
- 未登録モデル名を指定してもエラーにはなりませんが、 `_DEF_PRICE` が使われます
- `max_output_tokens` は見積り用。実際の生成上限は LLM クライアントの `max_tokens` 等で制御

---

### 動作確認手順

1. 環境変数

- `DAILY_BUDGET_JPY`（全テナント共通の上限）をとりあえず設定
- または後述の「テナント別上限」を設定

1. 正常系（上限未達）

- 同一テナントで `/embed/docs/ask` を数回実行し、200 が返ること

1. 超過系（上限超過）

- 連続実行で上限を超えるようにし、402 とメッセージ「本日の予算を超過しました」が返ること

1. テナント分離

- 異なるテナントキーで実行し、片方が超過してももう片方は利用できること

1. 再起動テスト（Redis 使用時）

- アプリを再起動しても超過状態が維持されること

---

### 任意: テナント別上限の設定

1. 設定例（環境変数）

- `TENANT_BUDGETS="alpha:200,beta:500"`

1. 実装方針

- 取り込んだマップから `(tenant → 日次上限)` を解決
- なければ `settings.daily_budget_jpy` を既定に

---

### 任意: 将来 Redis に移行を検討する項目（後回し推奨）

- レート制限（RPM などのカウンタ）
  - 高トラフィック/スケール時にのみ移行検討
- EMBED_API_KEYS の即時失効/権限制御
  - 当面は .env で十分。運用要件が固まってから DB ＋ Redis キャッシュ化
- ALLOWED_ORIGINS のテナント別動的管理
  - 変更頻度が上がるまでは .env で運用

---

### 運用上のベストプラクティス

- 80%/100% 到達時に通知（Slack/Webhook）
- 構造化ログ（tenant/day/model/tokens/cost）を記録
- ステータス API（当日の残額、リセット時刻）を用意
- 同時アクセスの負荷試験（競合時も誤差が出ないか）

---

### 付録：よくある質問

- Q: なぜ事前と事後の二段構え？
  - A: 事前は「未然防止」、事後は「実績記録」。両方必要です。
- Q: メモリ実装のままで十分？
  - A: 単一プロセスの検証には有効ですが、本番や複数ワーカーでは Redis/DB を推奨します。
