import truststore
truststore.inject_into_ssl()

"""
Approval Routes
---------------
FastAPI endpoints hit when you click Approve/Reject in the email.
Enforces single-use: once a post's status changes from
'pending_approval', clicking the link again shows an already-actioned
message instead of re-processing.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.db.database import SessionLocal
from app.db.models import PostedLog
from app.services.token_service import decode_approval_token

router = APIRouter()


def _get_post(db, post_log_id):
    return db.query(PostedLog).filter(PostedLog.id == post_log_id).first()


@router.get("/approve", response_class=HTMLResponse)
def approve_post(token: str):
    result = decode_approval_token(token)
    if not result["valid"]:
        return f"<h2>❌ Link invalid or expired</h2><p>{result['error']}</p>"

    db = SessionLocal()
    try:
        post = _get_post(db, result["post_log_id"])
        if not post:
            return "<h2>❌ Post not found</h2>"

        if post.status != "pending_approval":
            return f"<h2>⚠️ Already actioned</h2><p>This post's status is already: <strong>{post.status}</strong></p>"

        post.status = "approved"  # Phase 5 (LinkedIn Poster) will watch for this status
        db.commit()

        return f"""
        <h2>✅ Approved!</h2>
        <p>Your post about <strong>{post.topic}</strong> has been approved.
        It will be published to LinkedIn shortly.</p>
        """
    finally:
        db.close()


@router.get("/reject", response_class=HTMLResponse)
def reject_post(token: str):
    result = decode_approval_token(token)
    if not result["valid"]:
        return f"<h2>âŒ Link invalid or expired</h2><p>{result['error']}</p>"

    db = SessionLocal()
    try:
        post = _get_post(db, result["post_log_id"])
        if not post:
            return "<h2>âŒ Post not found</h2>"

        if post.status != "pending_approval":
            return f"<h2>âš ï¸ Already actioned</h2><p>This post's status is already: <strong>{post.status}</strong></p>"

        post.status = "rejected"
        db.commit()

        return f"""
        <h2>❌ Rejected</h2>
        <p>The post about <strong>{post.topic}</strong> was marked as rejected.
        The Planner will retry this same topic on the next run instead of skipping it.</p>
        """
    finally:
        db.close()
