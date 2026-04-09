# tests/conftest.py
import pytest
from pathlib import Path


# ── Базовые пути ──────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── Фикстура с правилами валидации ────────────────────────────────────────────

@pytest.fixture
def rules():
    return {
        "font": {"family": "Times New Roman", "size_half_points": 28, "size_pt": 14},
        "paragraph": {
            "line_spacing_twips": 420,
            "line_spacing_rule": "auto",
            "first_line_indent_dxa": 720,
            "first_line_indent_cm": 1.25,
            "alignment": "both",
            "space_before_twips": 0,
            "space_after_twips": 0
        },
        "margins_dxa": {"left": 1701, "right": 567, "top": 1134, "bottom": 1134},
        "required_sections": ["введение", "заключение", "список литературы"],
        "chapter_heading_pattern": "^Глава \\d+\\.\\s.+",
        "tolerances": {"dxa": 20, "pt": 0.5},
        "references": {"min_sources": 40}
    }


# ── Фикстуры для тестов валидации шрифта (Ф-*) ────────────────────────────────

@pytest.fixture
def correct_docx():
    """Полностью корректный документ — 0 ошибок форматирования."""
    return FIXTURES_DIR / "correct" / "correct_document.docx"


@pytest.fixture
def wrong_font_docx():
    """Абзац с Arial вместо Times New Roman (нарушение Ф-1)."""
    return FIXTURES_DIR / "formatting" / "wrong_F_1_font.docx"


@pytest.fixture
def wrong_spacing_docx():
    """Неправильный межстрочный интервал (нарушение Ф-2)."""
    return FIXTURES_DIR / "formatting" / "wrong_F_2_spacing.docx"


@pytest.fixture
def wrong_alignment_docx():
    """Выравнивание не по ширине (нарушение Ф-3)."""
    return FIXTURES_DIR / "formatting" / "wrong_F_3_alignment.docx"


@pytest.fixture
def wrong_margins_docx():
    """Неправильные поля документа (нарушение Ф-4)."""
    return FIXTURES_DIR / "formatting" / "wrong_F_4_margins.docx"


@pytest.fixture
def wrong_indent_docx():
    """Неправильный отступ первой строки (нарушение Ф-5)."""
    return FIXTURES_DIR / "formatting" / "wrong_F_5_indent.docx"


@pytest.fixture
def wrong_para_spacing_docx():
    """Неправильные интервалы до/после абзаца (нарушение Ф-6)."""
    return FIXTURES_DIR / "formatting" / "wrong_F_6_para_spacing.docx"


# ── Фикстуры для тестов структуры (С-*) ───────────────────────────────────────

@pytest.fixture
def wrong_missing_conclusion_docx():
    """Отсутствует раздел Заключение (нарушение С-1)."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_conclusion.docx"


@pytest.fixture
def wrong_chapter_name_docx():
    """Заголовок главы без слова Глава (нарушение С-5)."""
    return FIXTURES_DIR / "structure" / "wrong_C_5_chapter_name.docx"


@pytest.fixture
def wrong_bold_heading_docx():
    """Заголовок не жирным шрифтом (нарушение С-7)."""
    return FIXTURES_DIR / "structure" / "wrong_C_7_bold_heading.docx"


@pytest.fixture
def wrong_heading_alignment_docx():
    """Неправильное выравнивание заголовка (нарушение С-8)."""
    return FIXTURES_DIR / "structure" / "wrong_C_8_heading_alignment.docx"


@pytest.fixture
def wrong_heading_period_docx():
    """Точка в конце заголовка (нарушение С-9)."""
    return FIXTURES_DIR / "structure" / "wrong_C_9_heading_period.docx"


# ── Фикстуры для тестов таблиц (Т-*) ──────────────────────────────────────────

@pytest.fixture
def wrong_caption_position_docx():
    """Подпись таблицы снизу вместо сверху (нарушение Т-1)."""
    return FIXTURES_DIR / "tables" / "wrong_T_1_caption_position.docx"


@pytest.fixture
def wrong_table_font_size_docx():
    """Размер шрифта в таблице меньше 14 пт (нарушение Т-4)."""
    return FIXTURES_DIR / "tables" / "wrong_T_4_font_size.docx"


@pytest.fixture
def wrong_decimal_point_docx():
    """Неправильный десятичный разделитель (нарушение Т-12)."""
    return FIXTURES_DIR / "tables" / "wrong_T_12_decimal_point.docx"


# ── Фикстуры для тестов ссылок и списка литературы (Л-*) ──────────────────────

@pytest.fixture
def wrong_bracket_format_docx():
    """Ссылки в квадратных скобках без пробелов (нарушение Л-1)."""
    return FIXTURES_DIR / "references" / "wrong_L_1_bracket_format.docx"


@pytest.fixture
def wrong_multiple_order_docx():
    """Множественные ссылки в неправильном порядке (нарушение Л-3)."""
    return FIXTURES_DIR / "references" / "wrong_L_3_multiple_order.docx"


@pytest.fixture
def wrong_min_sources_docx():
    """Менее 25 источников в списке литературы (нарушение Л-7)."""
    return FIXTURES_DIR / "references" / "wrong_L_7_min_sources.docx"


# ── Фикстуры для тестов типографики (Н-*) ─────────────────────────────────────

@pytest.fixture
def wrong_initials_space_docx():
    """Нет пробелов между инициалами (нарушение Н-2)."""
    return FIXTURES_DIR / "typography" / "wrong_N_2_initials_space.docx"


@pytest.fixture
def wrong_quotes_docx():
    """Используются кавычки "" вместо «» (нарушение Н-4)."""
    return FIXTURES_DIR / "typography" / "wrong_N_4_quotes.docx"


@pytest.fixture
def wrong_abbreviation_docx():
    """Сокращения оформлены неправильно (нарушение Н-6)."""
    return FIXTURES_DIR / "typography" / "wrong_N_6_abbreviation.docx"
