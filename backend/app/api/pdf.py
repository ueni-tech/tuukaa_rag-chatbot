"""
PDF API ルーター（分離①）

STEP 3: まずは /upload のみ新ルーターへ移譲し、動作確認後に段階移譲。
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..core.web.dependencies import get_rag_engine
from ..core.services.rag_engine import RAGEngine
from ..models.schemas import SystemInfoResponse
from ..domains.pdf.schemas import (
    UploadResponse,
    QuestionRequest,
    AnswerResponse,
    SearchResponse,
    DocumentInfo,
    DocumentListResponse,
    DeleteDocumentRequest,
    DeleteDocumentResponse,
)
from ..core.services.document_processor import DocumentProcessor
from ..domains.pdf.service import (
    ingest_pdf_to_vectorstore,
    ask_question as service_ask_question,
    search_documents as service_search_documents,
    get_system_info as service_get_system_info,
    reset_system as service_reset_system,
)
from ..core.web.rate_limit import rate_limited


router = APIRouter(prefix="/pdf", tags=["PDF"])
logger = logging.getLogger(__name__)

document_processor = DocumentProcessor()


@router.post("/upload", response_model=UploadResponse)
@rate_limited("pdf:upload")
async def upload_document(
    file: UploadFile = File(...),
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="PDFファイルのみアップロード可能です"
        )

    max_size = 10 * 1024 * 1024
    temp_file_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(
                    status_code=413, detail="ファイルサイズが10MBを超えています"
                )
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        ingest_info = await ingest_pdf_to_vectorstore(
            temp_file_path, rag_engine, file.filename
        )

        file_info = {
            "filename": file.filename,
            "file_size": len(content),
            "text_length": ingest_info["text_length"],
            "chunk_count": ingest_info["chunk_count"],
            "estimated_tokens": ingest_info["estimated_tokens"],
        }

        return UploadResponse(
            status="success",
            message=f"ファイル '{file.filename}'の処理が完了しました",
            file_info=file_info,
            vectorstore_info=ingest_info["vectorstore_info"],
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
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
        except Exception:
            pass


@router.post("/ask", response_model=AnswerResponse)
@rate_limited("pdf:ask")
async def ask_question(
    request: QuestionRequest, rag_engine: RAGEngine = Depends(get_rag_engine)
) -> AnswerResponse:
    system_info = await service_get_system_info(rag_engine)
    if not system_info.get("vectorstore_ready"):
        raise HTTPException(
            status_code=400, detail="まずPDFファイルをアップロードしてください"
        )

    result = await service_ask_question(
        question=request.question, top_k=request.top_k, rag_engine=rag_engine
    )
    return AnswerResponse(
        answer=result["answer"],
        question=request.question,
        documents=result["documents"],
        context_used=result["context_used"],
    )


@router.post("/search", response_model=SearchResponse)
@rate_limited("pdf:search")
async def search_documents(
    request: QuestionRequest, rag_engine: RAGEngine = Depends(get_rag_engine)
) -> SearchResponse:
    system_info = await service_get_system_info(rag_engine)
    if not system_info.get("vectorstore_ready"):
        raise HTTPException(
            status_code=400, detail="まずPDFファイルをアップロードしてください"
        )

    documents = await service_search_documents(
        query=request.question, top_k=request.top_k, rag_engine=rag_engine
    )
    document_list = [
        DocumentInfo(content=doc.page_content, metadata=doc.metadata)
        for doc in documents
    ]
    return SearchResponse(
        documents=document_list, query=request.question, total_found=len(documents)
    )


@router.get("/documents", response_model=DocumentListResponse)
@rate_limited("pdf:documents:list")
async def get_document_list(
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> DocumentListResponse:
    try:
        logger.info("ドキュメント一覧取得開始")
        result = await rag_engine.get_document_list()
        logger.info(f"ドキュメント一覧取得完了: {result['total_files']}ファイル")
        return DocumentListResponse(
            files=result["files"],
            total_files=result["total_files"],
            total_chunks=result["total_chunks"],
        )
    except Exception as e:
        logger.error(f"ドキュメント一覧取得エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"ドキュメント一覧の取得に失敗しました: {str(e)}"
        )


@router.delete("/documents", response_model=DeleteDocumentResponse)
@rate_limited("pdf:documents:delete")
async def delete_document(
    request: DeleteDocumentRequest, rag_engine: RAGEngine = Depends(get_rag_engine)
) -> DeleteDocumentResponse:
    try:
        logger.info(f"ドキュメント削除開始: {request.filename}")
        result = await rag_engine.delete_document_by_filename(request.filename)
        logger.info(f"ドキュメント削除完了: {request.filename}")
        return DeleteDocumentResponse(
            status=result["status"],
            message=result["message"],
            deleted_filename=result["deleted_filename"],
            remaining_files=result["remaining_files"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"ドキュメント削除エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"ドキュメントの削除に失敗しました: {str(e)}"
        )


@router.get("/system/info", response_model=SystemInfoResponse)
@rate_limited("pdf:system:info")
async def get_system_info(
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> SystemInfoResponse:
    info = await service_get_system_info(rag_engine)
    return SystemInfoResponse(
        status=info["status"],
        embedding_model=info["embedding_model"],
        llm_model=info["llm_model"],
        vectorstore_ready=info["vectorstore_ready"],
        document_count=info.get("document_count"),
        collection_id=info.get("collection_id"),
    )


@router.post("/system/reset")
@rate_limited("pdf:system:reset")
async def reset_system(
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> dict[str, str]:
    return await service_reset_system(rag_engine)
