from fastapi import FastAPI
import logging
from app.api.routes import include_routers
from app.lifespan import lifespan


# Setup logging
logging.basicConfig(filename='risk_service.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Main entry point for the FastAPI application
app = FastAPI(
    title="Risk Signal Microservice",
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Jevina Verghese",
        "email": "jevina.ae@gmail.com"
    }
)

include_routers(app)
