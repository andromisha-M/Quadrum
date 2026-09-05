"""Document render helper for the Quadrum n8n expense workflow.

Turns documents into page images so a vision LLM can read invoices that
cannot be read as text: scans, photos exported to PDF, and Office files
(.doc, .docx, .xls, .xlsx, .odt, .rtf) that no text extractor handles well.

PDF rasterising uses PyMuPDF (prebuilt wheels, no system deps). Office
conversion shells out to LibreOffice headless, which the image installs.

Endpoints:
  GET  /health                  -> {"status": "ok", ...}
  POST /pdf-to-images           -> multipart upload, field name "file"
  POST /pdf-to-images-base64    -> JSON {"base64", "dpi", "max_pages"}
  POST /office-to-images-base64 -> JSON {"base64", "filename", "dpi", "max_pages"}

Every conversion endpoint returns:
  {"pageCount": 3, "returnedPages": 3,
   "images": [{"page": 1, "mimeType": "image/png", "base64": "..."}]}
"""

import base64
import io
import os
import pathlib
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List

import fitz
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from pydantic import BaseModel

app = FastAPI(title="n8n Document Render Helper", version="1.1.0")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_DPI = 200
MAX_DPI = 400
DEFAULT_MAX_PAGES = 5
SOFFICE_TIMEOUT = 180
OFFICE_SUFFIXES = {
    ".doc", ".docx", ".docm", ".dot", ".dotx", ".odt", ".rtf", ".txt",
    ".xls", ".xlsx", ".xlsm", ".xlt", ".xltx", ".ods", ".csv",
    ".ppt", ".pptx", ".odp",
}
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


def office_to_pdf(data: bytes, filename: str) -> bytes:
    """Convert an Office/text document to PDF with LibreOffice headless."""
    if not shutil.which("soffice"):
        raise HTTPException(
            status_code=501,
            detail="LibreOffice is not installed in this container - rebuild the image "
                   "(docker compose up -d --build) to enable Office conversion.",
        )

    suffix = pathlib.Path(filename or "").suffix.lower()
    if suffix not in OFFICE_SUFFIXES:
        # Unknown extension: let LibreOffice sniff it, but give it something to work with.
        suffix = suffix or ".doc"

    with tempfile.TemporaryDirectory() as tmp:
        source = os.path.join(tmp, "input" + suffix)
        with open(source, "wb") as handle:
            handle.write(data)

        # LibreOffice needs a writable HOME of its own, or it silently does nothing.
        env = dict(os.environ, HOME=tmp)
        try:
            proc = subprocess.run(
                ["soffice", "--headless", "--norestore", "--nolockcheck",
                 "--convert-to", "pdf", "--outdir", tmp, source],
                capture_output=True, timeout=SOFFICE_TIMEOUT, env=env,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="LibreOffice timed out converting this file")

        produced = os.path.join(tmp, "input.pdf")
        if not os.path.exists(produced):
            detail = (proc.stderr or proc.stdout or b"").decode("utf-8", "replace")[:400]
            raise HTTPException(
                status_code=422,
                detail=f"LibreOffice could not convert this file ({suffix or 'no extension'}): {detail}",
            )
        with open(produced, "rb") as handle:
            return handle.read()


class Base64Request(BaseModel):
    base64: str
    dpi: int = DEFAULT_DPI
    max_pages: int = DEFAULT_MAX_PAGES


class OfficeRequest(Base64Request):
    filename: str = ""


def decode_payload(value: str) -> bytes:
    raw = value.split(",", 1)[-1] if value.startswith("data:") else value
    try:
        return base64.b64decode(raw, validate=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {exc}")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "pymupdf": fitz.__doc__.strip() if fitz.__doc__ else "loaded",
        "libreoffice": bool(shutil.which("soffice")),
    }


