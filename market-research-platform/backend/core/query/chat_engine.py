# filepath: market-research-platform/backend/core/query/chat_engine.py
# Streaming chat engine built on LlamaIndex's query engine with citation support.
# Handles multi-turn context and returns token stream + source citations.

import logging
from typing import AsyncGenerator

from llama_index.core import PromptTemplate
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.llms import ChatMessage, MessageRole

from core.llamaindex_engine import LlamaIndexEngine
from prompts.chatbot_qa import CHATBOT_SYSTEM_PROMPT, CHATBOT_QA_PROMPT

logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Wraps LlamaIndex chat engine for streaming, multi-turn Q&A.
    One instance per chat session (to maintain conversation context).
    """

    def __init__(self, engine: LlamaIndexEngine):
        self.engine = engine
        self._chat_engine = None

    def _build_chat_engine(self):
        """
        Build the CondensePlusContextChatEngine with the market research Q&A prompt.
        Called lazily on first query.
        """
        index = self.engine.get_index()
        retriever = self.engine.get_retriever()

        self._chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=retriever,
            system_prompt=CHATBOT_SYSTEM_PROMPT,
            verbose=False,
        )

    async def stream_query(
        self, question: str, chat_history: list = None
    ) -> AsyncGenerator:
        """
        Stream a response to the user's question.

        Yields:
            str tokens one at a time, then a final dict: {"sources": [...]}
        """
        if self._chat_engine is None:
            self._build_chat_engine()

        try:
            # Build chat history from previous messages
            history = []
            if chat_history:
                for msg in chat_history:
                    role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                    history.append(ChatMessage(role=role, content=msg.get("content", "")))

            # Use streaming chat
            response = await self._chat_engine.astream_chat(
                question,
                chat_history=history if history else None,
            )

            # Yield tokens as they arrive
            full_response = ""
            async for token in response.async_response_gen():
                full_response += token
                yield token

            # Extract sources from the response's source nodes
            sources = self._extract_sources(response.source_nodes if hasattr(response, 'source_nodes') else [])
            yield {"sources": sources, "full_response": full_response}

        except Exception as e:
            logger.error(f"Chat engine error: {e}")
            yield f"I encountered an error processing your question: {str(e)}"
            yield {"sources": [], "full_response": ""}

    async def query_simple(self, question: str, chat_history: list = None) -> dict:
        """
        Non-streaming query for cases where we need the full response at once.
        Returns: { "response": str, "sources": list }
        """
        if self._chat_engine is None:
            self._build_chat_engine()

        try:
            history = []
            if chat_history:
                for msg in chat_history:
                    role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                    history.append(ChatMessage(role=role, content=msg.get("content", "")))

            response = await self._chat_engine.achat(
                question,
                chat_history=history if history else None,
            )

            sources = self._extract_sources(
                response.source_nodes if hasattr(response, 'source_nodes') else []
            )

            return {
                "response": str(response),
                "sources": sources,
            }
        except Exception as e:
            logger.error(f"Chat query error: {e}")
            return {"response": f"Error: {str(e)}", "sources": []}

    def _extract_sources(self, source_nodes: list) -> list[dict]:
        """
        Convert LlamaIndex source nodes into a list of citation dicts.
        Format: [{ "source_name": str, "page": int|None, "document_id": int|None, "score": float }]
        """
        sources = []
        seen = set()  # Deduplicate by source_name + document_id

        for node in source_nodes:
            metadata = node.metadata if hasattr(node, 'metadata') else {}
            # Handle nodes that are wrapped in NodeWithScore
            if hasattr(node, 'node'):
                metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}

            source_name = metadata.get("source_name", "Unknown")
            document_id = metadata.get("document_id")
            page = metadata.get("page")
            score = node.score if hasattr(node, 'score') else None

            key = f"{source_name}_{document_id}"
            if key not in seen:
                seen.add(key)
                sources.append({
                    "source_name": source_name,
                    "document_id": document_id,
                    "page": page,
                    "score": round(score, 3) if score else None,
                })

        return sources
