import requests
import logging
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

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
        logger.info("✅ Webhook sent - account %s (HTTP %s)", account_login, response.status_code)
    except Exception as e:
        logger.error(f"🚨 Webhook FAILED for account {account_login}: {e}")
