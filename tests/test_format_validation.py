# tests/test_format_validation.py
"""Тесты валидации форматирования (Контур А)."""

import pytest
from pathlib import Path
from docx import Document
from src.validators.font_validator import check_font_formatting
from src.validators.format_validator import validate_format
from src.schemas import ReportError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


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


# =============================================================================
# Тесты для межстрочного интервала (Ф-2)
# =============================================================================

def test_F_2_spacing_error(rules):
    """Ф-2: неправильный межстрочный интервал"""
    docx_path = FIXTURES_DIR / "formatting" / "wrong_F_2_spacing.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Ф-2"]
    assert len(errors) >= 1, "Ошибка Ф-2 не обнаружена"


def test_F_2_correct_no_error(rules):
    """Ф-2: корректный документ не даёт ошибку"""
    docx_path = FIXTURES_DIR / "correct" / "correct_document.docx"
    assert docx_path.exists(), f"Эталонный файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    assert all(e.code != "Ф-2" for e in report.errors), "Ложное срабатывание Ф-2"


# =============================================================================
# Тесты для выравнивания (Ф-3)
# =============================================================================

def test_F_3_alignment_error(rules):
    """Ф-3: неправильное выравнивание абзаца"""
    docx_path = FIXTURES_DIR / "formatting" / "wrong_F_3_alignment.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Ф-3"]
    assert len(errors) >= 1, "Ошибка Ф-3 не обнаружена"


def test_F_3_correct_no_error(rules):
    """Ф-3: корректный документ не даёт ошибку"""
    docx_path = FIXTURES_DIR / "correct" / "correct_document.docx"
    assert docx_path.exists(), f"Эталонный файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    assert all(e.code != "Ф-3" for e in report.errors), "Ложное срабатывание Ф-3"


# =============================================================================
# Тесты для полей (Ф-4)
# =============================================================================

def test_F_4_margins_error(rules):
    """Ф-4: неправильные поля документа"""
    docx_path = FIXTURES_DIR / "formatting" / "wrong_F_4_margins.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Ф-4"]
    assert len(errors) >= 1, "Ошибка Ф-4 не обнаружена"


def test_F_4_correct_no_error(rules):
    """Ф-4: корректный документ не даёт ошибку"""
    docx_path = FIXTURES_DIR / "correct" / "correct_document.docx"
    assert docx_path.exists(), f"Эталонный файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    assert all(e.code != "Ф-4" for e in report.errors), "Ложное срабатывание Ф-4"


# =============================================================================
# Тесты для отступа первой строки (Ф-5)
# =============================================================================

def test_F_5_indent_error(rules):
    """Ф-5: неправильный отступ первой строки"""
    docx_path = FIXTURES_DIR / "formatting" / "wrong_F_5_indent.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Ф-5"]
    assert len(errors) >= 1, "Ошибка Ф-5 не обнаружена"


def test_F_5_correct_no_error(rules):
    """Ф-5: корректный документ не даёт ошибку"""
    docx_path = FIXTURES_DIR / "correct" / "correct_document.docx"
    assert docx_path.exists(), f"Эталонный файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    assert all(e.code != "Ф-5" for e in report.errors), "Ложное срабатывание Ф-5"


# =============================================================================
# Тесты для интервалов между абзацами (Ф-6)
# =============================================================================

def test_F_6_para_spacing_error(rules):
    """Ф-6: неправильные интервалы до/после абзаца"""
    docx_path = FIXTURES_DIR / "formatting" / "wrong_F_6_para_spacing.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Ф-6"]
    assert len(errors) >= 1, "Ошибка Ф-6 не обнаружена"


def test_F_6_correct_no_error(rules):
    """Ф-6: корректный документ не даёт ошибку"""
    docx_path = FIXTURES_DIR / "correct" / "correct_document.docx"
    assert docx_path.exists(), f"Эталонный файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    assert all(e.code != "Ф-6" for e in report.errors), "Ложное срабатывание Ф-6"


# =============================================================================
# Тесты структуры документа (С-*)
# =============================================================================

def test_C_1_missing_conclusion_error(rules):
    """С-1: отсутствует раздел Заключение"""
    docx_path = FIXTURES_DIR / "structure" / "wrong_C_1_missing_conclusion.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "С-1"]
    assert len(errors) >= 1, "Ошибка С-1 не обнаружена"


