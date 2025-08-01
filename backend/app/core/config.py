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

    app_name: str = "LPナレッジ検索API"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    openai_api_key: str

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


settings = Settings()
