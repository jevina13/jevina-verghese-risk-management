import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Risk calculation parameters
    RISK_THRESHOLD = 80
    RISK_WINDOW_MINUTES = 60  # 1 hour
    WINDOW_SIZE = 100  # Last N trades for rolling window
    INITIAL_BALANCE = 100000
    HFT_DURATION = 60  # Seconds
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    # Signal thresholds
    WIN_RATIO_THRESHOLD = 0.3
    DRAWDOWN_THRESHOLD = 0.5
    STOP_LOSS_THRESHOLD = 0.5
    TAKE_PROFIT_THRESHOLD = 0.3


settings = Settings()
