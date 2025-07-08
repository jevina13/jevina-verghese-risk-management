from apscheduler.schedulers.background import BackgroundScheduler
from app.services.metrics import calculate_risk_metrics

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        calculate_risk_metrics,
        'interval',
        minutes=15,
        id='risk_metrics_job',
        replace_existing=True
    )
    scheduler.start()
    print("📅 Scheduler started: Metrics every 1 mins")
    return scheduler
