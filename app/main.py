import truststore
truststore.inject_into_ssl()
from fastapi.staticfiles import StaticFiles
"""
FastAPI app entrypoint. Run with:
    python -m uvicorn app.main:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.db.database import init_db
from app.services.auth_service import decode_session_token
from app.api import approval_routes, auth_routes, user_auth_routes, pipeline_routes, dashboard_routes
from app.scheduler import start_scheduler

app = FastAPI(title="OnePostLnkdn Assistant")
app.mount("/static", StaticFiles(directory="static"), name="static")
init_db()

app.include_router(approval_routes.router)
app.include_router(auth_routes.router)
app.include_router(user_auth_routes.router)
app.include_router(pipeline_routes.router)
app.include_router(dashboard_routes.router)


@app.get("/")
def root(request: Request):
    token = request.cookies.get("session_token")
    if token:
        result = decode_session_token(token)
        if result["valid"]:
            return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.on_event("startup")
def on_startup():
    if settings.ENABLE_INPROCESS_SCHEDULER:
        start_scheduler()