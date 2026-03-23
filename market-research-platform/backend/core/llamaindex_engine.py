# filepath: market-research-platform/backend/core/llamaindex_engine.py
# Singleton wrapper around all LlamaIndex resources.
# Initializes the LLM, embedding model, PGVectorStore, and VectorStoreIndex.
# Supports configurable LLM providers (Gemini, Groq, OpenAI) and
# embedding providers (HuggingFace local, Gemini, OpenAI).

import logging

from llama_index.core import VectorStoreIndex, StorageContext, Settings as LISettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.postgres import PGVectorStore

from config import settings

logger = logging.getLogger(__name__)

# Embedding dimensions per embedding provider
EMBED_DIMS = {
    "gemini":      3072,   # models/gemini-embedding-001
    "openai":      1536,   # text-embedding-3-small
    "huggingface": 384,    # all-MiniLM-L12-v2
}


def _build_llm_gemini():
    """Create Gemini LLM."""
    from llama_index.llms.gemini import Gemini

    return Gemini(
        model=settings.gemini_llm_model,
        api_key=settings.gemini_api_key,
        temperature=0.1,
    )


def _build_llm_groq():
    """Create Groq LLM."""
    from llama_index.llms.groq import Groq

    return Groq(
        model=settings.groq_llm_model,
        api_key=settings.groq_api_key,
        temperature=0.1,
    )


def _build_llm_openai():
    """Create OpenAI LLM."""
    from llama_index.llms.openai import OpenAI

    return OpenAI(
        model=settings.openai_llm_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
    )


def _build_embed_huggingface():
    """Create free, local HuggingFace embedding model (no API key needed)."""
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(model_name=settings.huggingface_embedding_model)


def _build_embed_gemini():
    """Create Gemini embedding model."""
    from llama_index.embeddings.gemini import GeminiEmbedding

    return GeminiEmbedding(
        model_name=settings.gemini_embedding_model,
        api_key=settings.gemini_api_key,
    )


def _build_embed_openai():
    """Create OpenAI embedding model."""
    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


class LlamaIndexEngine:
    """
    Central LlamaIndex resource manager.
    Instantiated once at application startup and injected as a FastAPI dependency.
    """

    def __init__(self):
        self.llm = None
        self.embed_model = None
        self.vector_store = None
        self.index = None
        self._storage_context = None

    def initialize(self):
        """
        Set up LLM, embeddings, vector store, and index.
        Called once at application startup in main.py lifespan hook.
        """
        llm_provider = settings.llm_provider.lower()
        embed_provider = settings.embedding_provider.lower()
        logger.info(
            f"Initializing LlamaIndex engine with LLM provider: {llm_provider}, "
            f"embedding provider: {embed_provider}"
        )

        # Build LLM based on configured LLM provider
        if llm_provider == "gemini":
            self.llm = _build_llm_gemini()
        elif llm_provider == "groq":
            self.llm = _build_llm_groq()
        elif llm_provider == "openai":
            self.llm = _build_llm_openai()
        else:
            raise ValueError(f"Unknown LLM provider: {llm_provider}. Use 'groq', 'gemini', or 'openai'.")

        # Build embedding model based on configured embedding provider
        if embed_provider == "huggingface":
            self.embed_model = _build_embed_huggingface()
        elif embed_provider == "gemini":
            self.embed_model = _build_embed_gemini()
        elif embed_provider == "openai":
            self.embed_model = _build_embed_openai()
        else:
            raise ValueError(
                f"Unknown embedding provider: {embed_provider}. "
                "Use 'huggingface', 'gemini', or 'openai'."
            )

        embed_dim = EMBED_DIMS.get(embed_provider, 384)

        # Set LlamaIndex global defaults so all components use these models
        LISettings.llm = self.llm
        LISettings.embed_model = self.embed_model
        LISettings.chunk_size = settings.chunk_size
        LISettings.chunk_overlap = settings.chunk_overlap
        LISettings.node_parser = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        # Connect to PostgreSQL with pgvector for embedding storage
        self.vector_store = PGVectorStore.from_params(
            database=settings.postgres_db,
            host=settings.postgres_host,
            password=settings.postgres_password,
            port=str(settings.postgres_port),
            user=settings.postgres_user,
            table_name="llama_embeddings",
            embed_dim=embed_dim,
        )

        self._storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store,
        )

        # Create or load VectorStoreIndex from the existing vector store
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self._storage_context,
        )

        logger.info(
            f"LlamaIndex engine initialized successfully "
            f"(llm={llm_provider}, embeddings={embed_provider}, embed_dim={embed_dim})."
        )

    def get_index(self) -> VectorStoreIndex:
        """Return the initialized VectorStoreIndex. Raise if not initialized."""
        if self.index is None:
            raise RuntimeError("LlamaIndex engine not initialized. Call initialize() first.")
        return self.index

    def get_retriever(self, top_k: int = None):
        """
        Return a retriever over the vector index.
        Uses vector similarity search with configurable top_k.
        """
        return self.get_index().as_retriever(
            similarity_top_k=top_k or settings.retrieval_top_k,
        )

    def add_documents(self, documents: list):
        """
        Insert LlamaIndex Document objects into the index.
        The index handles chunking, embedding, and storage automatically.
        """
        if not documents:
            return
        for doc in documents:
            self.index.insert(doc)
        logger.info(f"Added {len(documents)} document(s) to the index.")

    def add_nodes(self, nodes: list):
        """
        Insert pre-chunked nodes directly into the index.
        Used when we want manual control over chunking (e.g., PDF ingestion).
        """
        if not nodes:
            return
        self.index.insert_nodes(nodes)
        logger.info(f"Added {len(nodes)} node(s) to the index.")

    def delete_document(self, llamaindex_doc_id: str):
        """Remove all nodes belonging to a document from the index."""
        try:
            self.index.delete_ref_doc(llamaindex_doc_id, delete_from_docstore=True)
            logger.info(f"Deleted document {llamaindex_doc_id} from index.")
        except Exception as e:
            logger.warning(f"Failed to delete document {llamaindex_doc_id}: {e}")


# Singleton instance
_engine: LlamaIndexEngine | None = None


def get_engine() -> LlamaIndexEngine:
    """FastAPI dependency — returns the singleton engine instance."""
    global _engine
    if _engine is None:
        _engine = LlamaIndexEngine()
        _engine.initialize()
    return _engine
