import truststore
truststore.inject_into_ssl()

"""
Pipeline Orchestrator
----------------------
Ties together Planner -> Generator -> Verifier with a scored retry loop,
then saves the result tagged to the currently active roadmap run with an
approval deadline, and sends the approval email.

Logic:
  1. Confirm a roadmap run is currently active; if not, do nothing.
  2. Plan the next eligible topic (Planner Agent, duplicate-check aware).
  3. Generate a draft for that topic.
  4. Verify it (rule-based + LLM critic).
  5. If it passes AND meets the score threshold -> done, use this draft.
     If not -> feed the specific issues/feedback back into the Generator
     and try again, up to MAX_RETRIES times.
  6. Track the best-scoring draft seen across all attempts. If no attempt
     ever meets the threshold, return the best one anyway, flagged so the
     human reviewer knows it didn't fully pass automated QA.
  7. Save the draft to PostedLog (tagged to the active run, with an
     approval deadline) and send the approval email.

Run this file directly to test in isolation:
    python -m app.agents.pipeline
"""
import hashlib
from datetime import datetime, timezone, timedelta

from app.db.database import SessionLocal
from app.db.models import PostedLog, RoadmapRun
from app.services.token_service import create_approval_token
from app.services.email_service import send_approval_email
from app.core.config import settings

from app.agents.planner import plan_next_post
from app.agents.generator import generate_post
from app.agents.verifier import verify_post

MAX_RETRIES = 10
SCORE_THRESHOLD = 8  # out of 10, from the LLM critic


def _build_feedback_text(verification_result: dict) -> str:
    """
    Turns a failed verification result into a plain-text feedback string
    the Generator can use to fix the next attempt.
    """
    parts = []

    rule_result = verification_result.get("rule_result") or {}
    if rule_result.get("issues"):
        parts.append("Rule-based issues: " + "; ".join(rule_result["issues"]))

    critic_result = verification_result.get("critic_result") or {}
    if critic_result.get("feedback"):
        parts.append(f"Editor feedback (score {critic_result.get('score', '?')}/10): {critic_result['feedback']}")

    return "\n".join(parts) if parts else "General quality issue - please improve clarity and specificity."


def generate_verified_post(topic: str, subtopic: str = "", notes: str = "", past_posts: list = None) -> dict:
    """
    Main entry point: runs the generate -> verify -> retry loop for a single topic.

    Returns a dict:
      {
        "draft": <best draft text>,
        "attempts": <number of attempts made>,
        "final_verification": <verification result dict for the returned draft>,
        "met_threshold": <bool - True if this draft passed AND scored >= SCORE_THRESHOLD>,
      }
    """
    best_draft = None
    best_score = -1
    best_verification = None
    revision_feedback = ""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n--- Attempt {attempt}/{MAX_RETRIES} ---")

        draft = generate_post(
            topic=topic,
            subtopic=subtopic,
            notes=notes,
            past_posts=past_posts,
            revision_feedback=revision_feedback,
        )

        verification = verify_post(topic, draft)

        critic_score = (verification.get("critic_result") or {}).get("score", 0)
        rule_passed = (verification.get("rule_result") or {}).get("passed", False)

        # Rule failures get score 0 (never let a broken draft "win" on score alone)
        effective_score = critic_score if rule_passed else 0

        print(f"Rule-based passed: {rule_passed} | Critic score: {critic_score}/10 | Overall passed: {verification['passed']}")

        if effective_score > best_score:
            best_score = effective_score
            best_draft = draft
            best_verification = verification

        if verification["passed"] and critic_score >= SCORE_THRESHOLD:
            print(f"Threshold met on attempt {attempt} (score {critic_score}/10). Stopping loop.")
            return {
                "draft": draft,
                "attempts": attempt,
                "final_verification": verification,
                "met_threshold": True,
            }

        # Prepare feedback for the next attempt
        revision_feedback = _build_feedback_text(verification)

    print(f"\nMax retries reached. Returning best draft seen (score {best_score}/10) - flagged for extra scrutiny.")
    return {
        "draft": best_draft,
        "attempts": MAX_RETRIES,
        "final_verification": best_verification,
        "met_threshold": False,
    }


def run_daily_pipeline():
    """
    Full daily flow: Check active run -> Plan -> Generate+Verify (scored retry loop) ->
    save as 'pending_approval' in DB (tagged to the active run, with an approval deadline) ->
    send approval email.
    """
    db_check = SessionLocal()
    active_run = db_check.query(RoadmapRun).filter(RoadmapRun.status == "running").first()
    db_check.close()

    if not active_run:
        print("No active roadmap is running. Upload a roadmap via the dashboard to begin.")
        return None

    plan = plan_next_post()
    if not plan:
        print("No eligible topic found - roadmap fully covered or all topics posted recently.")
        return None

    print(f"Topic: {plan['topic']} / {plan['subtopic']}")

    result = generate_verified_post(
        topic=plan["topic"],
        subtopic=plan["subtopic"],
        notes=plan["notes"],
        past_posts=plan["past_posts"],
    )

    draft = result["draft"]
    content_hash = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    deadline = datetime.now(timezone.utc) + timedelta(hours=settings.APPROVAL_TIMEOUT_HOURS)

    db = SessionLocal()
    try:
        post_log = PostedLog(
            topic=plan["topic"],
            subtopic=plan["subtopic"],
            content_text=draft,
            content_hash=content_hash,
            status="pending_approval",
            roadmap_run_id=active_run.id,
            approval_deadline=deadline,
        )
        db.add(post_log)
        db.commit()
        db.refresh(post_log)

        token = create_approval_token(post_log.id)
        post_log.approval_token = token
        db.commit()

        approve_url = f"{settings.APP_BASE_URL}/approve?token={token}"
        reject_url = f"{settings.APP_BASE_URL}/reject?token={token}"

        score = (result["final_verification"].get("critic_result") or {}).get("score", 0)

        send_approval_email(
            post_log_id=post_log.id,
            topic=plan["topic"],
            subtopic=plan["subtopic"],
            draft_text=draft,
            score=score,
            attempts=result["attempts"],
            met_threshold=result["met_threshold"],
            approve_url=approve_url,
            reject_url=reject_url,
        )

        print(f"\nDraft saved (id={post_log.id}) and approval email sent.")
        return post_log.id
    finally:
        db.close()


if __name__ == "__main__":
    # Full pipeline run - plans, generates, verifies, saves to DB, and emails for approval
    run_daily_pipeline()