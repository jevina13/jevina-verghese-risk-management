from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import logging

router = APIRouter()


# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# # API Endpoints
@router.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")
