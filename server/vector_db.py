from __future__ import annotations

from typing import Iterable, List, Sequence, Optional

from server.settings import Settings
from util import call_with_retries
from logging_config import logger

import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


class OpenAIEmbeddingFunction(EmbeddingFunction):
    """Embedding function backed by OpenAI embeddings."""

    def __init__(
        self, model_name: str | None = None, api_key: str | None = None
    ) -> None:
        cfg = Settings()
        self.model_name = model_name or cfg.openai_embedding_model
        self.api_key = api_key or cfg.openai_api_key
        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        except Exception as exc:  # noqa: BLE001
            logger.bind(error=str(exc)).error("openai_init_failed")
            self.client = None

    def __call__(self, texts: Sequence[str]) -> Embeddings:
        if not self.client:
            return [[0.0] * 2 for _ in texts]
        try:
            resp = call_with_retries(
                self.client.embeddings.create,
                input=list(texts),
                model=self.model_name,
                timeout=10,
            )
            return [d.embedding for d in resp.data]
        except Exception as exc:  # noqa: BLE001
            logger.bind(error=str(exc)).error("embedding_request_failed")
            return [[0.0] * 2 for _ in texts]


class STEmbeddingFunction(EmbeddingFunction):
    """Embedding function backed by SentenceTransformers."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        cfg = Settings()
        name = model_name or cfg.embedding_model_name
        try:
            self.model = SentenceTransformer(name)
        except Exception:  # noqa: BLE001
            self.model = None

    def __call__(self, texts: Sequence[str]) -> Embeddings:
        if self.model is None:
            return [[0.0] * 2 for _ in texts]
        vectors = self.model.encode(list(texts))
        return vectors.tolist()


class VectorDB:
    """Wrapper around ChromaDB for semantic memory."""

    def __init__(
        self,
        persist_directory: str | None = None,
        *,
        collection_name: str = "memory",
        embedding_function: Optional[EmbeddingFunction] = None,
        model_name: Optional[str] = None,
    ) -> None:
        cfg = Settings()
        persist_directory = persist_directory or cfg.vector_db_path
        self.client = chromadb.PersistentClient(path=persist_directory)
        if not embedding_function:
            provider = cfg.embedding_provider
            if provider.lower() == "openai":
                embedding_function = OpenAIEmbeddingFunction(model_name=model_name)
            else:
                embedding_function = STEmbeddingFunction(model_name=model_name)

        self.collection = self.client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function,
        )

    def add_texts(
        self,
        texts: Iterable[str],
        ids: Optional[Iterable[str]] = None,
        *,
        metadatas: Optional[Iterable[dict[str, str]]] = None,
    ) -> None:
        docs = list(texts)
        if not docs:
            return
        id_list = list(ids) if ids is not None else [str(hash(doc)) for doc in docs]
        kwargs: dict[str, object] = {}
        if metadatas is not None:
            kwargs["metadatas"] = list(metadatas)
        self.collection.add(documents=docs, ids=id_list, **kwargs)

    def search(
        self,
        query: str,
        n_results: int = 3,
        *,
        where: Optional[dict[str, str]] = None,
    ) -> List[str]:
        kwargs: dict[str, object] = {}
        if where is not None:
            kwargs["where"] = where
        result = self.collection.query(
            query_texts=[query], n_results=n_results, **kwargs
        )
        return result.get("documents", [[]])[0]
