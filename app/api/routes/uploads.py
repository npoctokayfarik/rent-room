#я ебал апишки
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("")
async def upload_files(
    file: UploadFile | None = File(default=None),
    files: list[UploadFile] | None = File(default=None),
) -> dict[str, list[str]]:
    incoming = files or ([] if file is None else [file])
    if not incoming:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    urls: list[str] = []
    for item in incoming:
        suffix = Path(item.filename or "").suffix
        name = f"{uuid4().hex}{suffix}"
        destination = upload_dir / name
        async with aiofiles.open(destination, "wb") as out:
            while chunk := await item.read(1024 * 1024):
                await out.write(chunk)
        urls.append(f"/uploads/{name}")

    return {"urls": urls}
