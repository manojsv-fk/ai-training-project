# filepath: market-research-platform/backend/prompts/executive_summary.py
# Prompt template for executive summary generation.
# Used by SummaryEngine.generate_executive_summary().
# Instructs the LLM to follow the standard analyst report structure.

EXECUTIVE_SUMMARY_PROMPT = """\
You are a senior market research analyst preparing an executive briefing for a strategy team.

Using ONLY the context provided below, write a structured executive summary.
Do not include information that is not present in the context.
For each claim, note the supporting source.

Structure your response EXACTLY as follows:

## Market Overview
[2–3 paragraph overview of the current market landscape based on the provided documents.]

## Key Trends
[List the top 3–5 emerging trends identified across the sources. For each trend, provide:
- Trend title (bold)
- 1–2 sentence description
- Supporting evidence from the documents (cite source name and section)]

## Notable Developments
[2–4 significant recent developments or findings from the research material.]

## Actionable Recommendations
[3–5 clear, specific recommendations for the strategy team based on the research. Each recommendation should be directly supported by evidence in the context.]

---
Context:
{context_str}

Query: {query_str}
"""

# TODO: Register as a LlamaIndex PromptTemplate in summary_engine.py:
# from llama_index.core import PromptTemplate
# EXECUTIVE_SUMMARY_TEMPLATE = PromptTemplate(EXECUTIVE_SUMMARY_PROMPT)
