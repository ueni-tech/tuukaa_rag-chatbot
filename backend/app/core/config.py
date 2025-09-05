"""
設定管理モジュール
アプリケーションの設定を一元管理する
"""

import os
from pathlib import Path
from typing import Optional
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
    default_temperature: float = 0.0
    default_top_k: int = 3
    max_chunk_size: int = 2000
    chunk_overlap: int = 200

    # ファイルアップロード設定
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list[str] = ["pdf"]
    upload_directory: str = "./uploads"

    # ===== LP Domain =====
    lp_model: str | None = None
    lp_tone: str | None = None
    lp_max_tokens: Optional[int] = None

    # ===== Embed Domain =====
    embed_collection_prefix: str | None = None
    embed_allowed_origins: str | None = "*"
    embed_api_keys: str | None = None
    rate_limit_rpm: int = 60
    daily_budget_jpy: float = 50.0

    # ==== Redis設定 ====
    redis_url: str | None = "redis://localhost:6379/0"

    # === 料金・トークン上限 ===
    model_pricing: str | None = None  # 例: "gpt-4o-mini:0.002,gpt-4o:0.006"
    default_max_output_tokens: int = 1024
    # USD→JPY 為替レート（MODEL_PRICING を USD/token として受け取る想定）
    usd_jpy_rate: float = 148.117

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
        raw = os.getenv("ALLOWED_ORIGINS") or (self.embed_allowed_origins or "*")
        items = [o.strip() for o in raw.split(",") if o.strip()]
        return items or ["*"]

    @property
    def model_pricing_map(self) -> dict[str, float]:
        mapping: dict[str, float] = {}
        raw = (self.model_pricing or "").strip()
        if not raw:
            return mapping
        for pair in raw.split(","):
            if ":" not in pair:
                continue
            name, price = pair.split(":", 1)
            name, price = name.strip(), price.strip()
            # 価格が "=0.00001" や "in=0.00001" のような表記でも最後の '=' 以降を採用
            if "=" in price:
                price = price.split("=")[-1].strip()
            try:
                if name:
                    mapping[name] = float(price)
            except Exception:
                continue
        return mapping


settings = Settings()
