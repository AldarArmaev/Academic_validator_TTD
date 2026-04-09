# tests/test_format_validation.py
"""Тесты валидации форматирования (Контур А)."""

import pytest
from docx import Document
from src.validators.font_validator import check_font_formatting
from src.schemas import ReportError


class TestFontFormatting:
    """Тесты проверки шрифта (требование Ф-1)."""

    def test_wrong_font_detects_error(self, wrong_font_docx, rules):
        """RED-тест: документ с Arial должен вернуть ошибку Ф-1."""
        doc = Document(str(wrong_font_docx))
        errors = check_font_formatting(doc, rules)
        
        # Проверяем, что есть хотя бы одна ошибка с кодом Ф-1
        font_errors = [e for e in errors if e.code == "Ф-1"]
        assert len(font_errors) > 0, "Ожидалась ошибка Ф-1, но ошибок не найдено"
        
        # Проверяем, что ошибка содержит правильный тип шрифта
        arial_errors = [e for e in font_errors if "Arial" in e.found_value]
        assert len(arial_errors) > 0, "Ожидалась ошибка со шрифтом Arial"
        
        # Проверяем все обязательные поля ошибки
        error = arial_errors[0]
        assert error.id is not None
        assert error.code == "Ф-1"
        assert error.type == "formatting"
        assert error.severity == "error"
        assert error.location.paragraph_index >= 0
        assert error.fragment is not None
        assert "Times New Roman" in error.rule
        assert "§4.2" in error.rule_citation
        assert error.expected_value == "Times New Roman"
        assert "Arial" in error.found_value
        assert error.recommendation is not None

    def test_correct_font_no_errors(self, correct_docx, rules):
        """GREEN-тест: корректный документ не должен иметь ошибок Ф-1."""
        doc = Document(str(correct_docx))
        errors = check_font_formatting(doc, rules)
        
        # Проверяем, что нет ошибок Ф-1
        font_errors = [e for e in errors if e.code == "Ф-1"]
        assert len(font_errors) == 0, f"Ожидалось 0 ошибок Ф-1, но найдено: {font_errors}"
