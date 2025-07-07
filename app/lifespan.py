from contextlib import asynccontextmanager
from app.db.database import engine
from sqlalchemy import text
from app.db.database import Base

class Account(Base):
    __tablename__ = "accounts"
    ...
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    logger.info("🔷 Creating tables & index …")
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trades_login_closed
            ON trades (trading_account_login, closed_at)
        """))

    yield
