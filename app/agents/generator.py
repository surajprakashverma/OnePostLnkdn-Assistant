import truststore
truststore.inject_into_ssl()

"""
Generator Agent
----------------
Takes the Planner Agent's output (topic, subtopic, notes, past_posts)
and drafts a LinkedIn post using Gemini via LangChain.

Run this file directly to test in isolation:
    python -m app.agents.generator
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings

# ---- LLM setup ----
llm = ChatGoogleGenerativeAI(
    model=settings.GOOGLE_Model,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
)

# ---- Prompt template ----
PROMPT = ChatPromptTemplate.from_template(
    """You are writing a LinkedIn post for a software engineer who is documenting
their daily learning journey in public.

Topic: {topic}
Subtopic: {subtopic}
Learning notes (optional, may be empty): {notes}

Past posts already shared on this topic (avoid repeating the same angle/phrasing):
{past_posts}

{revision_feedback_section}

Write a LinkedIn post that:
- Sounds personal and authentic, like a "day in my learning journey" update
- Is 150-200 words long
- Shares one specific, concrete insight or takeaway (not generic fluff)
- Ends with 3-5 relevant hashtags (e.g. #Python #Django #100DaysOfCode)
- Does NOT include any placeholder text like "[Day X]" — write it as ready-to-post content
- Does NOT include any API keys, tokens, internal project names, or confidential details
- Does NOT use ANY Markdown formatting — no backticks (`), no asterisks (*) for bold/italic,
  no headers (#), no bullet symbols. LinkedIn does not render Markdown, so technical terms
  like method names should be written in plain text (e.g. select_related, not `select_related`)
- Write technical terms naturally in plain sentences, as if explaining to a colleague out loud

Output ONLY the post text, nothing else (no preamble, no explanation).
"""
)
def _extract_text(content) -> str:
    """
    Newer langchain-google-genai versions may return response.content as
    either a plain string or a list of content blocks (dicts with a 'text' key).
    This normalizes both cases into a single string.
    """
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts).strip()

    return str(content).strip()


def generate_post(
    topic: str,
    subtopic: str = "",
    notes: str = "",
    past_posts: list[str] | None = None,
    revision_feedback: str = "",
) -> str:
    """
    Generates a draft LinkedIn post text for the given topic.
    If revision_feedback is provided, the LLM is asked to specifically
    address that feedback in this new attempt.
    """
    past_posts = past_posts or []
    past_posts_text = "\n---\n".join(past_posts) if past_posts else "(none yet)"

    if revision_feedback:
        revision_feedback_section = (
            f"IMPORTANT - This is a REVISION. Your previous attempt had these issues:\n"
            f"{revision_feedback}\n"
            f"Fix these specific issues in this new version."
        )
    else:
        revision_feedback_section = ""

    chain = PROMPT | llm
    response = chain.invoke({
        "topic": topic,
        "subtopic": subtopic or "N/A",
        "notes": notes or "N/A",
        "past_posts": past_posts_text,
        "revision_feedback_section": revision_feedback_section,
    })

    return _extract_text(response.content)

if __name__ == "__main__":
    # Quick isolated test â€” run: python -m app.agents.generator
    from app.agents.planner import plan_next_post

    plan = plan_next_post()

    if not plan:
        print("No eligible topic found. Run the planner first to seed roadmap data.")
    else:
        print(f"Generating post for topic: {plan['topic']} / {plan['subtopic']}\n")

        draft = generate_post(
            topic=plan["topic"],
            subtopic=plan["subtopic"],
            notes=plan["notes"],
            past_posts=plan["past_posts"],
        )

        print("=" * 60)
        print("DRAFT LINKEDIN POST")
        print("=" * 60)
        print(draft)
        print("=" * 60)
        print(f"\nCharacter count: {len(draft)}")
