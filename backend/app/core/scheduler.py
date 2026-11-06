"""
SIH 2026 — PS26103 | APScheduler Automated Pipeline Trigger
===========================================================
Schedules recurring batch jobs for MoSPI infrastructure data ingestion:
- Runs data ingestion & hydration on the 1st of every month at 06:00 AM IST.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from backend.app.tasks.ingestion import run_ingestion_pipeline

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def scheduled_monthly_ingestion():
    """Wrapper function invoked by APScheduler."""
    logger.info("APScheduler: Triggering monthly data ingestion pipeline...")
    try:
        # If celery worker is running, dispatch to celery; otherwise run directly
        run_ingestion_pipeline.delay()
    except Exception as e:
        logger.warning(f"Celery dispatch failed ({e}). Executing ingestion pipeline synchronously...")
        run_ingestion_pipeline()


def start_scheduler():
    """Initializes and starts the background scheduler."""
    if not scheduler.running:
        # Schedule for the 1st of every month at 06:00 AM IST
        scheduler.add_job(
            scheduled_monthly_ingestion,
            trigger=CronTrigger(day=1, hour=6, minute=0, timezone="Asia/Kolkata"),
            id="monthly_data_ingestion",
            name="Monthly MoSPI Infrastructure Report Ingestion",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler started: 'monthly_data_ingestion' job scheduled (1st of month @ 06:00 IST).")


def shutdown_scheduler():
    """Gracefully shuts down the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")


if __name__ == "__main__":
    logger.info("Starting standalone APScheduler service...")
    start_scheduler()
    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        shutdown_scheduler()

