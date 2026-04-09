# src/validators/__init__.py
"""Модуль валидаторов для ВКР."""

from src.validators.font_validator import check_font_formatting
from src.validators.format_validator import (
    validate_format,
    check_paragraph_formatting,
    check_margins,
    validate_structure,
    validate_tables,
    validate_figures,
    validate_references,
    validate_volume,
    validate_formulas,
    validate_appendices,
    validate_typography,
)

__all__ = [
    "check_font_formatting",
    "validate_format",
    "check_paragraph_formatting",
    "check_margins",
    "validate_structure",
    "validate_tables",
    "validate_figures",
    "validate_references",
    "validate_volume",
    "validate_formulas",
    "validate_appendices",
    "validate_typography",
]
