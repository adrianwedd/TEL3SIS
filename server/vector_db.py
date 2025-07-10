from __future__ import annotations

import os
from typing import Iterable, List, Sequence, Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


class OpenAIEmbeddingFunction(EmbeddingFunction):
    """Embedding function backed by OpenAI embeddings."""

    def __init__(
        self, model_name: str | None = None, api_key: str | None = None
    ) -> None:
        self.model_name = model_name or os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        except Exception:  # noqa: BLE001
            self.client = None

    def __call__(self, texts: Sequence[str]) -> Embeddings:
        if not self.client:
            return [[0.0] * 2 for _ in texts]
        try:
            resp = self.client.embeddings.create(
                input=list(texts), model=self.model_name
            )
            return [d.embedding for d in resp.data]
        except Exception:  # noqa: BLE001
            return [[0.0] * 2 for _ in texts]


class STEmbeddingFunction(EmbeddingFunction):
    """Embedding function backed by SentenceTransformers."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        name = model_name or os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
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
        persist_directory = persist_directory or os.getenv(
            "VECTOR_DB_PATH", "vector_store"
        )
        self.client = chromadb.PersistentClient(path=persist_directory)
        if not embedding_function:
            provider = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
            if provider.lower() == "openai":
                embedding_function = OpenAIEmbeddingFunction(model_name=model_name)
            else:
                embedding_function = STEmbeddingFunction(model_name=model_name)

        self.collection = self.client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function,
        )

    def add_texts(
        self, texts: Iterable[str], ids: Optional[Iterable[str]] = None
    ) -> None:
        docs = list(texts)
        if not docs:
            return
        id_list = list(ids) if ids is not None else [str(hash(doc)) for doc in docs]
        self.collection.add(documents=docs, ids=id_list)

    def search(self, query: str, n_results: int = 3) -> List[str]:
        result = self.collection.query(query_texts=[query], n_results=n_results)
        return result.get("documents", [[]])[0]
