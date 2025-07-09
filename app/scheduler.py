from apscheduler.schedulers.background import BackgroundScheduler
from app.services.metrics import calculate_risk_metrics
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def start_scheduler():
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(
        calculate_risk_metrics,
        'interval',
        minutes=600,
        id='risk_metrics_job',
        replace_existing=True,
        next_run_time=datetime.now()  # runs immediately + every interval
    )
    scheduler.start()
    logger.info(f"📅 Scheduler started for job: {job.id} at {job.next_run_time}.")
    return scheduler
