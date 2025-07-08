from app.core.config import settings
from app.db.database import get_db
from app.models import Account, Trade, RiskMetric
from app.services.webhook import send_webhook
from app.risk_utils import calculations
from sqlalchemy.orm import Session
from datetime import datetime
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


def calculate_risk_metrics():
    """
    Computes and stores risk metrics for all accounts.
    """
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
            metrics = calculations.calculate_metrics(trades)
            risk_score = calculations.calculate_risk_score(metrics)
            risk_signals = calculations.generate_risk_signals(metrics)

            # TODO: cHEck this
            # Check if risk metric already exists for this account
            existing_metric = db.query(RiskMetric).filter(RiskMetric.account_login == account.login).first()

            if existing_metric:
                # Update existing record
                existing_metric.timestamp = datetime.now()
                existing_metric.win_ratio = metrics['win_ratio']
                existing_metric.profit_factor = metrics['profit_factor']
                existing_metric.max_drawdown = metrics['max_drawdown']
                existing_metric.stop_loss_used = metrics['stop_loss_used']
                existing_metric.take_profit_used = metrics['take_profit_used']
                existing_metric.hft_count = metrics['hft_count']
                existing_metric.max_layering = metrics['max_layering']
                existing_metric.risk_score = risk_score
                existing_metric.risk_signals = ",".join(risk_signals)
                existing_metric.last_trade_at = metrics['last_trade_at']
            else:
                # Insert a new record
                risk_metric = RiskMetric(
                    account_login=account.login,
                    timestamp=datetime.now(),
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
