from app.models import Base
from dotenv import load_dotenv
from app.db.database import engine
import pandas as pd
import os

load_dotenv(".env")

ACCOUNTS_CSV = os.getenv("ACCOUNTS_CSV_PATH")
TRADES_CSV = os.getenv("TRADES_CSV_PATH")

REPLACE_TABLES = True  # set to False if you want to only append

def validate_columns(df, required_cols, name):
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"{name} CSV missing columns: {missing}")

def load_data():
    # Recreate tables cleanly if needed
    if REPLACE_TABLES:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Load accounts
    if not ACCOUNTS_CSV or not os.path.exists(ACCOUNTS_CSV):
        raise FileNotFoundError(f"Accounts CSV path not found: {ACCOUNTS_CSV}")
    accounts_df = pd.read_csv(ACCOUNTS_CSV)

    validate_columns(accounts_df, ["login", "account_size", "platform", "phase", "user_id", "challenge_id"], "Accounts")

    accounts_df.drop_duplicates(subset="login", inplace=True)

    accounts_df.to_sql("accounts", engine, if_exists="replace" if REPLACE_TABLES else "append", index=False)
    print(f"✅ Loaded {len(accounts_df)} accounts")

    # Load trades
    if not TRADES_CSV or not os.path.exists(TRADES_CSV):
        raise FileNotFoundError(f"Trades CSV path not found: {TRADES_CSV}")
    trades_df = pd.read_csv(TRADES_CSV)

    # Clean up trades
    if "Unnamed: 0" in trades_df.columns:
        trades_df.drop(columns=["Unnamed: 0"], inplace=True)
    trades_df.drop_duplicates(subset="identifier", inplace=True)

    validate_columns(
        trades_df,
        [
            "identifier", "trading_account_login", "opened_at", "closed_at",
            "action", "open_price", "close_price", "lot_size", "profit", "symbol"
        ],
        "Trades"
    )
    
    # Dates
    for col in ["opened_at", "closed_at"]:
        trades_df[col] = pd.to_datetime(trades_df[col], errors="coerce")

    # Types
    trades_df["identifier"] = trades_df["identifier"].astype(str)
    trades_df["trading_account_login"] = trades_df["trading_account_login"].astype(str)

    trades_df.to_sql("trades", engine, if_exists="replace" if REPLACE_TABLES else "append", index=False)
    print(f"✅ Loaded {len(trades_df)} trades")

if __name__ == "__main__":
    load_data()
    print("🚀 Initial data loaded successfully")
