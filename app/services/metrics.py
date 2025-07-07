from app.core import config as settings
from app.db.database import get_db
from app.models import Account, Trade, RiskMetric
from app.services.webhook import send_webhook
from app import utils
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
