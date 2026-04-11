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
        "margins_cm": {"left": 3.0, "right": 1.0, "top": 2.0, "bottom": 2.0},
        "required_sections": [
            "титульный лист",
            "содержание",
            "введение",
            "Глава 1",
            "Глава 2",
            "заключение",
            "список литературы"
        ],
        "chapter_heading_pattern": "^Глава\\s+(?:\\d+|[IVX]+)[.:]?\\s.+",
        "paragraph_heading_pattern": "^\\d+\\.\\d+\\.?(?:\\.\\d+\\.?)?\\s.+",
        "tolerances": {"dxa": 20, "pt": 0.5},
        "references": {"min_sources": 40},
        "volume": {
            "total_chars_min": 90000,
            "total_chars_max": 108000,
            "theory_chapter_chars_min": 27000,
            "theory_chapter_chars_max": 36000,
            "empirical_chapter_chars_min": 45000,
            "empirical_chapter_chars_max": 54000
        },
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


@pytest.fixture
def wrong_missing_conclusion_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_conclusion.docx"

@pytest.fixture
def wrong_C_2_appendix_no_reference_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_2_appendix_no_reference.docx"

@pytest.fixture
def wrong_C_3_section_no_page_break_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_3_section_no_page_break.docx"

@pytest.fixture
def wrong_C_4_paragraph_with_page_break_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_4_paragraph_with_page_break.docx"

@pytest.fixture
def wrong_chapter_name_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_5_chapter_name.docx"

@pytest.fixture
def wrong_C_6_paragraph_numbering_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_6_paragraph_numbering.docx"

@pytest.fixture
def wrong_bold_heading_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_7_bold_heading.docx"

@pytest.fixture
def wrong_heading_alignment_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_8_heading_alignment.docx"

@pytest.fixture
def wrong_heading_period_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_9_heading_period.docx"

@pytest.fixture
def wrong_C_10_subheading_in_paragraph_docx():
    return FIXTURES_DIR / "structure" / "wrong_C_10_subheading_in_paragraph.docx"


@pytest.fixture
def wrong_C_1_missing_title_page_docx():
    """Нарушение С-1: отсутствует Титульный лист."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_title_page.docx"


@pytest.fixture
def wrong_C_1_missing_table_of_contents_docx():
    """Нарушение С-1: отсутствует Содержание."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_table_of_contents.docx"


@pytest.fixture
def wrong_C_1_missing_introduction_docx():
    """Нарушение С-1: отсутствует Введение."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_introduction.docx"


@pytest.fixture
def wrong_C_1_missing_chapter1_docx():
    """Нарушение С-1: отсутствует Глава 1."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_chapter1.docx"


