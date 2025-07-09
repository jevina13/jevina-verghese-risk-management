
from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
import app.schemas.schemas as schemas
from dotenv import load_dotenv
import logging
import os


load_dotenv()

router = APIRouter()


# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Admin endpoint to update configuration settings
@router.post("/admin/update-config")
def update_config(new_config: schemas.ConfigUpdate, admin_token: str = Query(..., description="Admin token")):

    TOKEN = os.getenv("TOKEN")
    if admin_token != TOKEN:
        logger.warning(f"User Unauthorized : Wrong token! {admin_token}")
        raise HTTPException(status_code=403, detail="Unauthorized User: Wrong token!")

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
