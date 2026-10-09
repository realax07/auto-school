"""FastAPI-приложение (sdd.md §2): сборка create_app, роутеры, статика,
/api/health, init_db через lifespan (задача 4.2).

Статика: / → frontend/index.html; /registered, /admin-login,
/admin-dashboard → одноименные html; остальное — из frontend/ по пути.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

import backend.db as db
from backend.admin import router as admin_router
from backend.auth import router as auth_router
from backend.register import router as register_router

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

_PAGE_ROUTES = {
    "/": "index.html",
    "/registered": "registered.html",
    "/admin-login": "admin-login.html",
    "/admin-dashboard": "admin-dashboard.html",
    "/cabinet": "cabinet.html",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Auto School API", lifespan=lifespan)
    app.include_router(register_router)
    app.include_router(admin_router)
    app.include_router(auth_router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    for route, filename in _PAGE_ROUTES.items():
        def _page(filename: str = filename):
            path = FRONTEND_DIR / filename
            if not path.is_file():
                raise HTTPException(status_code=404)
            return FileResponse(path, media_type="text/html; charset=utf-8")

        app.get(route)(_page)

    return app


app = create_app()
