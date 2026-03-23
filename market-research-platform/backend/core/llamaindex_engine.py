# filepath: market-research-platform/backend/core/llamaindex_engine.py
# Singleton wrapper around all LlamaIndex resources.
# Initializes the LLM, embedding model, PGVectorStore, and VectorStoreIndex.
# All ingestion, query, and summary engines are built on top of this foundation.

import logging

from llama_index.core import VectorStoreIndex, StorageContext, Settings as LISettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.postgres import PGVectorStore

from config import settings

logger = logging.getLogger(__name__)


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
        logger.info("Initializing LlamaIndex engine...")

        # Configure the LLM
        self.llm = OpenAI(
            model=settings.openai_llm_model,
            api_key=settings.openai_api_key,
            temperature=0.1,  # Low temperature for factual, analytical responses
        )

        # Configure the embedding model
        self.embed_model = OpenAIEmbedding(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

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
            embed_dim=1536,  # text-embedding-3-small dimension
        )

        self._storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store,
        )

        # Create or load VectorStoreIndex from the existing vector store
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self._storage_context,
        )

        logger.info("LlamaIndex engine initialized successfully.")

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