def test_C_5_chapter_naming_error(rules):
    """С-5: заголовок главы без слова 'Глава'"""
    docx_path = FIXTURES_DIR / "structure" / "wrong_C_5_chapter_name.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    assert any(e.code == "С-5" for e in report.errors), "Ошибка С-5 не обнаружена"


def test_C_7_bold_heading_error(rules):
    """С-7: заголовок не жирным шрифтом"""
    docx_path = FIXTURES_DIR / "structure" / "wrong_C_7_bold_heading.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "С-7"]
    assert len(errors) >= 1, "Ошибка С-7 не обнаружена"


def test_C_8_heading_alignment_error(rules):
    """С-8: неправильное выравнивание заголовка"""
    docx_path = FIXTURES_DIR / "structure" / "wrong_C_8_heading_alignment.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "С-8"]
    assert len(errors) >= 1, "Ошибка С-8 не обнаружена"


def test_C_9_heading_period_error(rules):
    """С-9: точка в конце заголовка"""
    docx_path = FIXTURES_DIR / "structure" / "wrong_C_9_heading_period.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "С-9"]
    assert len(errors) >= 1, "Ошибка С-9 не обнаружена"


# =============================================================================
# Тесты таблиц (Т-*)
# =============================================================================

def test_T_1_caption_position_error(rules):
    """Т-1: неправильное расположение подписи таблицы"""
    docx_path = FIXTURES_DIR / "tables" / "wrong_T_1_caption_position.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Т-1"]
    assert len(errors) >= 1, "Ошибка Т-1 не обнаружена"


def test_T_4_font_size_error(rules):
    """Т-4: неправильный размер шрифта в таблице"""
    docx_path = FIXTURES_DIR / "tables" / "wrong_T_4_font_size.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Т-4"]
    assert len(errors) >= 1, "Ошибка Т-4 не обнаружена"


def test_T_12_decimal_point_error(rules):
    """Т-12: неправильный разделитель десятичных дробей в таблице"""
    docx_path = FIXTURES_DIR / "tables" / "wrong_T_12_decimal_point.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Т-12"]
    assert len(errors) >= 1, "Ошибка Т-12 не обнаружена"


# =============================================================================
# Тесты библиографических ссылок (Л-*)
# =============================================================================

def test_L_1_bracket_format_error(rules):
    """Л-1: неправильный формат квадратных скобок в ссылке"""
    docx_path = FIXTURES_DIR / "references" / "wrong_L_1_bracket_format.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Л-1"]
    assert len(errors) >= 1, "Ошибка Л-1 не обнаружена"


def test_L_3_multiple_order_error(rules):
    """Л-3: неправильный порядок множественных ссылок"""
    docx_path = FIXTURES_DIR / "references" / "wrong_L_3_multiple_order.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Л-3"]
    assert len(errors) >= 1, "Ошибка Л-3 не обнаружена"


def test_L_7_min_sources_error(rules):
    """Л-7: недостаточно источников в списке литературы"""
    docx_path = FIXTURES_DIR / "references" / "wrong_L_7_min_sources.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Л-7"]
    assert len(errors) >= 1, "Ошибка Л-7 не обнаружена"


# =============================================================================
# Тесты типографики (Н-*)
# =============================================================================

def test_N_2_initials_space_error(rules):
    """Н-2: неправильные пробелы между инициалами"""
    docx_path = FIXTURES_DIR / "typography" / "wrong_N_2_initials_space.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Н-2"]
    assert len(errors) >= 1, "Ошибка Н-2 не обнаружена"


def test_N_4_quotes_error(rules):
    """Н-4: неправильные кавычки"""
    docx_path = FIXTURES_DIR / "typography" / "wrong_N_4_quotes.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Н-4"]
    assert len(errors) >= 1, "Ошибка Н-4 не обнаружена"


def test_N_6_abbreviation_error(rules):
    """Н-6: неправильное оформление сокращений"""
    docx_path = FIXTURES_DIR / "typography" / "wrong_N_6_abbreviation.docx"
    assert docx_path.exists(), f"Файл не найден: {docx_path}"
    
    report = validate_format(str(docx_path), rules)
    errors = [e for e in report.errors if e.code == "Н-6"]
    assert len(errors) >= 1, "Ошибка Н-6 не обнаружена"

