"""
PDF API ルーター（分離①）

STEP 3: まずは /upload のみ新ルーターへ移譲し、動作確認後に段階移譲。
"""

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..core.dependencies import get_rag_engine
from ..core.rag_engine import RAGEngine
from ..models.schemas import UploadResponse
from ..core.document_processor import DocumentProcessor
from ..domains.pdf.service import ingest_pdf_to_vectorstore


router = APIRouter(prefix="/pdf", tags=["PDF"])
logger = logging.getLogger(__name__)

document_processor = DocumentProcessor()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルのみアップロード可能です")

    max_size = 10 * 1024 * 1024
    temp_file_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(status_code=413, detail="ファイルサイズが10MBを超えています")
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        ingest_info = await ingest_pdf_to_vectorstore(temp_file_path, rag_engine)

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
        raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")
    finally:
        try:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
        except Exception:
            pass


