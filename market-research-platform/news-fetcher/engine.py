# filepath: market-research-platform/news-fetcher/engine.py
# LlamaIndex engine setup for the news-fetcher microservice.
# Focused on indexing only (chunk + embed + store). No query/retrieval needed.

import logging

from llama_index.core import VectorStoreIndex, StorageContext, Settings as LISettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.postgres import PGVectorStore

from config import settings

logger = logging.getLogger(__name__)

# Embedding dimensions per provider
EMBED_DIMS = {
    "huggingface": 384,  # all-MiniLM-L12-v2
    "gemini": 3072,      # models/gemini-embedding-001
    "openai": 1536,      # text-embedding-3-small
}


# ---------------------------------------------------------------------------
# LLM builders (return LLM only)
# ---------------------------------------------------------------------------

def _build_gemini_llm():
    """Create Gemini LLM."""
    from llama_index.llms.gemini import Gemini

    return Gemini(
        model=settings.gemini_llm_model,
        api_key=settings.gemini_api_key,
        temperature=0.1,
    )


def _build_groq_llm():
    """Create Groq LLM."""
    from llama_index.llms.groq import Groq

    return Groq(
        model=settings.groq_llm_model,
        api_key=settings.groq_api_key,
        temperature=0.1,
    )


def _build_openai_llm():
    """Create OpenAI LLM."""
    from llama_index.llms.openai import OpenAI

    return OpenAI(
        model=settings.openai_llm_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
    )


# ---------------------------------------------------------------------------
# Embedding builders (return embed model only)
# ---------------------------------------------------------------------------

def _build_huggingface_embed():
    """Create a free, local HuggingFace embedding model (no API key needed)."""
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(
        model_name=settings.huggingface_embedding_model,
    )


def _build_gemini_embed():
    """Create Gemini embedding model."""
    from llama_index.embeddings.gemini import GeminiEmbedding

    return GeminiEmbedding(
        model_name=settings.gemini_embedding_model,
        api_key=settings.gemini_api_key,
    )


def _build_openai_embed():
    """Create OpenAI embedding model."""
    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


class NewsIndexEngine:
    """
    LlamaIndex resource manager for the news-fetcher service.
    Handles embedding and storing documents into the shared PGVectorStore.
    Uses the same vector store table ('llama_embeddings') as the main backend.
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
        Called once at application startup.

        LLM provider and embedding provider are configured independently:
        - ``LLM_PROVIDER``: groq | gemini | openai
        - ``EMBEDDING_PROVIDER``: huggingface | gemini | openai
        HuggingFace embeddings are the default (free, local, no API key).
        """
        llm_provider = settings.llm_provider.lower()
        embed_provider = settings.embedding_provider.lower()
        logger.info(
            f"Initializing news index engine  "
            f"(llm={llm_provider}, embeddings={embed_provider})"
        )

        # -- Build LLM ----------------------------------------------------------
        llm_builders = {
            "gemini": _build_gemini_llm,
            "groq": _build_groq_llm,
            "openai": _build_openai_llm,
        }
        if llm_provider not in llm_builders:
            raise ValueError(
                f"Unknown LLM provider: {llm_provider}. "
                "Use 'groq', 'gemini', or 'openai'."
            )
        self.llm = llm_builders[llm_provider]()

        # -- Build Embedding model -----------------------------------------------
        embed_builders = {
            "huggingface": _build_huggingface_embed,
            "gemini": _build_gemini_embed,
            "openai": _build_openai_embed,
        }
        if embed_provider not in embed_builders:
            raise ValueError(
                f"Unknown embedding provider: {embed_provider}. "
                "Use 'huggingface', 'gemini', or 'openai'."
            )
        self.embed_model = embed_builders[embed_provider]()

        embed_dim = EMBED_DIMS.get(embed_provider, 384)

        # Set LlamaIndex global defaults
        LISettings.llm = self.llm
        LISettings.embed_model = self.embed_model
        LISettings.chunk_size = settings.chunk_size
        LISettings.chunk_overlap = settings.chunk_overlap
        LISettings.node_parser = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        # Connect to the same PGVectorStore used by the main backend
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

        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self._storage_context,
        )

        logger.info(
            f"News index engine initialized "
            f"(llm={llm_provider}, embeddings={embed_provider}, embed_dim={embed_dim})."
        )

    def add_nodes(self, nodes: list):
        """Insert pre-chunked nodes into the vector store index."""
        if not nodes:
            return
        self.index.insert_nodes(nodes)
        logger.info(f"Indexed {len(nodes)} node(s) into vector store.")

    def add_documents(self, documents: list):
        """Insert LlamaIndex Document objects (auto-chunked by the index)."""
        if not documents:
            return
        for doc in documents:
            self.index.insert(doc)
        logger.info(f"Indexed {len(documents)} document(s) into vector store.")
