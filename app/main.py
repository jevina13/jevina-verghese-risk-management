from fastapi import FastAPI
import logging
from app.api.routes import include_routers
from app.scheduler import start_scheduler
from app.lifespan import lifespan


# Global task reference
background_task = None

# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



app = FastAPI(
    title="Risk Signal Microservice",
    version="1.0.0",
    lifespan=lifespan
)

include_routers(app)

scheduler = start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    print("🛑 Scheduler stopped")

