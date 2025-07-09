Risk Signal Microservice
---

A FastAPI-based microservice to calculate and serve risk metrics for trading accounts.
The service computes risk metrics, persists them in a database, and exposes APIs to query them.
It also schedules risk calculations to run periodically and sends webhook notifications if risk thresholds are breached.

 **Project Structure**

```
.
├── app/                     # Application modules
│   ├── api/                 # API routes
│   ├── core/                # Core settings & configs
│   ├── db/                  # Database connection and helpers
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── risk_utils/          # Risk calculation logic
│   ├── services/            # Service layer (metrics, webhook)
│   ├── main.py              # FastAPI entry point
│   ├── lifespan.py          # App startup & shutdown logic
│   ├── scheduler.py         # APScheduler job scheduler
│   └── __init__.py
├── test_data/               # Sample CSVs for testing
│   ├── test_task_accounts.csv
│   ├── test_task_trades.csv
│   └── test_task_trades_short.csv
├── load_data.py             # Script to load test data into DB
├── risk_signal.db           # SQLite database
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── .env.example             # Example environment file
├── README.md                # Project documentation
├── .gitignore
└── risk_service.log         # Application logs

```
---

**Setup & Installation**

✅ Clone the repository
git clone <repo-url>
cd jevina-verghese-risk-management

✅ Create & activate virtual environment
python -m venv venv
source venv/bin/activate       # on Linux/Mac
venv\Scripts\activate          # on Windows

✅ Install dependencies:
pip install -r requirements.txt

✅ Create a .env file in the root directory with the following keys:
      *ACCOUNTS_CSV_PATH*
      *TRADES_CSV_PATH*
      *WEBHOOK_URL*
      *SQLALCHEMY_DATABASE_URL*
      *SECURITY_TOKEN*

✅ Set up environment variables:
Copy the .env.example file to .env

✅ Populate the database with the initial trade and account data:
     run - *python initial_data_load.py*
✅ Run the service:
     *uvicorn main:app --reload*

Once running:

📄 Swagger Docs: http://127.0.0.1:8000/docs

---

**Metrics Calculated**

The service computes the following risk indicators:

1. **Win Ratio** – Ratio of profitable trades to total trades  
2. **Profit Factor** – Ratio of gross profit to gross loss  
3. **Max Relative Drawdown** – Largest peak-to-valley loss assuming $100,000 starting balance  
4. **Stop Loss Used %** – Ratio of trades using a stop-loss  
5. **Take Profit Used %** – Ratio of trades using a take-profit  
6. **HFT Detection** – Count of trades closed in under 1 minute  
7. **Layering Detection** – Max number of concurrent open trades  
8. **Risk Score Calculation**
   - **Individual Risk Score** – Account-based score
   - **User Risk Score** – Aggregated across all accounts under a user
   - **Challenge Risk Score** – Aggregated across all accounts in a challenge

---

| Method | Endpoint                            | Description                             |
|--------|-------------------------------------|-----------------------------------------|
| GET    | `/health`                           | Health check                            |
| GET    | `/risk-report/{account_login}`      | Risk score for a trading account        |
| GET    | `/risk/user/{user_id}`              | Aggregated risk score for a user        |
| GET    | `/risk/challenge/{challenge_id}`    | Aggregated risk score for a challenge   |
| POST   | `/admin/update-config`              | Update thresholds dynamically           |


---
