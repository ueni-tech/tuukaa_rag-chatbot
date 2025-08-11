"""
RAGエンジンモジュール
RAGシステムの中核となる
ベクトルストア管理、検索、回答生成機能を提供する
"""

import gc
import shutil
from typing import Any
from datetime import datetime
import uuid

from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

from ..config import settings


class RAGEngine:
    """RAGエンジンクラス
    ベクトルストアの管理、文書検索、回答生成を統合的に行う
    """

    # RAG用プロンプトテンプレート
    RAG_PROMPT_TEMPLATE = """\
あなたは優秀な社内ルールのアシスタントです。
提供されたコンテキスト情報を基に、ユーザーの質問に正確で実用的な回答を提供してください。

**重要な指示:**
- コンテキストに含まれている情報のみを使用してください
- コードの例やベストプラクティスを含めて、実用的な回答を心がけてください
- 回答は日本語で行い、わかりやすく説明してください

**コンテキスト:**
{context}

**質問:**
{question}

**回答:**"""

    def __init__(self):
        self.chroma_settings = ChromaSettings(
            allow_reset=True,
            is_persistent=True,
            persist_directory=str(settings.persist_path),
            anonymized_telemetry=False,
        )

        self.embeddings: OpenAIEmbeddings | None = None
        self.llm: ChatOpenAI | None = None
        self.vectorstore: Chroma | None = None
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        settings.ensure_directories()

    async def initialize(self) -> None:
        """RAGエンジンの初期化
        OpenAIクライアントとLLMを初期化
        非同期で初期化することで、起動時の応答性を向上させる
        """
        try:
            api_key: SecretStr | None = (
                SecretStr(settings.openai_api_key)
                if settings.openai_api_key is not None
                else None
            )

            self.embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=api_key,
            )

            self.llm = ChatOpenAI(
                model=settings.default_model,
                temperature=settings.default_temperature,
                api_key=api_key,
            )

            await self._load_existing_vectorstore()

        except Exception as e:
            raise RuntimeError(f"RAGエンジンの初期化に失敗しました: {str(e)}")

    async def _load_existing_vectorstore(self) -> bool:
        """既存のベクトルストアを読み込み
        Returns:
            読み込みに成功した場合True, 失敗した場合False
        """
        try:
            if settings.persist_path.exists() and self.embeddings:
                self.vectorstore = Chroma(
                    persist_directory=str(settings.persist_path),
                    embedding_function=self.embeddings,
                    client_settings=self.chroma_settings,
                )
                return True
        except Exception:
            pass

        return False

    async def create_vectorstore_from_chunks(
        self, chunks: list[str], filename: str
    ) -> dict[str, Any]:
        """チャンクからベクトルストア作成
        Args:
            chunks: テキストチャンクのリスト
            filename: アップロードされたファイル名
        Returns:
            作成結果の情報
        Raises:
            RuntimeError: ベクトルストアの作成に失敗した場合
        """
        if not self.embeddings:
            raise RuntimeError("RAGエンジンが初期化されていません")

        try:
            if not self.vectorstore:
                await self._load_existing_vectorstore()

            file_id = str(uuid.uuid4())
            upload_time = datetime.now().isoformat()
            metadatas = [
                {
                    "filename": filename,
                    "file_id": file_id,
                    "upload_time": upload_time,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]

            if not self.vectorstore:
                # 新規作成
                self.vectorstore = Chroma.from_texts(
                    texts=chunks,
                    embedding=self.embeddings,
                    metadatas=metadatas,
                    client_settings=self.chroma_settings,
                )
            else:
                # 既存コレクションに追記
                await self._add_chunks_to_existing_vectorstore(chunks, metadatas)

            self.vectorstore.persist()
            current_uuid = str(self.vectorstore._collection.id)
            await self._cleanup_old_directories(current_uuid)

            return {
                "status": "success",
                "chunks_count": len(chunks),
                "collection_id": current_uuid,
                "document_count": self.vectorstore._collection.count(),
                "filename": filename,
            }

        except Exception as e:
            raise RuntimeError(f"ベクトルストアの作成に失敗しました: {str(e)}")

    async def _add_chunks_to_existing_vectorstore(
        self, chunks: list[str], metadatas: list[dict[str, Any]]
    ) -> None:
        """既存のベクトルストアにチャンクを追加"""
        self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)

    # NOTE
    # ↓はベクトルストアの上書き作成用のメソッドのため利用停止
    # async def _cleanup_existing_vectorstore(self) -> None:
    #     """既存のベクトルストア接続をクリーンアップ"""
    #     if self.vectorstore:
    #         try:
    #             self.vectorstore._client.reset()
    #         except Exception:
    #             pass
    #         del self.vectorstore
    #         self.vectorstore = None
    #         gc.collect()

    async def _cleanup_old_directories(self, keep_uuid: str) -> None:
        """古いUUIDディレクトリを削除

        Args:
            keep_uuid: 残しておくUUID
        """
        try:
            persist_dir = settings.persist_path
            if not persist_dir.exists():
                return

            for path in persist_dir.iterdir():
                if path.is_dir() and path.name != keep_uuid:
                    shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    async def search_documents(
        self, query: str, top_k: int | None = None
    ) -> list[Document]:
        """文書検索
        Args:
            query: 検索クエリ
            top_k: 検索結果の上位k件

        Returns:
            検索結果の文書リスト

        Raises:
            RuntimeError: ベクトルストアが初期化されていない場合
        """
        if not self.vectorstore:
            raise RuntimeError("ベクトルストアが初期化されていません")

        k = top_k or settings.default_top_k

        try:
            retriever = self.vectorstore.as_retriever(
                search_type="similarity", search_kwargs={"k": k}
            )
            documents = retriever.invoke(query)
            return documents

        except Exception as e:
            raise RuntimeError(f"文書検索に失敗しました: {str(e)}")

    async def generate_answer(
        self,
        question: str,
        top_k: int | None,
    ) -> dict[str, Any]:
        """RAGによる回答生成
        Args:
            question: 質問
            top_k: 検索結果の上位k件

        Returns:
            回答と関連文書を含む辞書

        Raises:
            RuntimeError: RAGエンジンが初期化されていない場合
        """
        if not self.vectorstore or not self.llm:
            raise RuntimeError("RAGエンジンが初期化されていません")

        try:
            documents = await self.search_documents(question, top_k)

            if not documents:
                return {
                    "answer": "関連する文書が見つかりませんでした。",
                    "documents": [],
                    "context_used": "",
                }

            context = self._format_documents(documents)

            prompt = PromptTemplate.from_template(self.RAG_PROMPT_TEMPLATE)

            rag_chain = (
                {"context": lambda x: context, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )

            answer = rag_chain.invoke(question)

            return {
                "answer": answer,
                "documents": [
                    {"content": doc.page_content, "metadata": doc.metadata}
                    for doc in documents
                ],
                "context_used": context,
            }

        except Exception as e:
            raise RuntimeError(f"回答生成に失敗しました: {str(e)}")

    def _format_documents(self, documets: list[Document]) -> str:
        """文書をフォーマットしてコンテキストとして使用
        Args:
            documents: 文書のリスト

        Returns:
            フォーマットされたコンテキスト
        """
        return "\n\n".join(doc.page_content for doc in documets)

    async def get_system_info(self) -> dict[str, Any]:
        """システム情報を取得

        Returns:
            システム情報の辞書
        """
        info: dict[str, Any] = {
            "status": "initialized" if self.vectorstore else "not_initialized",
            "embedding_model": settings.embedding_model,
            "llm_model": settings.default_model,
            "persist_directory": str(settings.persist_path),
        }

        if self.vectorstore:
            try:
                collection = self.vectorstore._collection
                info.update(
                    {
                        "collection_id": str(collection.id),
                        "document_count": collection.count(),
                        "vectorstore_ready": True,
                    }
                )
            except Exception:
                info["vectorstore_ready"] = False
        else:
            info["vectorstore_ready"] = False

        return info

    async def get_document_list(self) -> dict[str, Any]:
        """アップロード済みドキュメント一覧を取得"""
        try:
            if not self.vectorstore:
                return {"files": [], "total_files": 0, "total_chunks": 0}

            collection = self.vectorstore._collection
            results = collection.get(include=["metadatas"])
            metadatas = results.get("metadatas") or []
            if not metadatas:
                return {"files": [], "total_files": 0, "total_chunks": 0}

            file_info_dict: dict[str, dict[str, Any]] = {}
            for md in metadatas:
                if not md:
                    continue
                fname = md.get("filename", "unknown")
                if fname not in file_info_dict:
                    file_info_dict[fname] = {
                        "filename": fname,
                        "file_id": md.get("file_id", "unknown"),
                        "upload_time": md.get("upload_time", "unknown"),
                        "chunk_count": 0,
                        "file_size": md.get("file_size", 0),
                    }
                file_info_dict[fname]["chunk_count"] += 1

            files_list = list(file_info_dict.values())
            return {
                "files": files_list,
                "total_files": len(files_list),
                "total_chunks": len(metadatas),
            }
        except Exception as e:
            raise RuntimeError(f"ドキュメント一覧の取得に失敗しました: {str(e)}")

    async def delete_document_by_filename(self, filename: str) -> dict[str, Any]:
        """ファイル名でドキュメントを削除"""
        try:
            if not self.vectorstore:
                raise RuntimeError("ベクトルストアが初期化されていません")

            collection = self.vectorstore._collection
            before_count = collection.count()

            results = collection.get(
                where={"filename": filename}, include=["metadatas"]
            )
            ids = results.get("ids") or []
            if not ids:
                raise ValueError(f"ファイル '{filename}'は見つかりませんでした")

            deleted_count = len(ids)
            collection.delete(where={"filename": filename})
            after_count = collection.count()

            remaining_results = collection.get(include=["metadatas"])
            metadatas = remaining_results.get("metadatas") or []
            remaining_files = (
                len({md.get("filename", "unknown") for md in metadatas if md})
                if metadatas
                else 0
            )

            return {
                "status": "success",
                "message": f"ファイル '{filename}'を削除しました",
                "deleted_filename": filename,
                "deleted_chunks": deleted_count,
                "remaining_files": remaining_files,
                "remaining_chunks": after_count,
            }
        except Exception as e:
            raise RuntimeError(f"ドキュメントの削除に失敗しました: {str(e)}")

    async def reset_vectorstore(self) -> dict[str, str]:
        """ベクトルストアをリセット
        Returns:
            リセット結果
        """
        try:
            if self.vectorstore:
                current_uuid = str(self.vectorstore._collection.id)
                self.vectorstore._client.reset()
                await self._cleanup_old_directories(current_uuid)
                self.vectorstore = None

            return {"status": "success", "message": "ベクトルストアをリセットしました"}

        except Exception as e:
            return {"status": "error", "message": f"リセットに失敗しました: {str(e)}"}
