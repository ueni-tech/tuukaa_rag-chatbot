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
import tiktoken


class RAGEngine:
    """RAGエンジンクラス
    ベクトルストアの管理、文書検索、回答生成を統合的に行う
    """

    # RAG用プロンプトテンプレート（GFM厳密・冗長抑制）
    RAG_PROMPT_TEMPLATE = """\
あなたは頼れる情報アシスタントです。アップロードされた資料の内容に基づいて、分かりやすく親しみやすい日本語で回答してください。
すばやく回答してください。

重要な回答ルール:
1. **アップロードされた資料に関係のない質問には答えません**
   - 資料に含まれていない情報について聞かれた場合は、「申し訳ございませんが、そのご質問には回答できません。」と回答してください
   - 一般的な知識や資料と無関係な質問には対応しません

2. **挨拶への対応**
   - 「こんにちは」「おはよう」「お疲れ様」などの挨拶と判断できる質問には、簡潔で親しみやすい挨拶を返してください

3. **資料に基づく回答**
   - 提供されたコンテキストに含まれる情報のみを使用して回答します
   - 推測や想像ではなく、資料に明記されている内容を基に回答します

出力フォーマット（GitHub Flavored Markdown/GFM）:
- 回答全体を三連バッククォートで囲まず、先頭に「markdown」も不要です
- 見出しは #, ##, ### を使って整理しましょう
- 要点は箇条書き（- または *）や番号付き（1.）でまとめます
- コード例が必要な場合は ```言語名 で囲んで、実用的な例をご紹介します
- 表が役立つ場合はGFMテーブルで整理します
- 結論→根拠→具体例の順で、お話しするような感じで回答します

【コンテキスト】
{context}

【質問】
{question}

【回答】"""

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
        self._llm_cache: dict[tuple[str, float, int], ChatOpenAI] = {}

    def _get_llm(
        self, model: str | None, temperature: float | None, max_tokens: int | None = None
    ) -> tuple[ChatOpenAI, str]:
        """(model, temperature)ごとにLLMをキャッシュして取得"""
        used_model = model or settings.default_model
        used_temp = (
            temperature if temperature is not None else settings.default_temperature
        )
        used_max = int(max_tokens) if max_tokens is not None else int(
            settings.default_max_output_tokens)
        key = (used_model, used_temp, used_max)
        if key not in self._llm_cache:
            api_key = (
                SecretStr(settings.openai_api_key)
                if settings.openai_api_key is not None
                else None
            )
            self._llm_cache[key] = ChatOpenAI(
                model=used_model, temperature=used_temp, api_key=api_key, timeout=60,
                max_tokens=used_max,
            )
        return self._llm_cache[key], used_model

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
                max_tokens=settings.default_max_output_tokens,
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
        self,
        chunks: list[str],
        filename: str,
        tenant: str | None = None,
        source_type: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """チャンクからベクトルストア作成
        Args:
            chunks: テキストチャンクのリスト
            filename: アップロードされたファイル名
            tenant: クライアントの識別子
            source_type: ファイルの種類
            source: ファイルへのパス
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
            metadatas = []
            for i in range(len(chunks)):
                md = {
                    "filename": filename,
                    "file_id": file_id,
                    "upload_time": upload_time,
                    "chunk_index": i,
                }
                if tenant is not None:
                    md["tenant"] = tenant
                if source_type is not None:
                    md["source_type"] = source_type
                if source is not None:
                    md["source"] = source
                metadatas.append(md)

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
        self, query: str, top_k: int | None = None, tenant: str | None = None
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
            kwargs: dict[str, Any] = {"k": k}
            if tenant is not None:
                kwargs["filter"] = {"tenant": tenant}
            retriever = self.vectorstore.as_retriever(
                search_type="similarity", search_kwargs=kwargs
            )
            documents = await retriever.ainvoke(query)
            return documents

        except Exception as e:
            raise RuntimeError(f"文書検索に失敗しました: {str(e)}")

    async def generate_answer(
        self,
        question: str,
        top_k: int | None,
        model: str | None = None,
        temperature: float | None = None,
        tenant: str | None = None,
        max_output_tokens: int | None = None,
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
            # まず、テナントにドキュメントが存在するかチェック
            doc_list = await self.get_document_list(tenant=tenant)
            if doc_list["total_chunks"] == 0:
                return {
                    "answer": (
                        "まずはドキュメントをアップロードしてください。"
                        "質問にお答えするためには、関連する資料を"
                        "アップロードしていただく必要があります。"
                    ),
                    "documents": [],
                    "context_used": "",
                    "llm_model": getattr(
                        self.llm, "model", settings.default_model
                    ),
                }

            documents = await self.search_documents(
                question, top_k, tenant=tenant
            )

            if not documents:
                return {
                    "answer": "関連する文書が見つかりませんでした。",
                    "documents": [],
                    "context_used": "",
                    "llm_model": getattr(
                        self.llm, "model", settings.default_model
                    ),
                }

            # トークンベース詰め込み（質問・プロンプト・出力上限を考慮した残り枠に収める）
            model_for_encoding = model or getattr(
                self.llm, "model", settings.default_model)
            try:
                enc = tiktoken.encoding_for_model(model_for_encoding)
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")

            context_window = getattr(
                settings, "default_context_window_tokens", 8192)
            prompt_overhead = getattr(settings, "prompt_overhead_tokens", 512)

            question_tokens = len(enc.encode(question or ""))
            fixed_prompt_tokens = prompt_overhead

            used_max_out = int(max_output_tokens) if max_output_tokens is not None else int(
                settings.default_max_output_tokens)

            remaining_input_budget = max(
                0, context_window - fixed_prompt_tokens - question_tokens - used_max_out)

            selected_parts: list[str] = []
            used_tokens = 0
            for doc in documents:
                part = doc.page_content or ""
                part_tokens = len(enc.encode(part))
                if used_tokens + part_tokens <= remaining_input_budget:
                    selected_parts.append(part)
                    used_tokens += part_tokens
                else:
                    remaining = remaining_input_budget - used_tokens
                    if remaining > 0:
                        try:
                            ids = enc.encode(part)
                            clipped = enc.decode(ids[:remaining])
                        except Exception:
                            avg_chars_per_token = 4
                            clipped = part[: max(
                                0, remaining * avg_chars_per_token)]
                        if clipped:
                            selected_parts.append(clipped)
                            used_tokens = remaining_input_budget
                    break

            context = "\n\n".join(selected_parts)

            if model is not None or temperature is not None or max_output_tokens is not None:
                llm, used_model = self._get_llm(
                    model, temperature, max_output_tokens)
            else:
                llm = self.llm
                used_model = getattr(
                    llm,
                    "model",
                    getattr(llm, "model_name", settings.default_model),
                )

            prompt = PromptTemplate.from_template(self.RAG_PROMPT_TEMPLATE)

            rag_chain = (
                {"context": lambda x: context, "question": RunnablePassthrough()}
                | prompt
                | llm
            )

            msg = await rag_chain.ainvoke(question)
            answer = getattr(msg, "content", str(msg))

            # APIレスポンス由来のモデル名を優先（無ければused_model）
            resp_meta = getattr(msg, "response_metadata", {}) or {}
            resp_model = (
                resp_meta.get("model_name")
                or resp_meta.get("model")
                or getattr(msg, "model", None)
            )
            actual_model = resp_model or used_model

            return {
                "answer": answer,
                "documents": [
                    {"content": doc.page_content, "metadata": doc.metadata}
                    for doc in documents
                ],
                "context_used": context,
                "llm_model": actual_model,
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
            "persist_directory": str(settings.persist_path),
        }

        if self.vectorstore:
            try:
                collection = self.vectorstore._collection
                info.update(
                    {
                        "collection_id": str(collection.id),
                        "vector_document_count": collection.count(),
                        "vectorstore_ready": True,
                    }
                )
            except Exception:
                info["vectorstore_ready"] = False
        else:
            info["vectorstore_ready"] = False

        return info

    async def get_document_list(self, tenant: str | None = None) -> dict[str, Any]:
        """アップロード済みドキュメント一覧を取得"""
        try:
            if not self.vectorstore:
                return {"files": [], "total_files": 0, "total_chunks": 0}

            collection = self.vectorstore._collection
            where = {"tenant": {"$eq": tenant}} if tenant is not None else None
            results = collection.get(include=["metadatas"], where=where)
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

    async def delete_document_by_file_id(
        self, file_id: str, tenant: str | None = None
    ) -> dict[str, Any]:
        """file_idでドキュメントを削除（推奨）"""
        try:
            if not self.vectorstore:
                raise RuntimeError("ベクトルストアが初期化されていません")

            collection = self.vectorstore._collection
            conditions = [{"file_id": {"$eq": file_id}}]
            if tenant is not None:
                conditions.append({"tenant": {"$eq": tenant}})
            where = {"$and": conditions} if len(
                conditions) > 1 else conditions[0]

            results = collection.get(where=where, include=["metadatas"])
            ids = results.get("ids") or []
            if not ids:
                raise ValueError(f"file_id '{file_id}' は見つかりませんでした")

            # 表示用に代表となるファイル名を抽出
            metadatas = results.get("metadatas") or []
            detected_filename = "unknown"
            for md in metadatas:
                if md and md.get("filename"):
                    detected_filename = md.get("filename")
                    break

            deleted_count = len(ids)
            collection.delete(where=where)
            after_count = collection.count()

            remaining_where = (
                {"tenant": {"$eq": tenant}} if tenant is not None else None
            )
            remaining_results = collection.get(
                include=["metadatas"], where=remaining_where
            )
            metadatas = remaining_results.get("metadatas") or []
            remaining_files = (
                len({md.get("filename", "unknown") for md in metadatas if md})
                if metadatas
                else 0
            )

            return {
                "status": "success",
                "message": f"{detected_filename}({file_id})を削除しました",
                "deleted_file_id": file_id,
                "deleted_chunks": deleted_count,
                "remaining_files": remaining_files,
                "remaining_chunks": after_count,
            }
        except Exception as e:
            raise RuntimeError(f"file_id削除に失敗しました: {str(e)}")

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
