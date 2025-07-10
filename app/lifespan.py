from contextlib import asynccontextmanager
from app.db.database import engine
from app.scheduler import start_scheduler
from sqlalchemy import text
from app.models import Base
import logging
import socket

logger = logging.getLogger(__name__)


# FastAPI lifespan manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app):
    # 🟢 Startup: DB setup
    logger.info("🔷 Creating tables & index …")
    Base.metadata.create_all(bind=engine)
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    with engine.begin() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trades_login_closed
            ON trades (trading_account_login, closed_at)
        """))

    # 🚀 Start APScheduler
    scheduler = start_scheduler()
    app.state.scheduler = scheduler

    logger.info("✅ Application is ready to serve")
    if local_ip:
        logger.info(f"   → Service running on http://{local_ip}:8000 (on your LAN)")
    else:   
        logger.info("   → Service running on http://127.0.0.1:8000 (localhost)")

    yield

    # 🛑 Shutdown
    logger.info("🛑 Application shutting down …")
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()
        logger.info("✅ Scheduler stopped cleanly.")
