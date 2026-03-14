from pathlib import Path
import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes.auth import router as auth_router
from app.api.routes.properties import router as properties_router
from app.api.routes.uploads import router as uploads_router
from app.core.config import get_settings
from app.core.database import init_models
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import register_exception_handlers

app = FastAPI(title="RentRoom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

templates = Jinja2Templates(directory="app/web")

app.include_router(properties_router)
app.include_router(uploads_router)
app.include_router(auth_router)
register_exception_handlers(app)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event() -> None:
    last_error: Exception | None = None
    for attempt in range(1, settings.db_startup_retry_count + 1):
        try:
            await init_models()
            return
        except (OSError, SQLAlchemyError) as error:
            last_error = error
            logger.warning(
                "Database init failed (%s/%s): %s",
                attempt,
                settings.db_startup_retry_count,
                error,
            )
            if attempt < settings.db_startup_retry_count:
                await asyncio.sleep(settings.db_startup_retry_delay_seconds)

    msg = (
        "Не удалось подключиться к БД при старте. Проверьте DATABASE_URL и что PostgreSQL запущен. "
        "Для запуска API без fail-fast выставьте DB_FAIL_FAST_ON_STARTUP=false."
    )
    if settings.db_fail_fast_on_startup:
        raise RuntimeError(msg) from last_error

    logger.error(msg)


@app.get("/miniapp", response_class=HTMLResponse)
async def miniapp_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/miniapp/property", response_class=HTMLResponse)
async def miniapp_property(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("property.html", {"request": request})


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}
