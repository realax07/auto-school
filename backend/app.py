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
from backend.dashboard import router as dashboard_router
from backend.instructor_admin import router as instructor_admin_router
from backend.instructor_availability import router as instructor_availability_router
from backend.instructor_cars import router as instructor_cars_router
from backend.instructor_summary import router as instructor_summary_router
from backend.instructors import router as instructors_router
from backend.register import router as register_router
from backend.reviews import router as reviews_router
from backend.student_marketplace import router as student_marketplace_router
from backend.student_requests import router as student_requests_router

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

_PAGE_ROUTES = {
    "/": "index.html",
    "/registered": "registered.html",
    "/admin-login": "admin-login.html",
    "/admin-dashboard": "admin-dashboard.html",
    "/cabinet": "cabinet.html",
    # Спринт 2, часть 1 (задача 5.1, sdd.md §15.6): рядом с /cabinet
    "/instructors": "instructors.html",
    "/instructors/apply": "instructor-apply.html",
    "/instructors/pending": "instructor-pending.html",
    "/instructors/rejected": "instructor-rejected.html",
    "/instructor/cabinet-stub": "instructor-cabinet-stub.html",
    # Спринт 2, часть 2 (задача 3.1, change add-instructor-cabinet):
    # кабинет инструктора рядом с заглушкой
    "/instructor/dashboard": "instructor-dashboard.html",
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
    # Спринт 2, часть 1 (задача 5.1): заявки и модерация
    app.include_router(instructors_router)
    app.include_router(instructor_admin_router)
    # Спринт 2, часть 2 (задача 3.1): данные кабинета инструктора
    app.include_router(dashboard_router)
    # Спринт 3 (change add-instructor-student-loop, задача 7.1): контур
    # «инструктор ↔ ученик» (правило префиксов design.md: /api/instructor/*
    # — кабинет инструктора, /api/student/* — кабинет ученика)
    app.include_router(instructor_cars_router)
    app.include_router(instructor_availability_router)
    app.include_router(student_marketplace_router)
    app.include_router(reviews_router)
    app.include_router(student_requests_router)
    app.include_router(instructor_summary_router)

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
