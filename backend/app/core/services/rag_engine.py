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
import chromadb
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

    # RAG用プロンプトテンプレート（XML構造化版）
    RAG_PROMPT_TEMPLATE = """\
<system_role>
あなたはカスタマーセンターの担当者です。親しみと安心感のある丁寧な言葉遣いで、提供された資料（context）の内容に基づいてユーザーの質問に回答します。
</system_role>

<instructions>
<primary_directive>
- 最終出力は「顧客向けの本文」のみを返してください。
- 内部メモや下書き（例：「わかっていること」「まだ不明なこと」「次に取るべき行動」などの分析見出し）は出力しないでください。
- contextに情報がある限り、必ず可能な範囲で回答を作成してください（部分回答可）。不足点は本文中で簡潔に触れます。
</primary_directive>

<response_rules>
<rule priority="highest">
<condition>contextに質問に関連する情報が含まれている</condition>
<action>
- 関連情報を抽出し、わかりやすい日本語で要約・統合して回答します。
- 重要な点は箇条書きを用いても構いませんが、顧客に読みやすい本文としてまとめます。
- 断定できない事項は限定表現（「資料によれば」「contextの範囲では」）を用います。
</action>
</rule>

<rule priority="high">
<condition>contextが部分的にしか該当しない</condition>
<action>
- まず結論（言える範囲）を述べ、その根拠（contextの要約）を簡潔に示します。
- 不足情報がある場合は、その旨を一文で触れ、次の確認手段（問い合わせ・資料参照）を提案します。
</action>
</rule>

<rule priority="medium">
<condition>挨拶・雑談</condition>
<action>簡潔で親しみやすい応答を返します。</action>
</rule>
</response_rules>

<constraints>
- contextに明記されていない新規事実は作らないでください。
- 一般的知識や外部情報は持ち込まないでください。
- 絶対に推測や想像で回答を補完しないでくさい。
- 完全に無関係なcontextしかない、またはcontextが空のときのみ回答不能とします（理由を一言で記載）。
- 問い合わせ先や連絡方法はcontextに記載がある場合のみ本文に含めてください（なければ一般的な問い合わせ誘導を一文で行います）。
</constraints>

<output_tone>
- 丁寧・前向き・簡潔。2〜4文の導入→要点→補足/次のアクション の流れを推奨。
- 不要な専門用語は避け、顧客がすぐ理解できる表現を優先します。
</output_tone>

<output_format>
<format_type>GitHub Flavored Markdown (GFM)</format_type>
<guidelines>
- 必要に応じて見出し（##）や短い箇条書きを使い、可読性を高めます。
- 長文の引用や原文コピペは避け、要点のみを簡潔に要約します。
- 回答全体を三連バッククォートで囲まない・先頭に「markdown」を書かない。
</guidelines>
</output_format>
</instructions>

<context>
{context}
</context>

<user_question>
{question}
</user_question>

<response>
上記のcontextとuser_questionに基づき、顧客向けの本文のみを出力してください。内部分析の見出しや下書きは出力しないでください。
</response>"""

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
        self._chroma_client: Any | None = None
        self._ensure_directories()
        self._llm_cache: dict[tuple[str, float, int], ChatOpenAI] = {}

    def _get_llm(
        self,
        model: str | None,
        temperature: float | None,
        max_tokens: int | None = None,
    ) -> tuple[ChatOpenAI, str]:
        """(model, temperature)ごとにLLMをキャッシュして取得"""
        used_model = model or settings.default_model
        used_temp = (
            temperature if temperature is not None else settings.default_temperature
        )
        used_max = (
            int(max_tokens)
            if max_tokens is not None
            else int(settings.default_max_output_tokens)
        )
        key = (used_model, used_temp, used_max)
        if key not in self._llm_cache:
            api_key = (
                SecretStr(settings.openai_api_key)
                if settings.openai_api_key is not None
                else None
            )
            self._llm_cache[key] = ChatOpenAI(
                model=used_model,
                temperature=used_temp,
                api_key=api_key,
                timeout=60,
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
            # ChromaDB (v0.5.x) の初期化: 既定テナント/DB を用意し、クライアントを確立
            try:
                admin = chromadb.AdminClient(self.chroma_settings)
                try:
                    admin.create_tenant(name="default_tenant")
                except Exception:
                    pass
                try:
                    admin.create_database(
                        name="default_database", tenant="default_tenant"
                    )
                except Exception:
                    pass
            except Exception:
                # AdminClient が失敗しても後続で Client が初期化できる可能性があるため続行
                pass

            try:
                self._chroma_client = chromadb.Client(
                    self.chroma_settings,
                    tenant="default_tenant",
                    database="default_database",
                )
            except Exception:
                self._chroma_client = None

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
                # 既存のベクトルストアに接続（client を優先して使用）
                kwargs: dict[str, Any] = {
                    "persist_directory": str(settings.persist_path),
                    "embedding_function": self.embeddings,
                }
                if self._chroma_client is not None:
                    kwargs["client"] = self._chroma_client
                else:
                    kwargs["client_settings"] = self.chroma_settings
                self.vectorstore = Chroma(**kwargs)
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
                if self._chroma_client is not None:
                    self.vectorstore = Chroma.from_texts(
                        texts=chunks,
                        embedding=self.embeddings,
                        metadatas=metadatas,
                        client=self._chroma_client,
                        persist_directory=str(settings.persist_path),
                    )
                else:
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
        """文書検索（類似度閾値でフィルタリング）
        Args:
            query: 検索クエリ
            top_k: 検索結果の上位k件

        Returns:
            検索結果の文書リスト（類似度閾値以下の文書のみ）

        Raises:
            RuntimeError: ベクトルストアが初期化されていない場合
        """
        if not self.vectorstore:
            raise RuntimeError("ベクトルストアが初期化されていません")

        k = top_k or settings.default_top_k

        try:
            kwargs: dict[str, Any] = {}
            if tenant is not None:
                kwargs["filter"] = {"tenant": tenant}

            # スコア付きで検索を実行
            results = await self.vectorstore.asimilarity_search_with_score(
                query, k=k, filter=kwargs.get("filter")
            )

            # デバッグ: スコアを確認
            print(f"[DEBUG] 検索クエリ: {query[:50]}...")
            print(f"[DEBUG] 検索結果数: {len(results)}")
            for i, (doc, score) in enumerate(results):
                print(
                    f"[DEBUG] 文書{i+1}: スコア={score:.4f}, 内容={doc.page_content[:100]}..."
                )

            # 類似度閾値でフィルタリング（Chromaは距離を返すので、小さいほど類似）
            threshold = settings.similarity_score_threshold
            print(f"[DEBUG] 閾値: {threshold}")
            filtered_documents = []
            for doc, score in results:
                # スコアが閾値以下（類似度が高い）の文書のみ採用
                if score <= threshold:
                    filtered_documents.append(doc)
                    print(f"[DEBUG] ✓ 採用: スコア={score:.4f}")
                else:
                    print(f"[DEBUG] ✗ 除外: スコア={score:.4f}")

            print(f"[DEBUG] フィルタ後の文書数: {len(filtered_documents)}")
            return filtered_documents

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
                    "llm_model": getattr(self.llm, "model", settings.default_model),
                }

            documents = await self.search_documents(question, top_k, tenant=tenant)

            if not documents:
                return {
                    "answer": "申し訳ございませんが、その質問に関する情報が見つかりませんでした。（関連文書:0件）",
                    "documents": [],
                    "context_used": "",
                    "llm_model": getattr(self.llm, "model", settings.default_model),
                }

            # トークンベース詰め込み（質問・プロンプト・出力上限を考慮した残り枠に収める）
            model_for_encoding = model or getattr(
                self.llm, "model", settings.default_model
            )
            try:
                enc = tiktoken.encoding_for_model(model_for_encoding)
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")

            context_window = getattr(settings, "default_context_window_tokens", 8192)
            prompt_overhead = getattr(settings, "prompt_overhead_tokens", 512)

            question_tokens = len(enc.encode(question or ""))
            fixed_prompt_tokens = prompt_overhead

            used_max_out = (
                int(max_output_tokens)
                if max_output_tokens is not None
                else int(settings.default_max_output_tokens)
            )

            remaining_input_budget = max(
                0, context_window - fixed_prompt_tokens - question_tokens - used_max_out
            )

            selected_parts = self._select_context_parts(
                documents, enc, remaining_input_budget
            )

            context = self._format_documents(selected_parts)

            if (
                model is not None
                or temperature is not None
                or max_output_tokens is not None
            ):
                llm, used_model = self._get_llm(model, temperature, max_output_tokens)
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

    def _select_context_parts(
        self,
        documents: list[Document],
        enc: Any,
        remaining_input_budget: int,
    ) -> list[str]:
        """トークン予算内に収まるように文書内容を選択・クリップ

        Args:
            documents: 検索で得た文書のリスト
            enc: トークナイザ（tiktoken エンコーダ）
            remaining_input_budget: コンテキストとして投入可能なトークン数の上限

        Returns:
            コンテキストに使用するテキスト片のリスト
        """
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
                        clipped = part[: max(0, remaining * avg_chars_per_token)]
                    if clipped:
                        selected_parts.append(clipped)
                        used_tokens = remaining_input_budget
                break

        return selected_parts

    def _format_documents(self, selected_parts: list[str]) -> str:
        """選択済みテキストパートを結合してコンテキストとして使用
        Args:
            selected_parts: テキスト片のリスト

        Returns:
            フォーマットされたコンテキスト
        """
        return "\n\n".join(selected_parts)

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

    async def get_chunks_by_file_and_index(
        self,
        pairs: list(tuple[str, int]),
        tenant: str | None = None,
    ) -> list[dict[str, Any]]:
        """(file_id, chunk_index)の組みでチャンクを取得

        Args:
            pairs: (file_id, chunk_index)のリスト
            tenant: テナント（メタデータの格納）

        Return:
            各チャンクの{"content": str, "metadata": dict}のリスト
        """
        if not self.vectorstore:
            raise RuntimeError("ベクトルストアが初期化されていません")

        collection = self.vectorstore._collection
        results: list[dict[str, Any]] = []
        for file_id, chunk_index in pairs:
            try:
                conditions = [
                    {"file_id": {"$eq": file_id}},
                    {"chunk_index": {"$eq": int(chunk_index)}},
                ]
                if tenant is not None:
                    conditions.append({"tenant": {"$eq": tenant}})
                where = {"$and": conditions}
                got = collection.get(where=where, include=["documents", "metadatas"])
                docs = got.get("documents") or []
                metas = got.get("metadatas") or []
                if docs and metas:
                    results.append({"content": docs[0], "metadata": metas[0]})
            except Exception:
                continue
        return results

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
            where = {"$and": conditions} if len(conditions) > 1 else conditions[0]

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
