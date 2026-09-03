"""PDF render helper for the Quadrum n8n expense workflow.

Converts PDF pages to PNG images so a vision LLM can read invoices whose
text layer is missing or unreliable (scans, photos exported to PDF).

Uses PyMuPDF, which ships prebuilt wheels - no poppler or other system
packages required, so it runs on a plain python:3.11-slim container.

Endpoints:
  GET  /health          -> {"status": "ok"}
  POST /pdf-to-images   -> multipart upload, field name "file"
  POST /pdf-to-images-base64 -> JSON {"base64": "...", "dpi": 200, "max_pages": 5}

Both conversion endpoints return:
  {"pageCount": 3, "returnedPages": 3,
   "images": [{"page": 1, "mimeType": "image/png", "base64": "..."}]}
"""

import base64

import fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="n8n PDF Render Helper", version="1.0.0")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_DPI = 200
MAX_DPI = 400
DEFAULT_MAX_PAGES = 5
HARD_PAGE_CAP = 20


def render(pdf_bytes: bytes, dpi: int, max_pages: int) -> dict:
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF payload")
    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF larger than 50 MB")

    dpi = max(72, min(int(dpi or DEFAULT_DPI), MAX_DPI))
    max_pages = max(1, min(int(max_pages or DEFAULT_MAX_PAGES), HARD_PAGE_CAP))

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Not a readable PDF: {exc}")

    try:
        total_pages = doc.page_count
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        images = []
        for index in range(min(total_pages, max_pages)):
            pixmap = doc.load_page(index).get_pixmap(matrix=matrix)
            images.append({
                "page": index + 1,
                "mimeType": "image/png",
                "base64": base64.b64encode(pixmap.tobytes("png")).decode("ascii"),
            })
    finally:
        doc.close()

    return {"pageCount": total_pages, "returnedPages": len(images), "images": images}


class Base64Request(BaseModel):
    base64: str
    dpi: int = DEFAULT_DPI
    max_pages: int = DEFAULT_MAX_PAGES


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "pymupdf": fitz.__doc__.strip() if fitz.__doc__ else "loaded"}


@app.post("/pdf-to-images")
async def pdf_to_images(
    file: UploadFile = File(...),
    dpi: int = Form(DEFAULT_DPI),
    max_pages: int = Form(DEFAULT_MAX_PAGES),
) -> dict:
    return render(await file.read(), dpi, max_pages)


@app.post("/pdf-to-images-base64")
def pdf_to_images_base64(payload: Base64Request) -> dict:
    raw = payload.base64.split(",", 1)[-1] if payload.base64.startswith("data:") else payload.base64
    try:
        pdf_bytes = base64.b64decode(raw, validate=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {exc}")
    return render(pdf_bytes, payload.dpi, payload.max_pages)
