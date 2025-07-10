from fastapi import FastAPI
from app.core.logging_config import setup_logging
from app.api.routes import include_routers
from app.lifespan import lifespan

logger = setup_logging()

logger.info("🎯 Risk Signal Service starting up…")


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
