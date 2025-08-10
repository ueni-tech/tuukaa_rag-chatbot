"""
依存性注入のためのヘルパー関数
"""

from ..services.rag_engine import RAGEngine

# グローバルRAGエンジンインスタンス
_rag_engine: RAGEngine = RAGEngine()


async def initialize_rag_engine():
    """RAGエンジンを初期化"""
    await _rag_engine.initialize()


def get_rag_engine() -> RAGEngine:
    """RAGエンジンインスタンスを取得
    この関数は依存性注入のために使用されます
    """
    return _rag_engine


async def get_rag_system_info():
    """RAGエンジンのシステム情報を取得"""
    return await _rag_engine.get_system_info()
