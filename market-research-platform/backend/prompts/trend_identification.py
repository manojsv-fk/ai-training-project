# filepath: market-research-platform/backend/prompts/trend_identification.py
# Prompt template for cross-document trend identification.
# Used by SummaryEngine.identify_trends().
# Instructs the LLM to surface recurring themes with confidence scoring.

TREND_IDENTIFICATION_PROMPT = """\
You are a market intelligence analyst specializing in identifying recurring themes
across multiple research sources.

Analyze the following excerpts from multiple documents and identify the top market trends.
Focus on patterns that appear across MULTIPLE sources — do not surface single-source observations
as high-confidence trends.

For each trend, provide a confidence level:
- HIGH: Mentioned in 3+ sources with corroborating evidence
- MEDIUM: Mentioned in 2 sources or strongly implied
- LOW: Mentioned in 1 source but significant enough to flag

Return your response as a JSON array with this exact schema:
[
  {{
    "title": "Short trend label (5–8 words)",
    "description": "1–2 sentence description of the trend",
    "confidence": "HIGH | MEDIUM | LOW",
    "confidence_score": 0.0–1.0,
    "supporting_sources": ["Source Name 1", "Source Name 2"]
  }}
]

Return ONLY the JSON array. No preamble or explanation.

---
Context (excerpts from multiple documents):
{context_str}
"""

# TODO: Parse LLM JSON response in summary_engine.py and map to Trend model objects
