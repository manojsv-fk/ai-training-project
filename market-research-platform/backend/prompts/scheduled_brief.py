# filepath: market-research-platform/backend/prompts/scheduled_brief.py
# Prompt template for scheduled weekly/periodic market briefs.
# Optimized for concise, time-bound summaries.
# Used by SummaryEngine.generate_scheduled_brief().

SCHEDULED_BRIEF_PROMPT = """\
You are a market intelligence analyst preparing a concise weekly briefing
for a busy executive strategy team.

Using ONLY the context below (sourced from articles and reports published
in the last 7 days), write a tight, scannable weekly brief.

Structure your response EXACTLY as follows:

## This Week in [TOPIC]: [DATE RANGE]

**The Big Picture** (2–3 sentences: What is the single most important development this week?)

**Top Stories**
1. [Headline-style summary] — *Source*
2. [Headline-style summary] — *Source*
3. [Headline-style summary] — *Source*
(Include up to 5 top stories)

**Trend Watch**
[One emerging pattern or recurring theme seen across this week's material]

**Watch Next Week**
[1–2 things to monitor based on this week's developments]

Keep the entire brief under 400 words. Prioritize impact over completeness.

---
Topic: {topic}
Date range: {date_range}

Context:
{context_str}
"""

# TODO: In scheduler/jobs.py, populate {topic} and {date_range} at runtime
