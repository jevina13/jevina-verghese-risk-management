from fastapi import APIRouter, HTTPException, Path
from app.models import Account, Trade, RiskMetric
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import app.models as models
from app.db.database import get_db
from app.core.config import settings
import app.schemas.schemas as schemas
import app.risk_utils.calculations as calculations
import logging

router = APIRouter()

# Global task reference
background_task = None

# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@router.get("/risk-report/{account_login}", response_model=schemas.RiskReport)
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


@router.get("/risk/user/{user_id}", response_model=schemas.RiskReport)
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

    metrics = calculations.calculate_metrics(trades)
    risk_score = calculations.calculate_risk_score(metrics)
    risk_signals = calculations.generate_risk_signals(metrics)

    response = {
        "trading_account_login": user_id,
        "risk_signals": risk_signals,
        "risk_score": risk_score,
        "last_trade_at": metrics['last_trade_at']
    }

    logger.info(f"GET /risk/user/{user_id} - {response}")
    return response


@router.get("/risk/challenge/{challenge_id}", response_model=schemas.RiskReport)
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

    metrics = calculations.calculate_metrics(trades)
    risk_score = calculations.calculate_risk_score(metrics)
    risk_signals = calculations.generate_risk_signals(metrics)

    response = {
        "trading_account_login": challenge_id,
        "risk_signals": risk_signals,
        "risk_score": risk_score,
        "last_trade_at": metrics['last_trade_at']
    }

    logger.info(f"GET /risk/challenge/{challenge_id} - {response}")
    return response
