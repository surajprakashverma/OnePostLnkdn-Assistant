import truststore
truststore.inject_into_ssl()

"""
Verifier Agent
--------------
Two-layer QA gate before a draft ever reaches the email approval step:

  Layer 1 (rule-based, fast, free):
    - length within LinkedIn-safe bounds
    - hashtag count (3-6)
    - no leaked API keys/secrets/tokens
    - no leftover placeholder text
    - no Markdown formatting (LinkedIn doesn't render it)

  Layer 2 (LLM critic, uses Gemini):
    - tone/authenticity check
    - relevance to the stated topic
    - engagement quality
    - returns PASS/FAIL + specific feedback for revision

Run this file directly to test in isolation:
    python -m app.agents.verifier
"""
import re
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings

# ---- LLM setup (reused for the critic) ----
critic_llm = ChatGoogleGenerativeAI(
    model=settings.GOOGLE_Model,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.2,  # low temperature -> more consistent, less creative scoring
)

# =========================================================
# LAYER 1: Rule-based checks
# =========================================================

# Common secret/key patterns to guard against accidental leaks
SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z\-_]{35}",           # Google API key
    r"sk-[A-Za-z0-9]{20,}",              # OpenAI-style key
    r"ghp_[A-Za-z0-9]{36}",              # GitHub token
    r"(?i)api[_-]?key\s*[:=]\s*\S+",     # generic "api_key: xxxx"
    r"(?i)secret[_-]?key\s*[:=]\s*\S+",  # generic "secret_key: xxxx"
    r"(?i)password\s*[:=]\s*\S+",        # generic "password: xxxx"
    r"Bearer\s+[A-Za-z0-9\-_.]+",        # bearer tokens
]

PLACEHOLDER_PATTERNS = [
    r"\[Day\s*\d*\]", r"\bTODO\b", r"\bXXXX\b", r"\blorem ipsum\b",
    r"\{.*?\}",  # leftover template braces like {topic}
]

MARKDOWN_PATTERNS = [
    r"`[^`]+`",           # backtick code formatting
    r"\*\*[^*]+\*\*",     # bold asterisks
    r"(?m)^#{1,6}\s",     # markdown headers
]

MIN_WORDS = 50
MAX_WORDS = 300
MAX_CHARS = 3000          # LinkedIn hard limit
MIN_HASHTAGS = 3
MAX_HASHTAGS = 6


def rule_based_check(draft: str) -> dict:
    issues = []

    word_count = len(draft.split())
    char_count = len(draft)

    if word_count < MIN_WORDS:
        issues.append(f"Too short: {word_count} words (min {MIN_WORDS})")
    if word_count > MAX_WORDS:
        issues.append(f"Too long: {word_count} words (max {MAX_WORDS})")
    if char_count > MAX_CHARS:
        issues.append(f"Exceeds LinkedIn char limit: {char_count} chars (max {MAX_CHARS})")

    hashtags = re.findall(r"#\w+", draft)
    if len(hashtags) < MIN_HASHTAGS:
        issues.append(f"Too few hashtags: {len(hashtags)} (min {MIN_HASHTAGS})")
    if len(hashtags) > MAX_HASHTAGS:
        issues.append(f"Too many hashtags: {len(hashtags)} (max {MAX_HASHTAGS})")

    for pattern in SECRET_PATTERNS:
        if re.search(pattern, draft):
            issues.append(f"Potential leaked secret/key detected (pattern: {pattern})")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, draft, re.IGNORECASE):
            issues.append(f"Leftover placeholder text detected (pattern: {pattern})")

    for pattern in MARKDOWN_PATTERNS:
        if re.search(pattern, draft):
            issues.append(f"Markdown formatting detected (not supported on LinkedIn): pattern {pattern}")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "word_count": word_count,
        "char_count": char_count,
        "hashtag_count": len(hashtags),
    }


# =========================================================
# LAYER 2: LLM critic
# =========================================================

CRITIC_PROMPT = ChatPromptTemplate.from_template(
    """You are a strict LinkedIn content editor reviewing a draft post before publication.

Topic the post should cover: {topic}

Draft post:
---
{draft}
---

Evaluate the draft on:
1. Authenticity - does it sound like a genuine personal reflection, not generic AI-written fluff?
2. Relevance - does it actually relate to the stated topic?
3. Engagement quality - is there a specific, concrete insight (not vague generalities)?
4. Professionalism - appropriate tone for a professional network, no oversharing or awkward phrasing.

Respond ONLY with valid JSON in this exact format, no other text:
{{
  "passed": true or false,
  "score": 1-10,
  "feedback": "specific, actionable feedback if passed is false, otherwise empty string"
}}
"""
)


def _extract_text(content) -> str:
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


def llm_critic_check(topic: str, draft: str) -> dict:
    chain = CRITIC_PROMPT | critic_llm
    response = chain.invoke({"topic": topic, "draft": draft})
    raw_text = _extract_text(response.content)

    # Gemini sometimes wraps JSON in ```json ... ``` -- strip that if present
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fail safe: if the critic's response isn't parseable, treat as a failed check
        result = {
            "passed": False,
            "score": 0,
            "feedback": f"Critic response was not valid JSON: {raw_text[:200]}",
        }

    return result


# =========================================================
# Combined verification
# =========================================================

def verify_post(topic: str, draft: str) -> dict:
    """
    Runs Layer 1 (rules) first -- cheap and fast. Only calls the LLM critic
    (Layer 2) if rules pass, to avoid wasting API calls on obviously broken drafts.
    """
    rule_result = rule_based_check(draft)

    if not rule_result["passed"]:
        return {
            "passed": False,
            "layer_failed": "rule_based",
            "rule_result": rule_result,
            "critic_result": None,
        }

    critic_result = llm_critic_check(topic, draft)

    return {
        "passed": rule_result["passed"] and critic_result.get("passed", False),
        "layer_failed": None if critic_result.get("passed", False) else "llm_critic",
        "rule_result": rule_result,
        "critic_result": critic_result,
    }


if __name__ == "__main__":
    # Quick isolated test -- run: python -m app.agents.verifier
    from app.agents.planner import plan_next_post
    from app.agents.generator import generate_post

    plan = plan_next_post()

    if not plan:
        print("No eligible topic found. Run the planner first to seed roadmap data.")
    else:
        draft = generate_post(
            topic=plan["topic"],
            subtopic=plan["subtopic"],
            notes=plan["notes"],
            past_posts=plan["past_posts"],
        )

        print("=" * 60)
        print("DRAFT UNDER REVIEW")
        print("=" * 60)
        print(draft)
        print("=" * 60)

        result = verify_post(plan["topic"], draft)

        print("\nVERIFICATION RESULT")
        print("-" * 60)
        print(json.dumps(result, indent=2))