"""
PDFドメインサービス

STEP 2: 既存の実装（`app.core.document_processor`, `app.core.rag_engine`）への
薄いアダプタのみを提供。既存ルーターはこの段階では差し替えない。
"""

from pathlib import Path
from typing import Any, Dict, List

from ...core.services.document_processor import DocumentProcessor
from ...core.services.rag_engine import RAGEngine


document_processor = DocumentProcessor()


async def ingest_pdf_to_vectorstore(
    pdf_path: Path,
    rag_engine: RAGEngine,
    filename: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> Dict[str, Any]:
    """PDF を読み取り、チャンク化してベクトルストアを構築する薄いラッパ。

    既存の `DocumentProcessor` と `RAGEngine.create_vectorstore_from_chunks` を利用。
    振る舞いは既存エンドポイントと同等。
    """
    text = await document_processor.extract_text_form_pdf(pdf_path)
    chunks = document_processor.split_text(text, chunk_size, chunk_overlap)
    vectorstore_info = await rag_engine.create_vectorstore_from_chunks(chunks, filename)
    return {
        "text_length": len(text),
        "chunk_count": len(chunks),
        "vectorstore_info": vectorstore_info,
        "estimated_tokens": document_processor.count_tokens(text),
    }


async def ask_question(
    question: str,
    top_k: int | None,
    model: str | None,
    temperature: float | None,
    rag_engine: RAGEngine,
) -> Dict[str, Any]:
    """質問に対して回答を生成する薄いラッパ。"""
    result = await rag_engine.generate_answer(
        question=question, top_k=top_k, model=model, temperature=temperature
    )
    return result


async def search_documents(
    query: str, top_k: int | None, rag_engine: RAGEngine
) -> List[Any]:
    """関連文書のみ検索する薄いラッパ。"""
    documents = await rag_engine.search_documents(query=query, top_k=top_k)
    return documents


async def get_system_info(rag_engine: RAGEngine) -> Dict[str, Any]:
    """システム情報取得の薄いラッパ。"""
    return await rag_engine.get_system_info()


async def reset_system(rag_engine: RAGEngine) -> Dict[str, str]:
    """ベクトルストアのリセットの薄いラッパ。"""
    return await rag_engine.reset_vectorstore()
