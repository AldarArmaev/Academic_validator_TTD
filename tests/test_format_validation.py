# tests/test_format_validation.py
"""Тесты валидации форматирования (Контур А)."""

import pytest
from docx import Document
from src.validators.font_validator import check_font_formatting
from src.validators.paragraph_validator import check_paragraph_formatting
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


class TestParagraphFormatting:
    """Тесты проверки межстрочного интервала (требование Ф-2)."""

    def test_wrong_spacing_detects_error(self, wrong_spacing_docx, rules):
        """RED-тест: документ с одинарным интервалом должен вернуть ошибку Ф-2."""
        doc = Document(str(wrong_spacing_docx))
        errors = check_paragraph_formatting(doc, rules)
        
        # Проверяем, что есть хотя бы одна ошибка с кодом Ф-2
        spacing_errors = [e for e in errors if e.code == "Ф-2"]
        assert len(spacing_errors) > 0, "Ожидалась ошибка Ф-2, но ошибок не найдено"
        
        # Проверяем, что ошибка содержит неправильное значение интервала
        wrong_interval_errors = [e for e in spacing_errors if "240" in e.found_value]
        assert len(wrong_interval_errors) > 0, "Ожидалась ошибка с интервалом 240 twips"
        
        # Проверяем все обязательные поля ошибки
        error = wrong_interval_errors[0]
        assert error.id is not None
        assert error.code == "Ф-2"
        assert error.type == "formatting"
        assert error.severity == "error"
        assert error.location.paragraph_index >= 0
        assert error.fragment is not None
        assert "1,5" in error.rule or "420" in error.rule
        assert "§4.2" in error.rule_citation
        assert "420" in error.expected_value
        assert "240" in error.found_value
        assert error.recommendation is not None

    def test_correct_spacing_no_errors(self, correct_docx, rules):
        """GREEN-тест: корректный документ не должен иметь ошибок Ф-2."""
        doc = Document(str(correct_docx))
        errors = check_paragraph_formatting(doc, rules)
        
        # Проверяем, что нет ошибок Ф-2
        spacing_errors = [e for e in errors if e.code == "Ф-2"]
        assert len(spacing_errors) == 0, f"Ожидалось 0 ошибок Ф-2, но найдено: {spacing_errors}"
