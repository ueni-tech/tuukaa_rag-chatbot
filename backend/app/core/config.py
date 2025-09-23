"""
設定管理モジュール
アプリケーションの設定を一元管理する
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    pydantic_settingsを使用することで、環境変数から自動的に設定を読み込み、
    型チェックとバリデーションを行う
    """

    app_name: str = "tuukaa API"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    openai_api_key: str | None = None

    # ベクトルストア設定
    persist_directory: str = "./vectorstore"
    embedding_model: str = "text-embedding-3-small"

    # LLM設定
    default_model: str = "gpt-4o-mini"
    default_temperature: float = 0.2
    default_top_k: int = 2
    max_chunk_size: int = 2000
    chunk_overlap: int = 200

    # ファイルアップロード設定
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list[str] = ["pdf"]
    upload_directory: str = "./uploads"

    # ===== Embed Domain =====
    embed_collection_prefix: str | None = None
    embed_allowed_origins: str | None = None
    embed_api_keys: str | None = None
    rate_limit_rpm: int = 60
    daily_budget_jpy: float = 100.0
    # 管理者用シークレット
    admin_api_secret: str | None = None

    # ==== Redis設定 ====
    redis_url: str | None = "redis://localhost:6379/0"

    # === 料金・トークン上限 ===
    model_pricing: str | None = None  # 例: "gpt-4o-mini:0.002,gpt-4o:0.006"
    default_max_output_tokens: int = 768
    # USD→JPY 為替レート（MODEL_PRICING を USD/token として受け取る想定）
    usd_jpy_rate: float = 148.117

    # === 入力側のトークン予算（プロンプトと質問・コンテキストの合計に関する上限） ===
    # モデルのコンテキストウィンドウ（既定値）。必要に応じて .env で上書き。
    default_context_window_tokens: int = 8192
    # システム/指示/テンプレート固定分として見込むオーバーヘッド
    prompt_overhead_tokens: int = 512

    class ConfigDict:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def persist_path(self) -> Path:
        """ベクトルストアの永続化パスを取得"""
        return Path(self.persist_directory)

    @property
    def upload_path(self) -> Path:
        """アップロードディレクトリのパスを取得"""
        return Path(self.upload_directory)

    def ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.upload_path.mkdir(parents=True, exist_ok=True)

    @property
    def embed_api_keys_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        raw = (self.embed_api_keys or "").strip()
        if not raw:
            return mapping
        for pair in raw.split(","):
            if ":" not in pair:
                continue
            client, key = pair.split(":", 1)
            client, key = client.strip(), key.strip()
            if client and key:
                mapping[client] = key
        return mapping

    @property
    def embed_allowed_origins_list(self) -> list[str]:
        raw = os.getenv("EMBED_ALLOWED_ORIGINS") or (
            self.embed_allowed_origins or ""
        )
        items = [o.strip() for o in raw.split(",") if o.strip()]
        if self.debug:
            return items or ["*"]
        # production: wildcard and empty are not allowed
        if not items:
            raise ValueError("EMBED_ALLOWED_ORIGINS must be set in production")
        if "*" in items:
            raise ValueError("Wildcard '*' is not allowed in production")
        return items

    @property
    def model_pricing_inout_map(self) -> dict[str, tuple[float, float]]:
        """
        モデルごとの (入力USD/token, 出力USD/token) を返す。
        - 旧式の単一数値は in/out 同一単価として解釈
        - 拡張 "in=...:out=..." は 1M tokens あたりの USD を受け取り、USD/token に変換
        - 片側だけ指定された場合、指定のない側は同一値を補完（実務上の保守的見積り）
        """
        mapping: dict[str, tuple[float, float]] = {}
        raw = (self.model_pricing or "").strip()
        if not raw:
            return mapping
        for pair in raw.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            name, spec = pair.split(":", 1)
            name, spec = name.strip(), spec.strip()

            def _parse_inout(s: str) -> tuple[float, float] | None:
                s = (s or "").strip()
                if not s:
                    return None
                if ("in=" in s) or ("out=" in s):
                    in_val: float | None = None
                    out_val: float | None = None
                    for part in s.split(":"):
                        part = part.strip()
                        if part.startswith("in="):
                            try:
                                in_val = float(part.split("=", 1)[1].strip())
                            except Exception:
                                pass
                        elif part.startswith("out="):
                            try:
                                out_val = float(part.split("=", 1)[1].strip())
                            except Exception:
                                pass
                    # 1M 単価(USD) -> USD/token
                    if in_val is None and out_val is None:
                        return None
                    if in_val is None:
                        in_val = out_val
                    if out_val is None:
                        out_val = in_val
                    return (in_val / 1_000_000.0, out_val / 1_000_000.0)
                # 単一数値を USD/token と解釈（in/out 同一）
                if "=" in s:
                    s = s.split("=", 1)[-1].strip()
                try:
                    v = float(s)
                    return (v, v)
                except Exception:
                    return None

            vals = _parse_inout(spec)
            if name and vals is not None:
                mapping[name] = vals
        return mapping


settings = Settings()
