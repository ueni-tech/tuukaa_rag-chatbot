"""
共通スキーマ（基盤）

段階移行のため、まずは Error/Meta の最小骨格のみを提供。
既存 `app.models.schemas` はそのまま使用継続（互換維持）。
"""

from pydantic import BaseModel, Field


class ErrorMeta(BaseModel):
    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="短い説明")


class CostMeta(BaseModel):
    model: str = Field(...)
    input_tokens: int = Field(...)
    output_tokens: int = Field(...)
    input_cost_jpy: float = Field(...)
    output_cost_jpy: float = Field(...)
    total_cost_jpy: float = Field(...)
