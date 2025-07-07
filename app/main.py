from app.models import Base, Account, Trade, RiskMetric
from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
import app.schemas as schemas
import app.utils as utils
from app.config import settings
import app.models as models
from datetime import datetime, timedelta
from tqdm import tqdm
import requests
import logging
import traceback
import asyncio


# Global task reference
background_task = None

# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 📋 Lifespan to setup DB & run metrics once
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import engine

    logger.info("🔷 Creating tables & index …")
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))  # for better concurrency
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trades_login_closed
            ON trades (trading_account_login, closed_at)
        """))

    logger.info("✅ Tables & index ready — calculating risk metrics …")
    calculate_risk_metrics()
    logger.info("🎯 Risk metrics calculation complete.")

    yield


app = FastAPI(lifespan=lifespan)


# 📋 Risk metrics calculation
def calculate_risk_metrics():
    db: Session = next(get_db())
    try:
        accounts = db.query(Account).all()
        logger.info(f"📋 Processing {len(accounts)} accounts…")

        batch_size = 500
        count = 0

        for account in tqdm(accounts, desc="Processing Accounts", unit="acc"):
            trades = (
                db.query(Trade)
                .filter(Trade.trading_account_login == account.login)
                .order_by(Trade.closed_at.desc())
                .limit(settings.WINDOW_SIZE)
                .all()
            )

            if not trades:
                continue

            # 👉 Calculate metrics
            metrics = utils.calculate_metrics(trades)
            risk_score = utils.calculate_risk_score(metrics)
            risk_signals = utils.generate_risk_signals(metrics)

            risk_metric = RiskMetric(
                account_login=account.login,
                timestamp=datetime.utcnow(),
                win_ratio=metrics['win_ratio'],
                profit_factor=metrics['profit_factor'],
                max_drawdown=metrics['max_drawdown'],
                stop_loss_used=metrics['stop_loss_used'],
                take_profit_used=metrics['take_profit_used'],
                hft_count=metrics['hft_count'],
                max_layering=metrics['max_layering'],
                risk_score=risk_score,
                risk_signals=",".join(risk_signals),
                last_trade_at=metrics['last_trade_at']
            )

            db.add(risk_metric)

            count += 1
            if count % batch_size == 0:
                db.commit()
                logger.info(f"🔷 Committed {count} risk metrics")

            # 🚨 Send webhook if risk_score > threshold
            if risk_score > settings.RISK_THRESHOLD:
                send_webhook(account.login, risk_score, risk_signals, metrics['last_trade_at'])

        db.commit()
        logger.info("✅ All risk metrics committed.")
    except Exception as e:
        logger.error(f"🔥 Exception during risk calculation: {e}")
        db.rollback()
    finally:
        db.close()
        logger.debug("DB session closed.")



def send_webhook(account_login: int, score: float, signals: list[str], last_trade: datetime):
    payload = {
        "trading_account_login": account_login,
        "risk_signals": signals,
        "risk_score": score,
        "last_trade_at": last_trade.isoformat() if last_trade else None,
    }
    try:
        response = requests.post(settings.WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        logger.info("Webhook sent - account %s (HTTP %s)", account_login, response.status_code)
    except Exception as e:
        logger.error(f"Webhook FAILED - account{e}")


# API Endpoints
@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")


@app.get("/risk-report/{account_login}", response_model=schemas.RiskReport)
def get_risk_report(account_login: int, db: Session = Depends(get_db)):
    # Get latest risk metric for account
    risk_metric = (db.query(models.RiskMetric)
                 .filter(models.RiskMetric.account_login == account_login)
                 .order_by(models.RiskMetric.timestamp.desc())
                 .first())

    if not risk_metric:
        logger.warning(f"Account not found: {account_login}")
        raise HTTPException(status_code=404, detail="Account not found")

    response = {
        "trading_account_login": account_login,
        "risk_signals": risk_metric.risk_signals.split(",") if risk_metric.risk_signals else [],
        "risk_score": risk_metric.risk_score,
        "last_trade_at": risk_metric.last_trade_at
    }

    logger.info(f"GET /risk-report/{account_login} - {response}")
    return response


@app.post("/admin/update-config")
def update_config(new_config: schemas.ConfigUpdate,
            admin_token: str = Query(..., description="Admin token")):

    if admin_token != "secure_admin_token":
        logger.warning(f"User Unauthorized : Wrong token! {admin_token}")
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Update configuration
    if new_config.window_size is not None:
        settings.WINDOW_SIZE = new_config.window_size
    if new_config.win_ratio_threshold is not None:
        settings.WIN_RATIO_THRESHOLD = new_config.win_ratio_threshold
    if new_config.drawdown_threshold is not None:
        settings.DRAWDOWN_THRESHOLD = new_config.drawdown_threshold
    if new_config.stop_loss_threshold is not None:
        settings.STOP_LOSS_THRESHOLD = new_config.stop_loss_threshold
    if new_config.take_profit_threshold is not None:
        settings.TAKE_PROFIT_THRESHOLD = new_config.take_profit_threshold
    if new_config.risk_threshold is not None:
        settings.RISK_THRESHOLD = new_config.risk_threshold
    if new_config.initial_balance is not None:
        settings.INITIAL_BALANCE = new_config.initial_balance
    if new_config.hft_duration is not None:
        settings.HFT_DURATION = new_config.hft_duration

    logger.info(f"Configuration updated: {new_config.model_dump()}")
    return {"message": f"Configuration updated {new_config}"}


@app.get("/risk/user/{user_id}", response_model=schemas.RiskReport)
def get_user_risk_report(user_id: int = Path(...), db: Session = Depends(get_db)):
    accounts = db.query(models.Account).filter_by(user_id=user_id).all()
    if not accounts:
        logger.warning(f"User ID not found {user_id}.")
        raise HTTPException(status_code=404, detail="User not found")

    account_logins = [a.login for a in accounts]
    trades = (db.query(models.Trade)
                .filter(models.Trade.trading_account_login.in_(account_logins))
                .order_by(models.Trade.closed_at.desc())
                .limit(settings.WINDOW_SIZE)
                .all())

    if not trades:
        logger.warning(f"No trades found for User ID {user_id}. Accounts: {account_logins}")
        raise HTTPException(status_code=404, detail="No trades found for user")

    metrics = utils.calculate_metrics(trades)
    risk_score = utils.calculate_risk_score(metrics)
    risk_signals = utils.generate_risk_signals(metrics)

    response = {
        "trading_account_login": user_id,
        "risk_signals": risk_signals,
        "risk_score": risk_score,
        "last_trade_at": metrics['last_trade_at']
    }

    logger.info(f"GET /risk/user/{user_id} - {response}")
    return response


@app.get("/risk/challenge/{challenge_id}", response_model=schemas.RiskReport)
def get_challenge_risk_report(challenge_id: int = Path(...), db: Session = Depends(get_db)):
    accounts = db.query(models.Account).filter_by(challenge_id=challenge_id).all()
    if not accounts:
        logger.warning(f"Challenge ID not found {challenge_id}.")
        raise HTTPException(status_code=404, detail="Challenge not found")

    account_logins = [a.login for a in accounts]
    trades = (db.query(models.Trade)
                .filter(models.Trade.trading_account_login.in_(account_logins))
                .order_by(models.Trade.closed_at.desc())
                .limit(settings.WINDOW_SIZE)
                .all())

    if not trades:
        logger.warning(f"No trades found for Challenge ID {challenge_id}. Accounts: {account_logins}")
        raise HTTPException(status_code=404, detail="No trades found for challenge")

    metrics = utils.calculate_metrics(trades)
    risk_score = utils.calculate_risk_score(metrics)
    risk_signals = utils.generate_risk_signals(metrics)

    response = {
        "trading_account_login": challenge_id,
        "risk_signals": risk_signals,
        "risk_score": risk_score,
        "last_trade_at": metrics['last_trade_at']
    }

    logger.info(f"GET /risk/challenge/{challenge_id} - {response}")
    return response


@app.get("/health")
def health_check():
    response = {
        "status": "ok",
        "background_task": "running" if background_task and not background_task.done() else "inactive"
    }

    logger.info(f"GET /health/  - {response}")
    return response
