# src/validators/format_validator.py
"""Общий валидатор форматирования документов."""

from typing import Any
from pathlib import Path
from docx.document import Document

from src.schemas import ReportError, ValidationReport, ReportSummary, ErrorLocation
from src.validators.font_validator import check_font_formatting
from datetime import datetime, timedelta


def validate_format(docx_path: str, rules: dict[str, Any]) -> ValidationReport:
    """
    Выполняет полную валидацию форматирования DOCX-документа.
    
    Args:
        docx_path: Путь к DOCX-файлу.
        rules: Словарь с правилами валидации.
    
    Returns:
        ValidationReport с результатами проверки.
    """
    doc = Document(docx_path)
    all_errors: list[ReportError] = []
    
    # Запускаем все проверки
    all_errors.extend(check_font_formatting(doc, rules))
    # TODO: добавить другие валидаторы по мере реализации
    
    # Подсчитываем статистику
    formatting_errors = len([e for e in all_errors if e.type == "formatting"])
    style_errors = len([e for e in all_errors if e.type == "style"])
    citation_errors = len([e for e in all_errors if e.type == "citation_check"])
    
    report = ValidationReport(
        doc_id=Path(docx_path).name,
        created_at=datetime.now(),
        session_expires_at=datetime.now() + timedelta(hours=1),
        summary=ReportSummary(
            total_errors=len(all_errors),
            formatting=formatting_errors,
            style=style_errors,
            citations=citation_errors
        ),
        errors=all_errors
    )
    
    return report
