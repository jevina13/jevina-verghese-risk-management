
from fastapi import APIRouter, Request
import logging

router = APIRouter()


# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Health check endpoint to verify service status and scheduled jobs
@router.get("/health")
def health_check(request: Request):
    scheduler = getattr(request.app.state, "scheduler", None)
    jobs = scheduler.get_jobs() if scheduler else []
    response = {
        "status": "ok",
        "scheduled_jobs": [job.id for job in jobs]
    }
    logger.info(f"GET /health/  - {response}")
    return response
