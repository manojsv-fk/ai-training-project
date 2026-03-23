# filepath: market-research-platform/backend/core/query/summary_engine.py
# Summary and trend analysis engine. Uses LlamaIndex query engines
# for multi-document summarization and trend identification.

import json
import logging
from datetime import datetime, timezone

from llama_index.core import PromptTemplate
from llama_index.core.response_synthesizers import get_response_synthesizer

from core.llamaindex_engine import LlamaIndexEngine
from prompts.executive_summary import EXECUTIVE_SUMMARY_PROMPT
from prompts.trend_identification import TREND_IDENTIFICATION_PROMPT
from prompts.scheduled_brief import SCHEDULED_BRIEF_PROMPT

logger = logging.getLogger(__name__)


class SummaryEngine:
    """
    Generates executive summaries and trend reports using LlamaIndex query engines.
    """

    def __init__(self, engine: LlamaIndexEngine):
        self.engine = engine

    async def generate_executive_summary(
        self, document_ids: list[int] = None, title: str = "Executive Summary"
    ) -> str:
        """
        Generate a structured executive summary across selected documents.
        Follows the template: Market Overview -> Key Trends -> Notable Developments -> Recommendations.

        Returns:
            str: Markdown-formatted report content.
        """
        retriever = self.engine.get_retriever(top_k=15)  # More chunks for summaries

        # Build the query to retrieve relevant content
        query = f"Provide a comprehensive executive summary covering market overview, key trends, notable developments, and actionable recommendations for: {title}"

        # Retrieve relevant nodes, optionally filtering by document_ids
        nodes = await retriever.aretrieve(query)

        if document_ids:
            nodes = [
                n for n in nodes
                if n.metadata.get("document_id") in document_ids
            ]

        if not nodes:
            return "## Executive Summary\n\nNo relevant content found in the selected documents. Please ensure documents have been properly ingested."

        # Build context from retrieved nodes
        context = "\n\n---\n\n".join([
            f"[Source: {n.metadata.get('source_name', 'Unknown')}]\n{n.get_content()}"
            for n in nodes
        ])

        # Use the response synthesizer with our executive summary prompt
        prompt_template = PromptTemplate(EXECUTIVE_SUMMARY_PROMPT)
        synthesizer = get_response_synthesizer(
            response_mode="tree_summarize",
            text_qa_template=prompt_template,
        )

        response = await synthesizer.asynthesize(
            query=query,
            nodes=nodes,
        )

        return str(response)

    async def identify_trends(self, document_ids: list[int] = None) -> list[dict]:
        """
        Run a multi-document query to identify recurring themes and market trends.
        If document_ids is None, queries across the entire corpus.

        Returns:
            list[dict]: List of trend dicts with title, description, confidence_score, etc.
        """
        retriever = self.engine.get_retriever(top_k=20)

        query = "Identify the major recurring themes, emerging trends, and market shifts across all available research documents. Focus on patterns mentioned in multiple sources."

        nodes = await retriever.aretrieve(query)

        if document_ids:
            nodes = [
                n for n in nodes
                if n.metadata.get("document_id") in document_ids
            ]

        if not nodes:
            return []

        # Build context from retrieved nodes
        context = "\n\n---\n\n".join([
            f"[Source: {n.metadata.get('source_name', 'Unknown')}]\n{n.get_content()}"
            for n in nodes
        ])

        # Use the LLM directly with the trend identification prompt
        llm = self.engine.llm
        prompt = TREND_IDENTIFICATION_PROMPT.format(context_str=context)

        response = await llm.acomplete(prompt)
        response_text = str(response)

        # Parse the JSON response from the LLM
        trends = _parse_trend_response(response_text)

        # Enrich trends with source document IDs from the retrieved nodes
        source_doc_ids = list(set(
            n.metadata.get("document_id")
            for n in nodes
            if n.metadata.get("document_id")
        ))

        for trend in trends:
            trend["source_document_ids"] = source_doc_ids
            trend["supporting_chunk_ids"] = [
                n.node_id for n in nodes[:5]  # Top 5 chunks as supporting evidence
            ]

        return trends

    async def generate_scheduled_brief(self, topics: list[str]) -> str:
        """
        Generate a concise time-bound brief for scheduled delivery (e.g., weekly).
        Queries the most recently ingested documents matching the given topics.

        Returns:
            str: Markdown-formatted brief content.
        """
        retriever = self.engine.get_retriever(top_k=10)

        topic_str = ", ".join(topics) if topics else "market trends"
        query = f"Summarize the latest developments and news for: {topic_str}"

        nodes = await retriever.aretrieve(query)

        if not nodes:
            return f"## Weekly Brief: {topic_str}\n\nNo recent content available for this topic."

        context = "\n\n---\n\n".join([
            f"[Source: {n.metadata.get('source_name', 'Unknown')}]\n{n.get_content()}"
            for n in nodes
        ])

        # Format the scheduled brief prompt
        now = datetime.now(timezone.utc)
        prompt = SCHEDULED_BRIEF_PROMPT.format(
            topic=topic_str,
            date_range=f"Week of {now.strftime('%B %d, %Y')}",
            context_str=context,
        )

        llm = self.engine.llm
        response = await llm.acomplete(prompt)

        return str(response)


def _parse_trend_response(response_text: str) -> list[dict]:
    """
    Parse the LLM's JSON response into a list of trend dicts.
    Handles potential JSON formatting issues gracefully.
    """
    try:
        # Try to find JSON array in the response
        text = response_text.strip()

        # Find the first '[' and last ']' to extract the JSON array
        start = text.find("[")
        end = text.rfind("]")

        if start != -1 and end != -1:
            json_str = text[start:end + 1]
            raw_trends = json.loads(json_str)
        else:
            logger.warning("No JSON array found in trend response")
            return []

        # Normalize and validate each trend
        trends = []
        confidence_map = {"HIGH": 0.9, "MEDIUM": 0.65, "LOW": 0.35}

        for t in raw_trends:
            confidence_label = t.get("confidence", "MEDIUM").upper()
            trend = {
                "title": t.get("title", "Untitled Trend"),
                "description": t.get("description", ""),
                "confidence_score": t.get(
                    "confidence_score",
                    confidence_map.get(confidence_label, 0.5)
                ),
                "tags": t.get("supporting_sources", []),
            }
            trends.append(trend)

        return trends

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse trend JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing trends: {e}")
        return []