@app.post("/pdf-to-images")
async def pdf_to_images(
    file: UploadFile = File(...),
    dpi: int = Form(DEFAULT_DPI),
    max_pages: int = Form(DEFAULT_MAX_PAGES),
) -> dict:
    return render(await file.read(), dpi, max_pages)


@app.post("/pdf-to-images-base64")
def pdf_to_images_base64(payload: Base64Request) -> dict:
    return render(decode_payload(payload.base64), payload.dpi, payload.max_pages)


SHEET_COLUMNS = [
    ("Seller / Service Provider", 42, "text"),
    ("Description", 40, "text"),
    ("Net Cost", 16, "money"),
    ("VAT", 14, "money"),
    ("Date", 14, "text"),
    ("Project", 22, "text"),
    ("", 3, "spacer"),
    (" ", 3, "spacer"),
    ("  ", 3, "spacer"),
    ("   ", 3, "spacer"),
    ("TOTAL NET", 18, "money"),
]
ACCENT = "1A3D6D"
BAND = "F7F8FA"
TOTAL_BG = "EEF3FA"
MONEY_FORMAT = "#,##0.00"


class RowsRequest(BaseModel):
    rows: List[Dict[str, Any]] = []
    totalNet: float = 0
    projectName: str = "Expenses"


@app.post("/rows-to-xlsx")
def rows_to_xlsx(payload: RowsRequest) -> Response:
    """Render the expense rows as a formatted .xlsx - openpyxl can style, SheetJS cannot."""
    wb = Workbook()
    ws = wb.active
    ws.title = (payload.projectName or "Expenses")[:31]

    thin = Side(style="thin", color="DFE3E8")
    header_font = Font(bold=True, color="FFFFFF", size=10)
    header_fill = PatternFill("solid", fgColor=ACCENT)
    band_fill = PatternFill("solid", fgColor=BAND)
    total_fill = PatternFill("solid", fgColor=TOTAL_BG)

    # Header row
    for index, (title, width, _kind) in enumerate(SHEET_COLUMNS, start=1):
        cell = ws.cell(row=1, column=index, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.row_dimensions[1].height = 26
    ws.freeze_panes = "A2"

    # Data rows
    for offset, row in enumerate(payload.rows):
        excel_row = 2 + offset
        banded = offset % 2 == 1
        for index, (title, _width, kind) in enumerate(SHEET_COLUMNS, start=1):
            if kind == "spacer" or title == "TOTAL NET":
                value = None
            elif kind == "money":
                try:
                    value = float(row.get(title, 0) or 0)
                except (TypeError, ValueError):
                    value = 0.0
            else:
                value = row.get(title, "")
            cell = ws.cell(row=excel_row, column=index, value=value)
            cell.border = Border(bottom=thin)
            if banded:
                cell.fill = band_fill
            if kind == "money":
                cell.number_format = MONEY_FORMAT
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    # Running total, anchored in K away from the data
    total_column = len(SHEET_COLUMNS)
    total_cell = ws.cell(row=2, column=total_column, value=float(payload.totalNet or 0))
    total_cell.number_format = MONEY_FORMAT
    total_cell.font = Font(bold=True, size=12, color=ACCENT)
    total_cell.fill = total_fill
    total_cell.alignment = Alignment(horizontal="right", vertical="center")
    total_cell.border = Border(left=Side(style="medium", color=ACCENT), bottom=thin)

    buffer = io.BytesIO()
    wb.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="expenses.xlsx"'},
    )


@app.post("/office-to-images-base64")
def office_to_images_base64(payload: OfficeRequest) -> dict:
    """Word/Excel/etc -> PDF -> page images, so the vision model can read it."""
    data = decode_payload(payload.base64)
    if not data:
        raise HTTPException(status_code=400, detail="Empty document payload")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Document larger than 50 MB")
    result = render(office_to_pdf(data, payload.filename), payload.dpi, payload.max_pages)
    result["convertedFrom"] = payload.filename or "(unnamed)"
    return result
