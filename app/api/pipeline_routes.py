import truststore
truststore.inject_into_ssl()

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.services.auth_service import get_current_user
from app.agents.pipeline import run_daily_pipeline

router = APIRouter()


@router.get("/pipeline/trigger-now", response_class=HTMLResponse)
def trigger_now(user: str = Depends(get_current_user)):
    post_log_id = run_daily_pipeline()
    if post_log_id is None:
        return "<h2>No eligible topic found.</h2><p>Roadmap fully covered, no active run, or all topics posted recently.</p>"
    return f"<h2>Pipeline triggered successfully.</h2><p>Draft saved (id={post_log_id}) and approval email sent.</p>"