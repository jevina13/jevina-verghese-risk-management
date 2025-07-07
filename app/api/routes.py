from fastapi import FastAPI
from app.api.endpoints import root, risk, admin, health


def include_routers(app: FastAPI):
    app.include_router(root.router)
    app.include_router(risk.router)
    app.include_router(admin.router)
    app.include_router(health.router)
