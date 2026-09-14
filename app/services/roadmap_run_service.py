import truststore
truststore.inject_into_ssl()

from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db.models import RoadmapRun, RoadmapTopic, PostedLog
from app.services.roadmap_ingest_service import extract_text_from_file, structure_roadmap


def get_active_run(db):
    return db.query(RoadmapRun).filter(RoadmapRun.status == "running").first()


def get_status():
    db = SessionLocal()
    try:
        active_run = get_active_run(db)
        if not active_run:
            return {"active": False, "message": "No roadmap is currently running."}

        topics = (
            db.query(RoadmapTopic)
            .filter(RoadmapTopic.roadmap_run_id == active_run.id)
            .order_by(RoadmapTopic.day_or_order)
            .all()
        )
        total = len(topics)

        posted_count = (
            db.query(PostedLog)
            .filter(PostedLog.roadmap_run_id == active_run.id, PostedLog.status == "posted")
            .count()
        )
        pending_count = (
            db.query(PostedLog)
            .filter(PostedLog.roadmap_run_id == active_run.id, PostedLog.status == "pending_approval")
            .count()
        )

        posted_topics = {
            p.topic for p in db.query(PostedLog).filter(
                PostedLog.roadmap_run_id == active_run.id, PostedLog.status == "posted"
            ).all()
        }
        next_topic = next((t for t in topics if t.topic not in posted_topics), None)

        return {
            "active": True,
            "run_id": active_run.id,
            "roadmap_filename": active_run.roadmap_filename,
            "total_days": active_run.total_days,
            "started_at": active_run.started_at.isoformat() if active_run.started_at else None,
            "posted_count": posted_count,
            "pending_count": pending_count,
            "total_topics": total,
            "next_topic": f"{next_topic.topic} - {next_topic.subtopic}" if next_topic else "All topics covered",
        }
    finally:
        db.close()
        


def start_new_run(file_path: str, num_days: int):
    db = SessionLocal()
    try:
        existing = get_active_run(db)
        if existing:
            return {
                "success": False,
                "message": f"A roadmap is already running (started {existing.started_at}, day target {existing.total_days}). Stop it first before starting a new one.",
            }

        text = extract_text_from_file(file_path)
        days_list = structure_roadmap(text, num_days)

        new_run = RoadmapRun(
            roadmap_filename=file_path.split("\\")[-1].split("/")[-1],
            total_days=num_days,
            status="running",
        )
        db.add(new_run)
        db.commit()
        db.refresh(new_run)

        for day in days_list:
            db.add(RoadmapTopic(
                day_or_order=day["day"],
                topic=day["topic"],
                subtopic=day.get("subtopic", ""),
                notes=day.get("notes", ""),
                roadmap_run_id=new_run.id,
            ))
        db.commit()

        return {
            "success": True,
            "message": f"New roadmap started with {len(days_list)} days (run id={new_run.id}). Daily posting will begin on schedule.",
            "run_id": new_run.id,
        }
    finally:
        db.close()


def stop_run():
    db = SessionLocal()
    try:
        active_run = get_active_run(db)
        if not active_run:
            return {"success": False, "message": "No roadmap is currently running."}

        active_run.status = "stopped"
        active_run.stopped_at = datetime.now(timezone.utc)
        db.commit()

        return {"success": True, "message": f"Roadmap run id={active_run.id} has been stopped."}
    finally:
        db.close()