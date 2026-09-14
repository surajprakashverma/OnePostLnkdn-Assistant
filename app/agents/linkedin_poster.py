import truststore
truststore.inject_into_ssl()

"""
LinkedIn Poster Agent
----------------------
Scans the PostedLog table for posts with status == "approved" and
publishes them to LinkedIn, then updates their status to "posted"
(or "publish_failed" if the API call fails, so it can be retried
or investigated instead of silently disappearing).

Run this file directly to test in isolation:
    python -m app.agents.linkedin_poster
"""
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.db.models import PostedLog
from app.services.linkedin_service import publish_post


def publish_approved_posts():
    db = SessionLocal()
    try:
        approved_posts = db.query(PostedLog).filter(PostedLog.status == "approved").all()

        if not approved_posts:
            print("No approved posts waiting to be published.")
            return []

        results = []
        for post in approved_posts:
            print(f"\nPublishing post id={post.id} (topic: {post.topic})...")
            result = publish_post(post.content_text)

            if result["success"]:
                post.status = "posted"
                post.linkedin_post_urn = result["post_urn"]
                post.posted_at = datetime.now(timezone.utc)
                db.commit()
                print(f"Published successfully. LinkedIn post URN: {result['post_urn']}")
            else:
                post.status = "publish_failed"
                db.commit()
                print(f"Publish failed: {result['error']}")

            results.append({"post_id": post.id, "result": result})

        return results
    finally:
        db.close()


if __name__ == "__main__":
    publish_approved_posts()