@pytest.fixture
def wrong_C_1_missing_chapter2_docx():
    """Нарушение С-1: отсутствует Глава 2."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_chapter2.docx"


@pytest.fixture
def wrong_C_1_missing_references_docx():
    """Нарушение С-1: отсутствует Список литературы."""
    return FIXTURES_DIR / "structure" / "wrong_C_1_missing_references.docx"


@pytest.fixture
def correct_C_1_all_sections_present_docx():
    """Корректный документ: все разделы присутствуют."""
    return FIXTURES_DIR / "structure" / "correct_C_1_all_sections_present.docx"


# ── Фикстуры для тестов таблиц (Т-*) ──────────────────────────────────────────

@pytest.fixture
def wrong_caption_position_docx():
    """Подпись таблицы снизу вместо сверху (нарушение Т-1)."""
    return FIXTURES_DIR / "tables" / "wrong_T_1_caption_position.docx"


@pytest.fixture
def wrong_table_title_alignment_docx():
    """Название таблицы не по центру (нарушение Т-2)."""
    return FIXTURES_DIR / "tables" / "wrong_T_2_table_title_alignment.docx"


@pytest.fixture
def wrong_table_title_dot_docx():
    """Название таблицы с точкой в конце (нарушение Т-3)."""
    return FIXTURES_DIR / "tables" / "wrong_T_3_table_title_dot.docx"


@pytest.fixture
def wrong_table_font_size_docx():
    """Размер шрифта в таблице меньше 14 пт (нарушение Т-4)."""
    return FIXTURES_DIR / "tables" / "wrong_T_4_font_size.docx"


@pytest.fixture
def wrong_table_width_alignment_docx():
    """Таблица не выровнена по ширине страницы (нарушение Т-5)."""
    return FIXTURES_DIR / "tables" / "wrong_T_5_table_width_alignment.docx"


@pytest.fixture
def wrong_table_numbering_gap_docx():
    """Пропуск в нумерации таблиц (нарушение Т-6)."""
    return FIXTURES_DIR / "tables" / "wrong_T_6_numbering_gap.docx"


@pytest.fixture
def wrong_figure_caption_alignment_docx():
    """Подпись рисунка не по центру (нарушение Т-7)."""
    return FIXTURES_DIR / "tables" / "wrong_T_7_figure_caption_alignment.docx"


@pytest.fixture
def wrong_figure_title_capitalization_docx():
    """Название рисунка с неправильной капитализацией (нарушение Т-8)."""
    return FIXTURES_DIR / "tables" / "wrong_T_8_figure_title_capitalization.docx"


@pytest.fixture
def wrong_conditional_legend_font_docx():
    """Шрифт в условных обозначениях меньше 14 пт (нарушение Т-9)."""
    return FIXTURES_DIR / "tables" / "wrong_T_9_conditional_legend_font.docx"


@pytest.fixture
def wrong_figure_spacing_docx():
    """Неправильные отступы у рисунков (нарушение Т-10)."""
    return FIXTURES_DIR / "tables" / "wrong_T_10_figure_spacing.docx"


@pytest.fixture
def wrong_data_duplicate_docx():
    """Дублирование данных в таблице (нарушение Т-11)."""
    return FIXTURES_DIR / "tables" / "wrong_T_11_data_duplicate.docx"


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


@pytest.fixture
def wrong_N_5_hyphen_vs_dash_docx():
    """Нарушение Н-5: дефис вместо тире между датами."""
    return FIXTURES_DIR / "typography" / "wrong_N_5_hyphen_vs_dash.docx"


@pytest.fixture
def wrong_N_7_manual_list_numbering_docx():
    """Нарушение Н-7: ручная нумерация вместо автоматической."""
    return FIXTURES_DIR / "typography" / "wrong_N_7_manual_list_numbering.docx"


@pytest.fixture
def wrong_N_7_mixed_list_markers_docx():
    """Нарушение Н-7: разные маркеры в одном списке."""
    return FIXTURES_DIR / "typography" / "wrong_N_7_mixed_list_markers.docx"


# ── Фикстуры для корректных тестов типографики (Н-*) ──────────────────────────

@pytest.fixture
def correct_N_5_dash_correct_docx():
    """Корректное использование тире между датами."""
    return FIXTURES_DIR / "typography" / "correct_N_5_dash_correct.docx"


@pytest.fixture
def correct_N_7_auto_numbering_docx():
    """Корректная автоматическая нумерация списков."""
    return FIXTURES_DIR / "typography" / "correct_N_7_auto_numbering.docx"


@pytest.fixture
def correct_N_7_unified_markers_docx():
    """Корректные унифицированные маркеры списков."""
    return FIXTURES_DIR / "typography" / "correct_N_7_unified_markers.docx"


# ── Дополнительные фикстуры для списка литературы (Л-*) ───────────────────────

@pytest.fixture
def wrong_L_4_alphabetical_order_docx():
    return FIXTURES_DIR / "references" / "wrong_L_4_alphabetical_order.docx"


@pytest.fixture
def wrong_L_4_cyrillic_before_latin_docx():
    return FIXTURES_DIR / "references" / "wrong_L_4_cyrillic_before_latin.docx"


@pytest.fixture
def wrong_L_5_numbering_docx():
    return FIXTURES_DIR / "references" / "wrong_L_5_numbering.docx"


@pytest.fixture
def wrong_L_8_old_sources_docx():
    return FIXTURES_DIR / "references" / "wrong_L_8_old_sources.docx"


@pytest.fixture
def wrong_L_9_author_format_docx():
    return FIXTURES_DIR / "references" / "wrong_L_9_author_format.docx"


@pytest.fixture
def wrong_L_10_url_no_date_docx():
    return FIXTURES_DIR / "references" / "wrong_L_10_url_no_date.docx"


@pytest.fixture
def wrong_L_11_invalid_reference_docx():
    return FIXTURES_DIR / "references" / "wrong_L_11_invalid_reference.docx"


@pytest.fixture
def wrong_L_12_hyphen_instead_of_dash_docx():
    return FIXTURES_DIR / "references" / "wrong_L_12_hyphen_instead_of_dash.docx"


# ── Фикстуры для тестов содержания (Со-*) ─────────────────────────────────────

@pytest.fixture
def wrong_So_1_toc_missing_headings_docx():
    """Нарушение Со-1: в содержании отсутствуют некоторые заголовки."""
    return FIXTURES_DIR / "toc" / "wrong_So_1_toc_missing_headings.docx"


# ── Фикстуры для тестов приложений (П-*) ──────────────────────────────────────

@pytest.fixture
def wrong_P_1_appendix_no_new_page_docx():
    """Нарушение П-1: приложение не начинается с новой страницы."""
    return FIXTURES_DIR / "appendix" / "wrong_P_1_appendix_no_new_page.docx"


@pytest.fixture
def wrong_P_2_appendix_label_position_docx():
    """Нарушение П-2: надпись 'Приложение N' не в правом верхнем углу."""
    return FIXTURES_DIR / "appendix" / "wrong_P_2_appendix_label_position.docx"


@pytest.fixture
def wrong_P_3_appendix_title_format_docx():
    """Нарушение П-3: название приложения не по центру или с точкой."""
    return FIXTURES_DIR / "appendix" / "wrong_P_3_appendix_title_format.docx"


@pytest.fixture
def wrong_P_4_appendix_numbering_order_docx():
    """Нарушение П-4: нумерация приложений не в порядке ссылок."""
    return FIXTURES_DIR / "appendix" / "wrong_P_4_appendix_numbering_order.docx"


# ── Дополнительные фикстуры для ссылок (Л-*) ──────────────────────────────────

@pytest.fixture
def wrong_L_2_repeated_ref_format_docx():
    """Нарушение Л-2: повторная ссылка оформлена неправильно."""
    return FIXTURES_DIR / "references" / "wrong_L_2_repeated_ref_format.docx"


# ── Фикстуры для корректных тестов приложений (П-*) ───────────────────────────

@pytest.fixture
def correct_P_1_appendix_new_page_docx():
    """Корректное приложение: начинается с новой страницы."""
    return FIXTURES_DIR / "structure" / "correct_document.docx"


@pytest.fixture
def correct_P_2_appendix_label_position_docx():
    """Корректное приложение: надпись 'Приложение N' в правом верхнем углу."""
    return FIXTURES_DIR / "structure" / "correct_document.docx"


@pytest.fixture
def correct_P_3_appendix_title_format_docx():
    """Корректное приложение: название по центру, без точки."""
    return FIXTURES_DIR / "structure" / "correct_document.docx"


@pytest.fixture
def correct_P_4_appendix_numbering_order_docx():
    """Корректное приложение: нумерация в порядке ссылок."""
    return FIXTURES_DIR / "structure" / "correct_document.docx"


# ── Фикстуры для корректных тестов списка литературы (Л-*) ─────────────────────

@pytest.fixture
def correct_L_1_bracket_format_docx():
    """Корректные ссылки: формат квадратных скобок [N] или [N, с. X]."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_2_repeated_ref_format_docx():
    """Корректные ссылки: повторная ссылка оформлена как [там же, с. X]."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_3_multiple_order_docx():
    """Корректные ссылки: множественные источники в арифметическом порядке."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_4_alphabetical_order_docx():
    """Корректный список литературы: алфавитный порядок, сначала русские."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_5_numbering_docx():
    """Корректный список литературы: сплошная нумерация."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_7_min_sources_docx():
    """Корректный список литературы: не менее 40 источников."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_8_old_sources_docx():
    """Корректный список литературы: основная часть источников за последние 10 лет."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_9_author_format_docx():
    """Корректный список литературы: формат автора 'Фамилия, И. О.'."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_10_url_with_date_docx():
    """Корректные URL-ссылки: с датой обращения (дата обращения: ДД.ММ.ГГГГ)."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_11_all_references_valid_docx():
    """Корректные ссылки: все ссылки [N] соответствуют источникам в списке."""
    return FIXTURES_DIR / "references" / "correct_document.docx"


@pytest.fixture
def correct_L_12_dash_instead_of_hyphen_docx():
    """Корректный список литературы: все тире длинные (–)."""
    return FIXTURES_DIR / "references" / "correct_document.docx"
