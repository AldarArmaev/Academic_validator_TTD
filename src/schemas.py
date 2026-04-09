# src/schemas.py
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class ErrorLocation(BaseModel):
    paragraph_index: int
    structural_path: str              # пример: «Глава 1 > Параграф 1.2»
    chapter: Optional[str] = None


class ReportError(BaseModel):
    id: str                          # уникальный id внутри отчёта
    code: str                        # код требования: "Ф-1", "С-5", "Л-7" и т.д.
    type: Literal["formatting", "style", "citation_check"]
    severity: Literal["error", "warning", "info"]
    location: ErrorLocation
    fragment: str                    # до 100 символов из документа
    rule: str                        # формулировка требования
    rule_citation: str               # цитата из методички: "§4.2, с. 47"
    found_value: str                 # что нашли
    expected_value: str              # что ожидали
    recommendation: str              # инструкция для исправления


class ReportSummary(BaseModel):
    total_errors: int
    formatting: int
    style: int
    citations: int


class ValidationReport(BaseModel):
    doc_id: str
    created_at: datetime
    session_expires_at: datetime
    summary: ReportSummary
    errors: list[ReportError]
