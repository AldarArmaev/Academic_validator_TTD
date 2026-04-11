# src/web/main.py
"""FastAPI веб-сервис для валидации ВКР."""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from docx import Document

from src.schemas import ValidationReport, ReportSummary


app = FastAPI(
    title="ВКР Валидатор",
    description="Сервис для проверки оформления выпускных квалификационных работ",
    version="1.0.0",
)

BASE_DIR   = Path(__file__).parent
RULES_PATH = Path(__file__).parent.parent / "university_rules.json"

with open(RULES_PATH, "r", encoding="utf-8") as f:
    VALIDATION_RULES = json.load(f)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница сервиса."""
    with open(BASE_DIR / "templates" / "index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ─────────────────────────────────────────────────────────────────────────────
# ИСПРАВЛЕНИЕ #1
# Раньше validate_format_from_document передавал summary как словарь, а не
# как объект ReportSummary, что вызывало ошибку сериализации.
# Теперь явно создаём ReportSummary и ValidationReport корректно.
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/validate", response_model=ValidationReport)
async def validate_work(file: UploadFile = File(...)):
    """
    Загрузить файл ВКР (.docx) и получить отчёт об ошибках.
    """
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Загрузите файл в формате .docx",
        )

    try:
        contents  = await file.read()
        doc       = Document(BytesIO(contents))
        report    = _validate_document(doc, VALIDATION_RULES)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}",
        )


def _validate_document(doc: Document, rules: dict) -> ValidationReport:
    """
    Выполняет полную валидацию документа и возвращает ValidationReport.
    """
    from src.validators.font_validator import check_font_formatting
    from src.validators.format_validator import (
        check_paragraph_formatting,
        check_margins,
        validate_structure,
        validate_tables,
        validate_references_format,
        validate_typography_format,
        validate_toc,
        validate_appendix,
        validate_repeated_references,
        validate_volume,
    )

    errors = []
    errors.extend(check_font_formatting(doc, rules))
    errors.extend(check_paragraph_formatting(doc, rules))
    errors.extend(check_margins(doc, rules))
    errors.extend(validate_structure(doc, rules))
    errors.extend(validate_tables(doc, rules))
    errors.extend(validate_references_format(doc, rules))
    errors.extend(validate_typography_format(doc, rules))
    errors.extend(validate_toc(doc, rules))
    errors.extend(validate_appendix(doc, rules))
    errors.extend(validate_repeated_references(doc, rules))
    errors.extend(validate_volume(doc, rules))

    formatting_count = sum(1 for e in errors if e.type == "formatting")
    style_count      = sum(1 for e in errors if e.type == "style")
    citation_count   = sum(1 for e in errors if e.type == "citation_check")

    # ИСПРАВЛЕНИЕ #1: используем Pydantic-модели, а не сырые словари
    return ValidationReport(
        doc_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        summary=ReportSummary(
            total_errors=len(errors),
            formatting=formatting_count,
            style=style_count,
            citations=citation_count,
        ),
        errors=errors,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ВКР Валидатор"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)