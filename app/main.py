from pathlib import Path

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


@app.on_event("startup")
async def startup_event() -> None:
    await init_models()


@app.get("/miniapp", response_class=HTMLResponse)
async def miniapp_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/miniapp/property", response_class=HTMLResponse)
async def miniapp_property(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("property.html", {"request": request})


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}
