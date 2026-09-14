import truststore
truststore.inject_into_ssl()

"""
Planner Agent
-------------
Picks the next roadmap topic to post about, from the currently active
roadmap run only, after checking it hasn't already been posted (exact
match) and isn't semantically too similar to a recent post (embedding
similarity - handled separately in the pipeline's retry loop).

Run this file directly to test in isolation:
    python -m app.agents.planner
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.db.models import RoadmapTopic, PostedLog, RoadmapRun
from app.core.config import settings
from app.core.time_utils import to_naive_utc


def get_eligible_topics(db: Session):
    """
    Step 0-3: confirm there's an active roadmap run, fetch its topics + posted log,
    filter out topics already 'posted' unless older than REFRESH_TOPIC_AFTER_DAYS.
    """
    active_run = db.query(RoadmapRun).filter(RoadmapRun.status == "running").first()
    if not active_run:
        return []  # no active roadmap -> nothing eligible

    all_topics = db.query(RoadmapTopic).filter(
        RoadmapTopic.roadmap_run_id == active_run.id
    ).order_by(
        RoadmapTopic.priority.desc(),
        RoadmapTopic.day_or_order.asc()
    ).all()

    eligible = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.REFRESH_TOPIC_AFTER_DAYS)
    cutoff_naive = cutoff.replace(tzinfo=None)

    for t in all_topics:
        posted_entry = (
            db.query(PostedLog)
            .filter(PostedLog.topic == t.topic, PostedLog.status == "posted")
            .order_by(PostedLog.posted_at.desc())
            .first()
        )

        if posted_entry is None:
            eligible.append(t)  # never posted -> eligible
        elif posted_entry.posted_at and to_naive_utc(posted_entry.posted_at) < cutoff_naive:
            eligible.append(t)  # posted long ago -> eligible for a "refresher" post
        # else: skip, already posted recently

    return eligible


def pick_next_topic(db: Session):
    """
    Step 4: pick the next eligible topic (priority first, then sequence order).
    """
    eligible = get_eligible_topics(db)
    return eligible[0] if eligible else None


def get_past_context_for_topic(db: Session, topic: str, limit: int = 3):
    """
    Step 5: pull past posts on this topic (if any) so the Generator can
    avoid repeating the same angle/phrasing.
    """
    return (
        db.query(PostedLog)
        .filter(PostedLog.topic == topic)
        .order_by(PostedLog.created_at.desc())
        .limit(limit)
        .all()
    )


def plan_next_post():
    """
    Main entry point the daily scheduler will call.
    Returns a dict ready to hand off to the Generator Agent, or None if
    nothing is eligible (no active run, or roadmap fully covered).
    """
    db = SessionLocal()
    try:
        topic_row = pick_next_topic(db)
        if not topic_row:
            return None

        past_posts = get_past_context_for_topic(db, topic_row.topic)

        return {
            "topic": topic_row.topic,
            "subtopic": topic_row.subtopic,
            "notes": topic_row.notes,
            "past_posts": [p.content_text for p in past_posts],
        }
    finally:
        db.close()


if __name__ == "__main__":
    # Quick isolated test - run: python -m app.agents.planner
    # Note: this no longer auto-seeds sample topics, since topics must now
    # belong to an active RoadmapRun (created via the dashboard or
    # roadmap_run_service.start_new_run()).
    init_db()

    result = plan_next_post()
    print("Next topic to post about:")
    print(result)