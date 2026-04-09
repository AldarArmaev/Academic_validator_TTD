# tests/conftest.py
import pytest
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path
import json


# ── Вспомогательные функции ──────────────────────────────────────────────────

def set_paragraph_spacing(para, line_twips: int, space_before: int = 0, space_after: int = 0):
    """Устанавливает межстрочный интервал и отступы до/после абзаца через XML."""
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:line'), str(line_twips))
    spacing.set(qn('w:lineRule'), 'auto')
    spacing.set(qn('w:before'), str(space_before))
    spacing.set(qn('w:after'), str(space_after))
    pPr.append(spacing)


def set_first_line_indent(para, dxa: int):
    """Устанавливает отступ первой строки через XML."""
    pPr = para._p.get_or_add_pPr()
    ind = OxmlElement('w:ind')
    ind.set(qn('w:firstLine'), str(dxa))
    pPr.append(ind)


def set_alignment(para, alignment: str):
    """alignment: 'both' | 'left' | 'center' | 'right'"""
    pPr = para._p.get_or_add_pPr()
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), alignment)
    pPr.append(jc)


def add_correct_paragraph(doc, text: str):
    """Добавляет абзац со всеми правильными параметрами форматирования."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, line_twips=420, space_before=0, space_after=0)
    set_first_line_indent(p, dxa=720)
    set_alignment(p, 'both')
    return p


def make_base_doc():
    """Создаёт документ с правильными полями."""
    doc = Document()
    s = doc.sections[0]
    EMU_PER_DXA = 635
    s.left_margin   = 1701 * EMU_PER_DXA   # 3.0 см = 1701 DXA = 1079135 EMU
    s.right_margin  = 567  * EMU_PER_DXA   # 1.0 см
    s.top_margin    = 1134 * EMU_PER_DXA   # 2.0 см
    s.bottom_margin = 1134 * EMU_PER_DXA   # 2.0 см
    return doc


# ── Фикстуры для тестов валидации шрифта ─────────────────────────────────────

@pytest.fixture(scope="session")
def correct_docx(tmp_path_factory):
    """Полностью корректный документ — 0 ошибок форматирования."""
    path = tmp_path_factory.mktemp("fix") / "correct.docx"
    doc = make_base_doc()
    for title in ["Введение", "Глава 1. Теоретические основы", "Заключение", "Список литературы"]:
        doc.add_heading(title, level=1)
        add_correct_paragraph(doc, "Текст раздела. Содержательный абзац.")
    doc.save(path)
    return path


@pytest.fixture(scope="session")
def wrong_font_docx(tmp_path_factory):
    """Абзац с Arial вместо Times New Roman (нарушение Ф-1)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_font.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    add_correct_paragraph(doc, "Правильный абзац.")
    p = doc.add_paragraph()
    run = p.add_run("Абзац с неправильным шрифтом Arial.")
    run.font.name = "Arial"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, 420)
    set_first_line_indent(p, 720)
    set_alignment(p, 'both')
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path


@pytest.fixture
def rules():
    """Загружает правила из university_rules.json."""
    rules_content = {
        "font": {
            "family": "Times New Roman",
            "size_half_points": 28,
            "size_pt": 14
        },
        "paragraph": {
            "line_spacing_twips": 420,
            "line_spacing_rule": "auto",
            "first_line_indent_dxa": 720,
            "first_line_indent_cm": 1.25,
            "alignment": "both",
            "space_before_twips": 0,
            "space_after_twips": 0
        },
        "margins_dxa": {
            "left": 1701,
            "right": 567,
            "top": 1134,
            "bottom": 1134
        },
        "tolerances": {
            "dxa": 20,
            "pt": 0.5
        }
    }
    return rules_content
