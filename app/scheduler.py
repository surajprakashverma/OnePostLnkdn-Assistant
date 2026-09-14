import truststore
truststore.inject_into_ssl()

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.agents.pipeline import run_daily_pipeline
from app.services.scheduler_jobs import auto_reject_expired_approvals
from app.agents.linkedin_poster import publish_approved_posts

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        run_daily_pipeline,
        trigger=CronTrigger(hour=settings.DAILY_TRIGGER_HOUR, minute=settings.DAILY_TRIGGER_MINUTE),
        id="daily_pipeline",
        replace_existing=True,
    )

    scheduler.add_job(
        auto_reject_expired_approvals,
        trigger="interval",
        minutes=15,
        id="auto_reject_check",
        replace_existing=True,
    )

    scheduler.add_job(
        publish_approved_posts,
        trigger="interval",
        minutes=2,
        id="publish_approved_check",
        replace_existing=True,
    )

    scheduler.start()
    print(f"Scheduler started: daily pipeline at {settings.DAILY_TRIGGER_HOUR:02d}:{settings.DAILY_TRIGGER_MINUTE:02d}, auto-reject every 15 min, publish-check every 2 min.")