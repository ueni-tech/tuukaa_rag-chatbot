"""
APIエンドポイントの実装
各種API機能をエンドポイントとして公開する
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..core.document_processor import DocumentProcessor
from ..core.rag_engine import RAGEngine
from ..core.dependencies import (
    get_rag_engine,
)
from ..models.schemas import (
    AnswerResponse,
    ErrorResponse,
    QuestionRequest,
    SearchResponse,
    SystemInfoResponse,
    UploadResponse,
    DocumentInfo,
)


logger = logging.getLogger(__name__)

router = APIRouter()

document_processor = DocumentProcessor()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    # NOTE
    # File(...) はファイルアップロード用のパラメータ宣言ヘルパー
    file: UploadFile = File(...),
    # NOTE
    # Depends(get_rag_engine) と書くと、FastAPI がリクエストごとに get_rag_engine() を呼び出し、
    # 新しい RAGEngine を生成・提供する
    rag_engin: RAGEngine = Depends(get_rag_engine),
) -> UploadResponse:
    """PDF文書のアップロードとベクトルストア構築
    Args:
        file: アップロードされたPDFファイル。UploadFile型の fileパラメータを必須指定。
        rag_engine: RAGエンジンインスタンス

    Returns:
        アップロード結果

    Raises:
        HTTPException: ファイル処理エラーの場合
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="PDFファイルのみアップロード可能です"
        )

    max_size = 10 * 1024 * 1024  # 10MB

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()

            if len(content) > max_size:
                raise HTTPException(
                    status_code=413, detail="ファイルサイズが10MBを超えています"
                )

            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        # PDFの処理
        logger.info(f"PDF処理開始: {file.filename}")
        text = await document_processor.extract_text_form_pdf(temp_file_path)

        if not text.strip():
            raise HTTPException(
                status_code=400, detail="PDFからテキストを抽出できませんでした"
            )

        chunks = document_processor.split_text(text)

        if not chunks:
            raise HTTPException(
                status_code=400, detail="テキストをチャンクに分割できませんでした"
            )

        # ベクトルストアを構築
        logger.info(f"ベクトルストア構築開始: {len(chunks)}チャンク")
        vectorstore_info = await rag_engin.create_vectorstore_from_chunks(chunks)

        token_count = document_processor.count_tokens(text)

        file_info = {
            "filename": file.filename,
            "file_size": len(content),
            "text_length": len(text),
            "chunk_count": len(chunks),
            "estimated_tokens": token_count,
        }

        logger.info(f"PDF処理完了: {file.filename}")

        return UploadResponse(
            status="success",
            message=f"ファイル '{file.filename}'の処理が完了しました",
            file_info=file_info,
            vectorstore_info=vectorstore_info,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF処理エラー: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}"
        )
    finally:
        try:
            if "temp_file_path" in locals():
                temp_file_path.unlink()
        except Exception:
            pass


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest, rag_engine: RAGEngine = Depends(get_rag_engine)
) -> AnswerResponse:
    """質問に対する回答を生成
    Args:
        request: 質問リクエスト
        rag_engine: RAGエンジンインスタンス

    Returns:
        生成された回答

    Raises:
        HTTPException: 処理エラーの場合
    """
    try:
        system_info = await rag_engine.get_system_info()
        if not system_info.get("vectorstore_ready"):
            raise HTTPException(
                status_code=400, detail="まずPDFファイルをアップロードしてください"
            )

        logger.info(f"質問処理開始: {request.question[:50]}...")

        result = await rag_engine.generate_answer(
            question=request.question, top_k=request.top_k
        )

        logger.info("質問処理完了")

        return AnswerResponse(
            answer=result["answer"],
            question=request.question,
            documents=result["documents"],
            context_used=result["context_used"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"質問処理エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"回答生成中にエラーが発生しました: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: QuestionRequest, rag_engine: RAGEngine = Depends(get_rag_engine)
) -> SearchResponse:
    """関連文書の検索（回答生成なし）
    Args:
        request: 検索リクエスト
        rag_engine: RAGエンジンインスタンス

    Returns:
        検索結果

    Raises:
        HTTPException: 処理エラーの場合
    """
    try:
        system_info = await rag_engine.get_system_info()
        if not system_info.get("vectorstore_ready"):
            raise HTTPException(
                status_code=400, detail="まずPDFファイルをアップロードしてください"
            )

        logger.info(f"文書検索開始: {request.question[:50]}...")

        documents = await rag_engine.search_documents(
            query=request.question, top_k=request.top_k
        )

        document_list = [
            DocumentInfo(content=doc.page_content, metadata=doc.metadata)
            for doc in documents
        ]

        logger.info(f"文書検索完了: {len(documents)}件")

        return SearchResponse(
            documents=document_list, query=request.question, total_found=len(documents)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文書検索エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"文書検索中にエラーが発生しました: {str(e)}"
        )


@router.get("/system/info", response_model=SystemInfoResponse)
async def get_system_info(
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> SystemInfoResponse:
    """システム情報を取得

    Args:
        rag_engine: RAGエンジンインスタンス

    Returns:
        システム情報
    """
    try:
        info = await rag_engine.get_system_info()

        return SystemInfoResponse(
            status=info["status"],
            embedding_model=info["embedding_model"],
            llm_model=info["llm_model"],
            vectorstore_ready=info["vectorstore_ready"],
            document_count=info.get("document_count"),
            collection_id=info.get("collection_id"),
        )

    except Exception as e:
        logger.error(f"システム情報取得エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"システム情報の取得に失敗しました: {str(e)}"
        )


@router.post("/system/reset")
async def reset_system(
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> dict[str, str]:
    """ベクトルストアをリセット

    Args:
        rag_engine: RAGエンジンインスタンス

    Returns:
        リセット結果
    """
    try:
        logger.info("システムリセット開始")
        result = await rag_engine.reset_vectorstore()
        logger.info("システムリセット完了")

        return result

    except Exception as e:
        logger.error(f"システムリセットエラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"システムリセットに失敗しました: {str(e)}"
        )
