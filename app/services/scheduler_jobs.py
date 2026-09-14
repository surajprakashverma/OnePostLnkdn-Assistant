import truststore
truststore.inject_into_ssl()

from app.db.database import SessionLocal
from app.db.models import PostedLog
from app.core.time_utils import to_naive_utc, now_naive_utc


def auto_reject_expired_approvals():
    db = SessionLocal()
    try:
        now_naive = now_naive_utc()
        candidates = (
            db.query(PostedLog)
            .filter(PostedLog.status == "pending_approval")
            .filter(PostedLog.approval_deadline.isnot(None))
            .all()
        )
        expired = [p for p in candidates if to_naive_utc(p.approval_deadline) < now_naive]

        for post in expired:
            post.status = "auto_rejected"
            print(f"Auto-rejected post id={post.id} (topic: {post.topic}) - approval window expired.")

        if expired:
            db.commit()

        return len(expired)
    finally:
        db.close()


if __name__ == "__main__":
    count = auto_reject_expired_approvals()
    print(f"Checked expired approvals. {count} post(s) auto-rejected.")