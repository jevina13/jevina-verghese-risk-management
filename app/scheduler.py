from apscheduler.schedulers.background import BackgroundScheduler
from app.services.metrics import calculate_risk_metrics
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        calculate_risk_metrics,
        'interval',
        minutes=30,
        id='risk_metrics_job',
        replace_existing=True,
        next_run_time=datetime.now()  # 👈 runs immediately + every 30 min
    )
    scheduler.start()
    logger.info("📅 Scheduler started: first run NOW, then every 30 minutes.")
    return scheduler
