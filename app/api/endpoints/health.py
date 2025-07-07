
from fastapi import APIRouter
import logging

router = APIRouter()

# Global task reference
background_task = None

# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@router.get("/health")
def health_check():
    response = {
        "status": "ok",
        "background_task": "running" if background_task and not background_task.done() else "inactive"
    }

    logger.info(f"GET /health/  - {response}")
    return response
