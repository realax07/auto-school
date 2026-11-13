"""FastAPI-приложение (sdd.md §2): сборка create_app, роутеры, статика,
/api/health, init_db через lifespan (задача 4.2).

Статика: / → frontend/index.html; /registered, /admin-login,
/admin-dashboard → одноименные html; остальное — из frontend/ по пути.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

import backend.core.db as db
from backend.auth.admin import router as admin_router
from backend.auth.application_status import router as application_status_router
from backend.auth.auth import router as auth_router
from backend.student.booking import router as booking_router
from backend.instructor.dashboard import router as dashboard_router
from backend.auth.instructor_admin import router as instructor_admin_router
from backend.instructor.instructor_availability import router as instructor_availability_router
from backend.instructor.instructor_cars import router as instructor_cars_router
from backend.instructor.instructor_documents import router as instructor_documents_router
from backend.instructor.instructor_summary import router as instructor_summary_router
from backend.instructor.instructors import router as instructors_router
from backend.policy.policy import router as policy_router
from backend.auth.register import router as register_router
from backend.student.reviews import router as reviews_router
from backend.student.student_marketplace import router as student_marketplace_router
from backend.student.student_requests import router as student_requests_router

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
# Спринт 9 (change add-vue-framework-pilot): артефакты сборки каркаса
# Vue/Vite (ADR-008) — в git не коммитятся, собираются `npm ci && npm run
# build` (Dockerfile frontend-builder, задача 2.2; bare-metal FR-57).
VUE_DIST_DIR = FRONTEND_DIR / "vue" / "dist"

_PAGE_ROUTES = {
    # Спринт 12 (change add-vue-s12-landing-apply, задачи 4.1/4.2): лендинг
    # «/» — каркас Vue (ADR-008, замена монолита целиком: legacy index.html
    # + js/landing.js удалены). Маркер "vue:<вход dist>" — цикл отдачи ниже
    # читает VUE_DIST_DIR (404 при отсутствии dist — паттерн пилота).
    "/": "vue:index.html",
    "/registered": "vue:registered.html",
    "/admin-login": "vue:admin-login.html",
    "/admin-dashboard": "vue:admin-dashboard.html",
    "/cabinet": "vue:cabinet.html",
    # Спринт 2, часть 1 (задача 5.1, sdd.md §15.6): рядом с /cabinet.
    # Спринт 14 (change add-vue-s14-instructor-loop, задачи 4.1/4.2):
    # лендинг инструкторов — каркас Vue (ADR-008, замена монолита целиком:
    # legacy instructors.html + js/instructors.js удалены; последний дубль
    # модалки входа умер — консолидация wiring в shared/loginWiring.js).
    "/instructors": "vue:instructors.html",
    # Спринт 12 (change add-vue-s12-landing-apply, задачи 4.1/4.2): анкета
    # инструктора — каркас Vue (замена монолита целиком: legacy
    # instructor-apply.html + js/apply.js удалены).
    "/instructors/apply": "vue:instructor-apply.html",
    # Спринт 9 (change add-vue-framework-pilot, задача 2.3): пилотная
    # страница /instructors/pending обслуживается каркасом Vue — вход из
    # dist (маршрут ниже, вне словаря); legacy instructor-pending.html
    # удален (замена монолита целиком, FR-86/ОВ-4).
    # Спринт 11 (change add-vue-s11-status-forms, задачи 3.1/3.2): экран
    # отказа и форма отзыва — каркас Vue (ADR-008): значение с маркером
    # "vue:<вход dist>" — цикл отдачи ниже читает VUE_DIST_DIR (404 при
    # отсутствии dist — паттерн пилотного хендлера /instructors/pending).
    "/instructors/rejected": "vue:instructors-rejected.html",
    # Спринт 2, часть 2 (задача 3.1, change add-instructor-cabinet):
    # кабинет инструктора рядом с заглушкой.
    # Спринт 14 (change add-vue-s14-instructor-loop, задачи 4.1/4.2):
    # кабинет инструктора — каркас Vue (замена монолита целиком: legacy
    # instructor-dashboard.html + js/instructor/dashboard-instructor.js
    # удалены); НОВАЯ страница «Мои документы» /instructor/documents —
    # сразу вход каркаса (legacy-монолит НЕ создается — BUG-047).
    "/instructor/dashboard": "vue:instructor-dashboard.html",
    "/instructor/documents": "vue:documents.html",
    # Спринт 3 (change add-instructor-student-loop):
    # выбор инструктора учеником
    "/instructor-choice": "vue:instructor-choice.html",
    # Спринт 4, Партия A (change add-s3-frontend-links): форма отзыва —
    # целевая страница (открывается из раздела «Мои заявки» кабинета);
    # Спринт 11 (change add-vue-s11-status-forms) — перевод на каркас Vue
    # (историческое имя входа сохранено — маршрут /review)
    "/review": "vue:review-form.html",
    # Спринт 9 (change add-personal-data-policy, задача 2.1): публичная
    # страница-оболочка политики персональных данных (текст — из артефакта
    # через GET /api/policy, в HTML его нет — NFR-25)
    "/policy": "vue:policy.html",
    # Спринт 15 — ФИНАЛ миграции (change add-vue-s15-final-migration,
    # задача 5.1): последние шесть маршрутов переведены на каркас Vue
    # (ADR-008, замена монолита целиком: легаси cabinet.html,
    # instructor-choice.html, admin-login.html, admin-dashboard.html,
    # registered.html, policy.html + каталог js/ удалены тем же коммитом,
    # хендлер /js/{path} снят — потребителей нет). В карте НЕ осталось
    # значений без маркера «vue:» — все страницы обслуживаются из dist.
}

# BUG-047 (решение Заказчика 2026-10-17): отдельных standalone-страниц больше
# нет — все разделы живут внутри кабинетов с единым лейаутом (сайдбар слева +
# контент). Старые ссылки получают 301 на соответствующий раздел кабинета
# (хеш открывает таб напрямую).
_PAGE_REDIRECTS = {
    "/my-cars": ("/instructor/dashboard#/my-cars", 301),
    "/my-requests": ("/cabinet#/my-requests", 301),
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
    # Спринт 9 (add-application-status-polling, задачи 2.1/6.1): статус
    # заявки и обмен токена на сессию (правило префиксов design.md:
    # /api/instructors/* — до-сессионный контур заявителя)
    app.include_router(application_status_router)
    # Спринт 2, часть 2 (задача 3.1): данные кабинета инструктора
    app.include_router(dashboard_router)
    # Спринт 3 (change add-instructor-student-loop, задача 7.1): контур
    # «инструктор ↔ ученик» (правило префиксов design.md: /api/instructor/*
    # — кабинет инструктора, /api/student/* — кабинет ученика)
    app.include_router(instructor_cars_router)
    app.include_router(instructor_availability_router)
    # Спринт 5 (change add-booking-docs, задачи 3.1/4.1): «Мои документы»
    # и контур бронирования (правило префиксов design.md соблюдено)
    app.include_router(instructor_documents_router)
    app.include_router(booking_router)
    app.include_router(student_marketplace_router)
    app.include_router(reviews_router)
    app.include_router(student_requests_router)
    app.include_router(instructor_summary_router)
    # Спринт 9 (change add-personal-data-policy, задача 2.1): домен
    # PersonalData — GET /api/policy публичный, БЕЗ префикса роли
    # (политика читается гостями до любой регистрации, механика /api/health)
    app.include_router(policy_router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    # Спринт 9 (change add-vue-framework-pilot, задача 2.3): пилотная
    # страница «Ожидание модерации» — вход каркаса Vue из dist (FR-84/FR-86,
    # ADR-008: base '/vue/'). Маршрут сохранен (NFR-27); отдача тем же
    # сервисом — ADR-001.
    @app.get("/instructors/pending")
    def instructor_pending_page():
        path = VUE_DIST_DIR / "instructors-pending.html"
        if not path.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(path, media_type="text/html; charset=utf-8")

    # Статика каркаса Vue (ADR-008): /vue/assets/* из dist/assets,
    # content-type по суффиксу явно — паттерн /js/{filename}, не зависеть
    # от системных mimetypes; обход каталогов исключен той же проверкой
    # ("/", "..", скрытые). Неизвестный суффикс — 404 (угадывание не
    # вводится; следующие шаги миграции расширяют карту явно).
    @app.get("/vue/assets/{path:path}")
    def vue_asset(path: str):
        if "/" in path or ".." in path or path.startswith("."):
            raise HTTPException(status_code=404)
        media_types = {
            ".js": "application/javascript",
            ".css": "text/css",
        }
        media_type = media_types.get(Path(path).suffix.lower())
        if media_type is None:
            raise HTTPException(status_code=404)
        file_path = VUE_DIST_DIR / "assets" / path
        if not file_path.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(file_path, media_type=media_type)

    for route, filename in _PAGE_ROUTES.items():
        def _page(filename: str = filename):
            # Спринт 11 (change add-vue-s11-status-forms, задача 3.2):
            # маркер "vue:" — страница обслуживается каркасом Vue, вход
            # читается из VUE_DIST_DIR (ADR-008); без собранного dist — 404
            # (паттерн пилотного хендлера). Спринт 15 (задача 5.1): значений
            # без маркера не осталось — все страницы из dist; карта —
            # единственный декларативный реестр маршрутов страниц.
            if filename.startswith("vue:"):
                path = VUE_DIST_DIR / filename[len("vue:"):]
            else:
                path = FRONTEND_DIR / filename
            if not path.is_file():
                raise HTTPException(status_code=404)
            return FileResponse(path, media_type="text/html; charset=utf-8")

        app.get(route)(_page)

    for route, (target, status) in _PAGE_REDIRECTS.items():
        def _redirect(target: str = target, status: int = status):
            return RedirectResponse(target, status_code=status)

        app.get(route)(_redirect)

    return app


app = create_app()
