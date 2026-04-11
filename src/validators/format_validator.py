# src/validators/format_validator.py
"""Общий валидатор форматирования документов."""

from docx import Document
from docx.oxml.ns import qn
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from src.schemas import ValidationReport, ReportSummary, ReportError, ErrorLocation
from src.validators.font_validator import check_font_formatting


# ─────────────────────────────────────────────────────────────────────────────
# ИСПРАВЛЕНИЕ #2 и #4
# Служебные заголовки и заголовки глав/параграфов нужно пропускать везде.
# Паттерны вынесены в константы, чтобы использовать одинаково во всех функциях.
# ─────────────────────────────────────────────────────────────────────────────

HEADING_STYLES = {
    "Heading 1", "Heading 2", "Heading 3",
    "Heading 4", "Heading 5", "Heading 6",
}

SERVICE_TITLES = [
    "введение", "заключение", "список литературы",
    "содержание", "оглавление", "библиографический список",
]

# ИСПРАВЛЕНИЕ #4: паттерн параграфа должен допускать точку после номера:
# «2.1. Описание» — точка после последней цифры обязательна по ГОСТ
CHAPTER_HEADING_PATTERN  = r"^Глава\s+\d+[.:]?\s+.+"
PARAGRAPH_HEADING_PATTERN = r"^\d+\.\d+\.?(\.\d+\.?)?\s+.+"


def _is_heading_paragraph(para, chapter_pat: str = CHAPTER_HEADING_PATTERN,
                           para_pat: str = PARAGRAPH_HEADING_PATTERN) -> bool:
    """True если абзац является заголовком (по стилю или по тексту)."""
    # По стилю Word
    if para.style and para.style.name in HEADING_STYLES:
        return True
    # По наличию w:outlineLvl в XML
    pPr = para._p.pPr
    if pPr is not None and pPr.find(qn('w:outlineLvl')) is not None:
        return True
    text = para.text.strip()
    if not text:
        return False
    text_lower = text.lower()
    # Служебные разделы
    if any(s in text_lower for s in SERVICE_TITLES):
        return True
    # По паттернам
    if re.match(chapter_pat, text) or re.match(para_pat, text):
        return True
    return False


def check_paragraph_formatting(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет форматирование абзацев.

    А) Межстрочный интервал (Ф-2)
    Б) Выравнивание (Ф-3)
    В) Отступ первой строки (Ф-5)
    Г) Интервалы до/после (Ф-6)
    """
    errors: list[ReportError] = []

    expected_line_spacing  = rules["paragraph"]["line_spacing_twips"]   # 420
    tolerance_dxa          = rules["tolerances"]["dxa"]                  # 20
    expected_first_line    = 720                                          # DXA
    expected_before_after  = 0                                            # twips

    chapter_pat = rules.get("chapter_heading_pattern",   CHAPTER_HEADING_PATTERN)
    para_pat    = rules.get("paragraph_heading_pattern", PARAGRAPH_HEADING_PATTERN)

    for para_index, para in enumerate(doc.paragraphs):
        # ИСПРАВЛЕНИЕ #2: пропускаем любые заголовки и подписи
        if _is_heading_paragraph(para, chapter_pat, para_pat):
            continue
        if not para.text.strip():
            continue

        text_stripped = para.text.strip()
        if (text_stripped.startswith("Таблица") or
                text_stripped.startswith("Рис.") or
                text_stripped.startswith("Рисунок")):
            continue

        pPr = para._p.pPr

        # А) Межстрочный интервал (Ф-2)
        spacing_el = pPr.find(qn('w:spacing')) if pPr is not None else None
        if spacing_el is not None:
            line_val = spacing_el.get(qn('w:line'))
            if line_val is not None:
                try:
                    actual = int(line_val)
                    if abs(actual - expected_line_spacing) > tolerance_dxa:
                        errors.append(ReportError(
                            id=f"Ф-2-{para_index}",
                            code="Ф-2",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=para_index,
                                structural_path=f"Абзац {para_index + 1}",
                            ),
                            fragment=para.text[:100],
                            rule="Межстрочный интервал должен быть 1.5 (420 twips)",
                            rule_citation="§4.2, с. 47",
                            found_value=str(actual),
                            expected_value=str(expected_line_spacing),
                            recommendation="Установите межстрочный интервал 1.5",
                        ))
                except ValueError:
                    pass

        # Б) Выравнивание (Ф-3)
        jc_el = pPr.find(qn('w:jc')) if pPr is not None else None
        if jc_el is not None:
            alignment = jc_el.get(qn('w:val'))
            if alignment != "both":
                errors.append(ReportError(
                    id=f"Ф-3-{para_index}",
                    code="Ф-3",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_index,
                        structural_path=f"Абзац {para_index + 1}",
                    ),
                    fragment=para.text[:100],
                    rule="Текст должен быть выровнен по ширине",
                    rule_citation="§4.2, с. 47",
                    found_value=alignment or "не задано",
                    expected_value="both",
                    recommendation="Установите выравнивание по ширине",
                ))

        # В) Отступ первой строки (Ф-5)
        ind_el = pPr.find(qn('w:ind')) if pPr is not None else None
        if ind_el is not None:
            first_line = ind_el.get(qn('w:firstLine'))
            if first_line is not None:
                try:
                    actual_fl = int(first_line)
                    if abs(actual_fl - expected_first_line) > tolerance_dxa:
                        errors.append(ReportError(
                            id=f"Ф-5-{para_index}",
                            code="Ф-5",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=para_index,
                                structural_path=f"Абзац {para_index + 1}",
                            ),
                            fragment=para.text[:100],
                            rule="Отступ первой строки должен быть 1.25 см (720 DXA)",
                            rule_citation="§4.2, с. 47",
                            found_value=str(actual_fl),
                            expected_value=str(expected_first_line),
                            recommendation="Установите отступ первой строки 1.25 см",
                        ))
                except ValueError:
                    pass

        # Г) Интервалы до/после (Ф-6)
        if spacing_el is not None:
            for attr, label in [(qn('w:before'), "перед абзацем"), (qn('w:after'), "после абзаца")]:
                val = spacing_el.get(attr)
                if val is not None:
                    try:
                        actual_sp = int(val)
                        if actual_sp != expected_before_after:
                            side = "before" if "before" in attr else "after"
                            errors.append(ReportError(
                                id=f"Ф-6-{side}-{para_index}",
                                code="Ф-6",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=para_index,
                                    structural_path=f"Абзац {para_index + 1}",
                                ),
                                fragment=para.text[:100],
                                rule="Интервалы до и после абзаца должны быть 0",
                                rule_citation="§4.2, с. 47",
                                found_value=str(actual_sp),
                                expected_value=str(expected_before_after),
                                recommendation=f"Установите интервал {label} равным 0",
                            ))
                    except ValueError:
                        pass

    return errors


def check_margins(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет поля документа (Ф-4)."""
    errors: list[ReportError] = []

    section       = doc.sections[0]
    EMU_PER_DXA   = 635
    tolerance_dxa = rules["tolerances"]["dxa"]

    margins_config = {
        "left":   section.left_margin,
        "right":  section.right_margin,
        "top":    section.top_margin,
        "bottom": section.bottom_margin,
    }

    for margin_name, margin_emu in margins_config.items():
        expected_dxa = rules["margins_dxa"][margin_name]
        actual_dxa   = round(margin_emu / EMU_PER_DXA)
        if abs(actual_dxa - expected_dxa) > tolerance_dxa:
            errors.append(ReportError(
                id=f"Ф-4-{margin_name}",
                code="Ф-4",
                type="formatting",
                severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Поля документа"),
                fragment=f"Поле {margin_name}",
                rule=f"Поле {margin_name} должно быть {expected_dxa} DXA "
                     f"({rules['margins_cm'][margin_name]} см)",
                rule_citation="§4.2, с. 47",
                found_value=str(actual_dxa),
                expected_value=str(expected_dxa),
                recommendation=f"Установите поле {margin_name} = "
                               f"{rules['margins_cm'][margin_name]} см",
            ))

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# ИСПРАВЛЕНИЕ #3 — корректный поиск разрыва страницы
# ─────────────────────────────────────────────────────────────────────────────

def _has_page_break_before(para, para_idx: int, all_paragraphs) -> bool:
    """
    Возвращает True если перед данным абзацем есть разрыв страницы.

    Проверяет три места:
    1. w:pageBreakBefore в pPr самого абзаца (явное свойство «с новой страницы»).
    2. w:br[@w:type='page'] внутри runs предыдущего абзаца (вставка через Ctrl+Enter).
    3. w:lastRenderedPageBreak внутри runs предыдущего абзаца (рендер Word).
    """
    # 1. Явный атрибут pageBreakBefore на самом абзаце
    pPr = para._p.find(qn('w:pPr'))
    if pPr is not None:
        pb = pPr.find(qn('w:pageBreakBefore'))
        if pb is not None:
            val = pb.get(qn('w:val'))
            # Значение отсутствует или явно «включено»
            if val is None or val in ('1', 'true', 'on'):
                return True

    if para_idx == 0:
        return False

    prev_para = all_paragraphs[para_idx - 1]

    # 2. w:br type="page" внутри любого run предыдущего абзаца
    # ВАЖНО: w:br живёт внутри <w:r>, а не в <w:pPr>!
    for br in prev_para._p.iter(qn('w:br')):
        br_type = br.get(qn('w:type'))
        if br_type == 'page':
            return True

    # 3. w:lastRenderedPageBreak — Word иногда использует его при отображении
    for _ in prev_para._p.iter(qn('w:lastRenderedPageBreak')):
        return True

    return False


def validate_structure(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет структуру документа (С-1 … С-10).
    """
    errors: list[ReportError] = []
    all_paragraphs = doc.paragraphs  # нужен для _has_page_break_before

    def _get_effective_alignment(para) -> str | None:
        pPr = para._p.find(qn('w:pPr'))
        jc_el = pPr.find(qn('w:jc')) if pPr is not None else None
        if jc_el is not None:
            return jc_el.get(qn('w:val'))
        if para.style and para.style.paragraph_format:
            fmt = para.style.paragraph_format
            if fmt.alignment is not None:
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                mapping = {
                    WD_ALIGN_PARAGRAPH.CENTER:  "center",
                    WD_ALIGN_PARAGRAPH.LEFT:    "left",
                    WD_ALIGN_PARAGRAPH.JUSTIFY: "both",
                    WD_ALIGN_PARAGRAPH.RIGHT:   "right",
                }
                return mapping.get(fmt.alignment)
        if para.style and "Heading" in para.style.name:
            return "center"
        return None

    chapter_pat = rules.get("chapter_heading_pattern",   CHAPTER_HEADING_PATTERN)
    para_pat    = rules.get("paragraph_heading_pattern", PARAGRAPH_HEADING_PATTERN)

    # ИСПРАВЛЕНИЕ #2: список служебных названий для пропуска структурных проверок
    service_titles = SERVICE_TITLES  # используем глобальную константу

    # С-1: Обязательные разделы
    titles_lower = [
        p.text.strip().lower()
        for p in doc.paragraphs
        if p.style and p.style.name in ("Heading 1", "Heading 2")
    ]
    for section_name in rules["required_sections"]:
        if not any(section_name.lower() in t for t in titles_lower):
            errors.append(ReportError(
                id=f"С-1-{section_name}",
                code="С-1",
                type="formatting",
                severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Структура документа"),
                fragment=section_name,
                rule=f"Документ должен содержать раздел «{section_name}»",
                rule_citation="§3.2, с. 42",
                found_value="раздел отсутствует",
                expected_value=section_name,
                recommendation=f"Добавьте раздел «{section_name}» в документ",
            ))

    has_appendix = False
    appendix_ref_pattern = re.compile(r'\(прил\.\s*\d+\)', re.IGNORECASE)
    in_chapter        = False
    chapter_start_idx = None

    for para_idx, para in enumerate(doc.paragraphs):
        if not para.style or "Heading" not in para.style.name:
            # С-10: подзаголовки
            continue

        title       = para.text.strip()
        title_lower = title.lower()

        if "приложен" in title_lower:
            has_appendix = True

        is_service = any(s in title_lower for s in service_titles)

        # ── С-3: главы/служебные разделы должны начинаться с новой страницы ──
        # ИСПРАВЛЕНИЕ #3: используем исправленную функцию
        if para.style.name == "Heading 1":
            if not _has_page_break_before(para, para_idx, all_paragraphs):
                errors.append(ReportError(
                    id=f"С-3-{para_idx}",
                    code="С-3",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Заголовок «{title[:50]}»",
                    ),
                    fragment=title[:100],
                    rule="Каждый новый раздел должен начинаться с новой страницы",
                    rule_citation="§4.2, с. 47",
                    found_value="нет разрыва страницы",
                    expected_value="разрыв страницы перед разделом",
                    recommendation="Добавьте разрыв страницы (Ctrl+Enter) перед заголовком",
                ))

        # ── С-4: параграфы (H2, H3) НЕ должны начинаться с новой страницы ──
        if para.style.name in ("Heading 2", "Heading 3"):
            pPr = para._p.find(qn('w:pPr'))
            has_pb = False
            if pPr is not None:
                pb_el = pPr.find(qn('w:pageBreakBefore'))
                if pb_el is not None:
                    val = pb_el.get(qn('w:val'))
                    if val is None or val in ('1', 'true', 'on'):
                        has_pb = True
            # w:lastRenderedPageBreak внутри runs НЕ считаем ошибкой для параграфов —
            # это только рендерный маркер, он не означает принудительный разрыв.
            if has_pb:
                errors.append(ReportError(
                    id=f"С-4-{para_idx}",
                    code="С-4",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Параграф «{title[:50]}»",
                    ),
                    fragment=title[:100],
                    rule="Параграфы не должны начинаться с новой страницы",
                    rule_citation="§4.2, с. 47",
                    found_value="есть w:pageBreakBefore",
                    expected_value="нет разрыва страницы",
                    recommendation="Уберите свойство «С новой страницы» у параграфа",
                ))

        # ── С-5: формат заголовков глав ──
        # ИСПРАВЛЕНИЕ #2: служебные разделы пропускаем полностью
        if para.style.name == "Heading 1" and not is_service:
            if not re.match(chapter_pat, title):
                errors.append(ReportError(
                    id=f"С-5-{para_idx}",
                    code="С-5",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Заголовок {para_idx + 1}",
                    ),
                    fragment=title[:100],
                    rule="Заголовок главы должен соответствовать шаблону «Глава N. Название»",
                    rule_citation="§3.3, с. 43",
                    found_value=title[:100],
                    expected_value="Глава N. Название",
                    recommendation="Измените формат заголовка главы",
                ))

        # ── С-6: нумерация параграфов ──
        # ИСПРАВЛЕНИЕ #4: используем исправленный паттерн (с точкой после цифр)
        if para.style.name in ("Heading 2", "Heading 3") and not is_service:
            if not re.match(para_pat, title):
                errors.append(ReportError(
                    id=f"С-6-{para_idx}",
                    code="С-6",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Параграф {para_idx + 1}",
                    ),
                    fragment=title[:100],
                    rule="Параграфы должны иметь нумерацию вида «1.1.» или «1.1.1.»",
                    rule_citation="§4.2, с. 47",
                    found_value=title[:100],
                    expected_value="N.N. Название или N.N.N. Название",
                    recommendation="Измените формат заголовка параграфа",
                ))

        # ── С-7: заголовки без bold/italic/underline ──
        has_fmt = any(
            run.font.bold or run.font.italic or run.font.underline
            for run in para.runs
        )
        if has_fmt:
            errors.append(ReportError(
                id=f"С-7-{para_idx}",
                code="С-7",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}",
                ),
                fragment=title[:100],
                rule="Заголовки не должны быть жирными, курсивом или подчёркнутыми",
                rule_citation="§3.3, с. 43",
                found_value="bold/italic/underline",
                expected_value="обычный текст",
                recommendation="Уберите жирность, курсив и подчёркивание из заголовка",
            ))

        # ── С-8: заголовки по центру ──
        eff_align = _get_effective_alignment(para)
        if eff_align != "center":
            errors.append(ReportError(
                id=f"С-8-{para_idx}",
                code="С-8",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}",
                ),
                fragment=title[:100],
                rule="Заголовки должны быть выровнены по центру",
                rule_citation="§3.3, с. 43",
                found_value=eff_align or "не задано",
                expected_value="center",
                recommendation="Установите выравнивание заголовка по центру",
            ))

        # ── С-9: нет точки в конце заголовка ──
        if title.endswith('.'):
            errors.append(ReportError(
                id=f"С-9-{para_idx}",
                code="С-9",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}",
                ),
                fragment=title[:100],
                rule="В конце заголовка не должно быть точки",
                rule_citation="§3.3, с. 43",
                found_value=title[-10:] if len(title) > 10 else title,
                expected_value="без точки",
                recommendation="Удалите точку в конце заголовка",
            ))

        # Обновляем состояние «внутри главы» для С-10
        if para.style.name == "Heading 1":
            in_chapter        = True
            chapter_start_idx = para_idx

    # ── С-10: подзаголовки внутри параграфов ──
    in_chapter = False
    chapter_start_idx = None
    for para_idx, para in enumerate(doc.paragraphs):
        if not para.style:
            continue
        style_name = para.style.name
        title      = para.text.strip()

        if style_name == "Heading 1":
            in_chapter        = True
            chapter_start_idx = para_idx
            continue

        if in_chapter and style_name == "Heading 2":
            if not re.match(r'^\d+\.\d+', title):
                errors.append(ReportError(
                    id=f"С-10-{para_idx}",
                    code="С-10",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Подзаголовок внутри главы {chapter_start_idx}",
                    ),
                    fragment=title[:100],
                    rule="Внутри параграфов не должно быть подзаголовков без правильной нумерации",
                    rule_citation="§4.2, с. 47",
                    found_value=title[:100],
                    expected_value="нумерация вида N.N или обычный текст",
                    recommendation="Удалите подзаголовок или добавьте правильную нумерацию",
                ))

        if in_chapter and style_name in ("Heading 3", "Heading 4", "Heading 5", "Heading 6"):
            if title:
                errors.append(ReportError(
                    id=f"С-10-sub-{para_idx}",
                    code="С-10",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Подзаголовок внутри главы {chapter_start_idx}",
                    ),
                    fragment=title[:100],
                    rule="Внутри параграфов не должно быть подзаголовков",
                    rule_citation="§4.2, с. 47",
                    found_value=title[:100],
                    expected_value="обычный текст без подзаголовков",
                    recommendation="Удалите подзаголовок или оформите его как обычный текст",
                ))

    # С-2: приложения
    if has_appendix:
        full_text = "\n".join(p.text for p in doc.paragraphs)
        if not appendix_ref_pattern.search(full_text):
            errors.append(ReportError(
                id="С-2-appx-ref",
                code="С-2",
                type="formatting",
                severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Приложения"),
                fragment="Приложение",
                rule="Приложения должны иметь ссылки из текста в формате «(прил. N)»",
                rule_citation="§3.8, с. 44",
                found_value="ссылки на приложения отсутствуют",
                expected_value="(прил. N)",
                recommendation="Добавьте ссылки на приложения в тексте",
            ))

    return errors


def get_effective_font_size(run, doc) -> float | None:
    """Возвращает размер шрифта run в пт с учётом наследования."""
    if run.font.size is not None:
        return run.font.size.pt

    rPr = run._element.find(qn('w:rPr'))
    if rPr is not None:
        for tag in (qn('w:sz'), qn('w:szCs')):
            el = rPr.find(tag)
            if el is not None:
                val = el.get(qn('w:val'))
                if val:
                    try:
                        return int(val) / 2.0
                    except ValueError:
                        pass

    para = run._parent
    while para is not None and not hasattr(para, 'style'):
        para = para._parent

    if para is not None and hasattr(para, 'style') and para.style is not None:
        try:
            sz = para.style.font.size
            if sz is not None:
                return sz.pt
        except Exception:
            pass

    return 12.0


def validate_tables(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет форматирование таблиц и рисунков (Т-1…Т-12)."""
    errors: list[ReportError] = []

    body           = doc.element.body
    elements_flow  = []
    para_index     = 0

    for child in body:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            elements_flow.append(('paragraph', para_index, child))
            para_index += 1
        elif tag == 'tbl':
            tbl_idx = sum(1 for e in elements_flow if e[0] == 'table')
            elements_flow.append(('table', tbl_idx, child))

    # ── Т-1: подпись «Таблица N» над таблицей, выравнивание по правому краю ──
    table_caption_pattern = re.compile(r'^Таблица\s*\d+', re.IGNORECASE)

    for i, (etype, eidx, element) in enumerate(elements_flow):
        if etype != 'table':
            continue

        caption_found = False
        for j in range(i - 1, -1, -1):
            ptype, pidx, pelement = elements_flow[j]
            if ptype != 'paragraph':
                break
            para_text = ''.join(
                t.text for t in pelement.iter(
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
                ) if t.text
            ).strip()
            if table_caption_pattern.match(para_text):
                caption_found = True
                pPr    = pelement.find(qn('w:pPr'))
                jc_el  = pPr.find(qn('w:jc')) if pPr is not None else None
                align  = jc_el.get(qn('w:val')) if jc_el is not None else None
                if align != 'right':
                    errors.append(ReportError(
                        id=f"Т-1-caption-align-{pidx}",
                        code="Т-1",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=pidx,
                            structural_path=f"Подпись таблицы {eidx + 1}",
                        ),
                        fragment=para_text[:100],
                        rule="Подпись «Таблица N» должна быть выровнена по правому краю",
                        rule_citation="§4.5, с. 51",
                        found_value=align or "не задано",
                        expected_value="right",
                        recommendation="Установите выравнивание подписи таблицы по правому краю",
                    ))
                if para_text.endswith('.'):
                    errors.append(ReportError(
                        id=f"Т-1-caption-dot-{pidx}",
                        code="Т-1",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=pidx,
                            structural_path=f"Подпись таблицы {eidx + 1}",
                        ),
                        fragment=para_text[:100],
                        rule="В конце подписи таблицы не должно быть точки",
                        rule_citation="§4.5, с. 51",
                        found_value=para_text[-10:],
                        expected_value="без точки",
                        recommendation="Удалите точку в конце подписи таблицы",
                    ))
                break
            if para_text:
                break

        if not caption_found:
            errors.append(ReportError(
                id=f"Т-1-no-caption-{eidx}",
                code="Т-1",
                type="formatting",
                severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path=f"Таблица {eidx + 1}"),
                fragment=f"Таблица {eidx + 1}",
                rule="Над таблицей должна быть подпись «Таблица N»",
                rule_citation="§4.5, с. 51",
                found_value="подпись отсутствует или расположена неверно",
                expected_value="Таблица N над таблицей",
                recommendation="Добавьте подпись «Таблица N» непосредственно над таблицей",
            ))

    # ── Т-4: шрифт в таблицах Times New Roman 11-12 пт ──
    tables_list = list(doc.tables)
    for table_idx, table in enumerate(tables_list):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para in cell.paragraphs:
                    for run in para.runs:
                        fn = run.font.name
                        if fn and fn != "Times New Roman":
                            errors.append(ReportError(
                                id=f"Т-4-font-name-{table_idx}-{row_idx}-{cell_idx}",
                                code="Т-4",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=0,
                                    structural_path=f"Таблица {table_idx + 1}, "
                                                    f"ячейка [{row_idx + 1}, {cell_idx + 1}]",
                                ),
                                fragment=para.text[:50],
                                rule="Шрифт в таблице должен быть Times New Roman",
                                rule_citation="§4.5, с. 51",
                                found_value=fn,
                                expected_value="Times New Roman",
                                recommendation="Установите шрифт Times New Roman",
                            ))
                        fs = get_effective_font_size(run, doc)
                        if fs is not None and (fs < 11 or fs > 12):
                            errors.append(ReportError(
                                id=f"Т-4-font-size-{table_idx}-{row_idx}-{cell_idx}",
                                code="Т-4",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=0,
                                    structural_path=f"Таблица {table_idx + 1}, "
                                                    f"ячейка [{row_idx + 1}, {cell_idx + 1}]",
                                ),
                                fragment=para.text[:50],
                                rule="Размер шрифта в таблице должен быть 11-12 пт",
                                rule_citation="§4.5, с. 51",
                                found_value=str(fs),
                                expected_value="11-12",
                                recommendation="Установите размер шрифта 11-12 пт",
                            ))

    # ── Т-6: сквозная нумерация таблиц и рисунков ──
    table_numbers  = []
    figure_numbers = []
    figure_cap_pat = re.compile(r'^Рис\.?\s*(\d+)', re.IGNORECASE)

    for i, (etype, eidx, element) in enumerate(elements_flow):
        if etype != 'table':
            continue
        for j in range(i - 1, -1, -1):
            ptype, _, pelement = elements_flow[j]
            if ptype != 'paragraph':
                break
            para_text = ''.join(
                t.text for t in pelement.iter(
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
                ) if t.text
            ).strip()
            if not para_text:
                continue
            m = re.match(r'^Таблица\s*(\d+)', para_text, re.IGNORECASE)
            if m:
                table_numbers.append(int(m.group(1)))
            break

    for para in doc.paragraphs:
        m = figure_cap_pat.match(para.text.strip())
        if m:
            figure_numbers.append(int(m.group(1)))

    for nums, label in [(table_numbers, "Таблица"), (figure_numbers, "Рис.")]:
        for i, (actual, expected) in enumerate(zip(nums, range(1, len(nums) + 1))):
            if actual != expected:
                errors.append(ReportError(
                    id=f"Т-6-{label}-{i}",
                    code="Т-6",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(paragraph_index=0, structural_path=f"{label} {i + 1}"),
                    fragment=f"{label} {actual}",
                    rule=f"Нумерация {label} должна быть сквозной: 1, 2, 3, ...",
                    rule_citation="§4.4, с. 50-52",
                    found_value=str(actual),
                    expected_value=str(expected),
                    recommendation=f"Исправьте номер на {expected}",
                ))
                break

    # ── Т-12: дробные числа с запятой ──
    decimal_point_pat = re.compile(r'\b\d+\.\d+\b')
    for table_idx, table in enumerate(tables_list):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para in cell.paragraphs:
                    for match in decimal_point_pat.findall(para.text):
                        errors.append(ReportError(
                            id=f"Т-12-{table_idx}-{row_idx}-{cell_idx}",
                            code="Т-12",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=0,
                                structural_path=f"Таблица {table_idx + 1}, "
                                                f"ячейка [{row_idx + 1}, {cell_idx + 1}]",
                            ),
                            fragment=para.text[:100],
                            rule="Дробные числа должны использовать запятую, не точку",
                            rule_citation="§4.5, с. 51",
                            found_value=match,
                            expected_value=match.replace('.', ','),
                            recommendation="Замените точку на запятую в дробных числах",
                        ))

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# ИСПРАВЛЕНИЕ #5 — нумерованный список Word (w:numPr)
# ─────────────────────────────────────────────────────────────────────────────

def _get_list_number(para, doc: Document) -> int | None:
    """
    Если абзац является элементом автоматического нумерованного списка Word,
    возвращает его порядковый номер (1-based), иначе None.

    Word хранит нумерацию в w:numPr → w:numId + w:ilvl и в части numbering.xml.
    python-docx не вычисляет итоговый номер, поэтому мы считаем его сами,
    обходя документ сверху вниз.
    """
    pPr = para._p.find(qn('w:pPr'))
    if pPr is None:
        return None
    numPr = pPr.find(qn('w:numPr'))
    if numPr is None:
        return None
    numId_el = numPr.find(qn('w:numId'))
    ilvl_el  = numPr.find(qn('w:ilvl'))
    if numId_el is None:
        return None
    return (
        int(numId_el.get(qn('w:val'), 0)),
        int(ilvl_el.get(qn('w:val'), 0)) if ilvl_el is not None else 0,
    )


def _build_list_counters(doc: Document) -> dict[tuple[int, int], int]:
    """
    Проходит весь документ и строит словарь {(numId, ilvl): текущий_номер}.
    Возвращает словарь paragraph_index → номер_позиции.
    """
    counters: dict[tuple, int] = {}
    para_numbers: dict[int, int] = {}

    for idx, para in enumerate(doc.paragraphs):
        key = _get_list_number(para, doc)
        if key is None:
            continue
        num_id, ilvl = key
        # Сбрасываем счётчики более глубоких уровней при переходе на верхний
        for (nid, lvl) in list(counters.keys()):
            if nid == num_id and lvl > ilvl:
                del counters[(nid, lvl)]
        counters[(num_id, ilvl)] = counters.get((num_id, ilvl), 0) + 1
        para_numbers[idx] = counters[(num_id, ilvl)]

    return para_numbers


def validate_references_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет форматирование списка литературы (Л-1, Л-3..Л-12).
    """
    errors: list[ReportError] = []

    # Находим раздел «Список литературы»
    ref_section_paragraphs: list[str] = []
    ref_section_start_idx = 0
    in_refs = False

    for para_idx, para in enumerate(doc.paragraphs):
        if "список литературы" in para.text.lower() or \
                "библиографический список" in para.text.lower():
            in_refs = True
            ref_section_start_idx = para_idx + 1
            continue
        if in_refs and para.style and "Heading" in para.style.name:
            break
        if in_refs and para.text.strip():
            ref_section_paragraphs.append(para.text.strip())

    # ── Л-7: минимум 40 источников ──
    min_sources = rules.get("references", {}).get("min_sources", 40)
    if len(ref_section_paragraphs) < min_sources:
        errors.append(ReportError(
            id="Л-7-count",
            code="Л-7",
            type="formatting",
            severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Список литературы"),
            fragment="Список литературы",
            rule=f"Список литературы должен содержать не менее {min_sources} источников",
            rule_citation="§3.7, с. 44",
            found_value=str(len(ref_section_paragraphs)),
            expected_value=str(min_sources),
            recommendation="Добавьте недостающие источники в список литературы",
        ))

    # ── ИСПРАВЛЕНИЕ #5: определяем, использует ли список автонумерацию Word ──
    # Собираем para-объекты секции
    end_idx = len(doc.paragraphs)
    ref_paras: list[tuple[int, Any]] = []  # (global_idx, para)
    in_refs2 = False
    for para_idx, para in enumerate(doc.paragraphs):
        if "список литературы" in para.text.lower() or \
                "библиографический список" in para.text.lower():
            in_refs2 = True
            continue
        if in_refs2 and para.style and "Heading" in para.style.name:
            end_idx = para_idx
            break
        if in_refs2 and para.text.strip():
            ref_paras.append((para_idx, para))

    # Проверяем, есть ли у абзацев автонумерация (w:numPr)
    auto_numbered_paras = []
    manual_numbered_paras = []

    numbering_pattern = re.compile(r'^(\d+)[\.\)]\s')

    list_counters = _build_list_counters(doc)

    for global_idx, para in ref_paras:
        text = para.text.strip()
        pPr  = para._p.find(qn('w:pPr'))
        has_numPr = pPr is not None and pPr.find(qn('w:numPr')) is not None

        if has_numPr:
            auto_numbered_paras.append((global_idx, para, text))
        elif numbering_pattern.match(text):
            manual_numbered_paras.append((global_idx, para, text))

    uses_auto_numbering = len(auto_numbered_paras) > len(manual_numbered_paras)

    if uses_auto_numbering:
        # ИСПРАВЛЕНИЕ #5: при автонумерации проверяем непрерывность счётчика w:numPr
        if auto_numbered_paras:
            # Берём numId первого элемента
            first_pPr   = auto_numbered_paras[0][1]._p.find(qn('w:pPr'))
            first_numPr = first_pPr.find(qn('w:numPr'))
            numId_el    = first_numPr.find(qn('w:numId')) if first_numPr is not None else None
            ilvl_el     = first_numPr.find(qn('w:ilvl')) if first_numPr is not None else None
            numId = int(numId_el.get(qn('w:val'), 0)) if numId_el is not None else None
            ilvl  = int(ilvl_el.get(qn('w:val'), 0))  if ilvl_el  is not None else 0

            # Проверяем, что все элементы принадлежат одному списку
            for seq, (global_idx, para, text) in enumerate(auto_numbered_paras, start=1):
                expected_num = list_counters.get(global_idx)
                if expected_num is not None and expected_num != seq:
                    errors.append(ReportError(
                        id=f"Л-5-auto-{global_idx}",
                        code="Л-5",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=global_idx,
                            structural_path="Список литературы",
                        ),
                        fragment=text[:100],
                        rule="Нумерация источников должна быть сплошной: 1, 2, 3, ...",
                        rule_citation="§4.5, с. 52",
                        found_value=str(expected_num),
                        expected_value=str(seq),
                        recommendation="Исправьте нумерацию автосписка",
                    ))
                    break
    else:
        # Ручная нумерация — проверяем как раньше
        source_numbers: list[int] = []
        has_numbering = False

        for idx_txt, (global_idx, para, text) in enumerate(ref_paras):
            m = numbering_pattern.match(text)
            if m:
                source_numbers.append(int(m.group(1)))
                has_numbering = True

        if not has_numbering and ref_paras:
            errors.append(ReportError(
                id="Л-5-no-numbering",
                code="Л-5",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx,
                    structural_path="Список литературы",
                ),
                fragment=ref_paras[0][2][:100] if ref_paras else "Список литературы",
                rule="Источники в списке литературы должны иметь сквозную нумерацию",
                rule_citation="§4.5, с. 52",
                found_value="нумерация отсутствует",
                expected_value="1, 2, 3, ...",
                recommendation="Добавьте нумерацию к каждому источнику",
            ))
        elif source_numbers:
            for i, (actual, expected) in enumerate(
                zip(source_numbers, range(1, len(source_numbers) + 1))
            ):
                if actual != expected:
                    errors.append(ReportError(
                        id=f"Л-5-num-{i}",
                        code="Л-5",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=ref_section_start_idx + i,
                            structural_path="Список литературы",
                        ),
                        fragment=ref_section_paragraphs[i][:100],
                        rule="Нумерация источников должна быть сплошной: 1, 2, 3, ...",
                        rule_citation="§4.5, с. 52",
                        found_value=str(actual),
                        expected_value=str(expected),
                        recommendation=f"Исправьте номер источника на {expected}",
                    ))
                    break

    # ── Л-4: алфавитный порядок ──
    def extract_surname(text: str) -> tuple[str, str]:
        clean = re.sub(r'^\d+[\.\)]\s*', '', text.strip())
        author_part = re.split(r'[,.]', clean)[0].strip()
        is_cyr = bool(re.search(r'[А-ЯЁа-яё]', author_part))
        return (author_part.lower(), 'cyrillic' if is_cyr else 'latin')

    def surname_sort_key(item):
        _, text = item
        surname, lang = extract_surname(text)
        return (0 if lang == 'cyrillic' else 1, surname)

    if len(ref_section_paragraphs) > 1:
        indexed = list(enumerate(ref_section_paragraphs))
        sorted_ = sorted(indexed, key=surname_sort_key)
        for i, (oi, _) in enumerate(indexed):
            si, _ = sorted_[i]
            if oi != si:
                cs, _ = extract_surname(ref_section_paragraphs[oi])
                ns, _ = extract_surname(ref_section_paragraphs[si])
                errors.append(ReportError(
                    id=f"Л-4-order-{i}",
                    code="Л-4",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_section_start_idx + oi,
                        structural_path="Список литературы",
                    ),
                    fragment=ref_section_paragraphs[oi][:100],
                    rule="Источники — по алфавиту: сначала русские, затем иностранные",
                    rule_citation="§4.5, с. 52",
                    found_value=f"«{cs}» после «{ns}»",
                    expected_value=f"«{ns}» перед «{cs}»",
                    recommendation="Расположите источники в алфавитном порядке",
                ))
                break

    # ── Л-8: актуальность источников (70 % за последние 10 лет) ──
    current_year   = datetime.now().year
    year_threshold = current_year - rules.get("references", {}).get("max_years_old", 10)
    year_pat       = re.compile(r'\b(19|20)\d{2}\b')
    recent = total_with_year = 0

    for text in ref_section_paragraphs:
        m = year_pat.search(text)
        if m:
            total_with_year += 1
            if int(m.group(0)) >= year_threshold:
                recent += 1

    if total_with_year > 0 and (recent / total_with_year) < 0.70:
        errors.append(ReportError(
            id="Л-8-recency",
            code="Л-8",
            type="formatting",
            severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Список литературы"),
            fragment="Список литературы",
            rule="Не менее 70 % источников должны быть за последние 10 лет",
            rule_citation="§4.5, с. 52",
            found_value=f"{recent / total_with_year * 100:.1f}%",
            expected_value=">= 70%",
            recommendation="Добавьте более свежие источники",
        ))

    # ── Л-9: формат автора «Фамилия, И. О.» ──
    author_pats = [
        r'[А-ЯЁ][а-яё]+\s*,\s*[А-ЯЁ]\.\s*[А-ЯЁ]\.',
        r'[A-Z][a-z]+\s*,\s*[A-Z]\.\s*[A-Z]\.',
    ]
    author_start = re.compile(r'^(\d+[\.\)]\s*)?([А-ЯЁ][а-яё]{2,})\s*,?\s*[А-ЯЁ]\.')

    for idx, text in enumerate(ref_section_paragraphs):
        if not author_start.match(text):
            continue
        if not any(re.search(p, text) for p in author_pats):
            errors.append(ReportError(
                id=f"Л-9-author-{idx}",
                code="Л-9",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы",
                ),
                fragment=text[:100],
                rule="Автор указывается как: Фамилия, И. О.",
                rule_citation="§4.5, с. 52",
                found_value=text[:50],
                expected_value="Фамилия, И. О.",
                recommendation="Исправьте формат указания автора",
            ))

    # ── Л-10: URL с датой обращения ──
    url_pat    = re.compile(r'https?://\S+')
    access_pat = re.compile(r'\(дата обращения:\s*\d{2}\.\d{2}\.\d{4}\)')

    for idx, text in enumerate(ref_section_paragraphs):
        if url_pat.search(text) and not access_pat.search(text):
            errors.append(ReportError(
                id=f"Л-10-url-{idx}",
                code="Л-10",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы",
                ),
                fragment=text[:100],
                rule="Для URL-источников укажите дату обращения: (дата обращения: ДД.ММ.ГГГГ)",
                rule_citation="§4.5, с. 52",
                found_value="URL без даты обращения",
                expected_value="(дата обращения: ДД.ММ.ГГГГ)",
                recommendation="Добавьте дату обращения после URL",
            ))

    # ── Л-11: ссылки в тексте соответствуют источникам ──
    # Собираем валидные номера: из автосписка или ручного
    valid_nums: set[int] = set()
    if uses_auto_numbering:
        valid_nums = set(range(1, len(auto_numbered_paras) + 1))
    else:
        valid_nums = set(source_numbers) if 'source_numbers' in dir() else set()

    ref_inline_pat = re.compile(r'\[(\d+)(?:\s*,\s*с\.\s*\d+)?\]')
    for para_idx, para in enumerate(doc.paragraphs):
        for m in ref_inline_pat.finditer(para.text):
            n = int(m.group(1))
            if valid_nums and n not in valid_nums:
                errors.append(ReportError(
                    id=f"Л-11-ref-{para_idx}-{n}",
                    code="Л-11",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Абзац {para_idx + 1}",
                    ),
                    fragment=m.group(0),
                    rule="Ссылка в тексте должна соответствовать источнику в списке",
                    rule_citation="§4.3, с. 49",
                    found_value=f"№{n}",
                    expected_value=f"номер от 1 до {len(valid_nums)}",
                    recommendation=f"Добавьте источник №{n} или исправьте ссылку",
                ))

    # ── Л-12: длинные тире в библиографии ──
    hyphen_dash = re.compile(r'\s-\s|\d-\d')
    for idx, text in enumerate(ref_section_paragraphs):
        if hyphen_dash.search(text):
            errors.append(ReportError(
                id=f"Л-12-{idx}",
                code="Л-12",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы",
                ),
                fragment=text[:100],
                rule="В библиографии используйте длинное тире «–», не дефис «-»",
                rule_citation="§4.5, с. 52",
                found_value="-",
                expected_value="–",
                recommendation="Замените дефис на длинное тире",
            ))

    # ── Л-1: ссылки в квадратных скобках, не в круглых ──
    round_brackets = re.compile(r'\(\d+\)')
    for para_idx, para in enumerate(doc.paragraphs):
        matches = round_brackets.findall(para.text)
        if matches:
            errors.append(ReportError(
                id=f"Л-1-{para_idx}",
                code="Л-1",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Абзац {para_idx + 1}",
                ),
                fragment=para.text[:100],
                rule="Ссылки оформляются в квадратных скобках: [N] или [N, с. X]",
                rule_citation="§4.3, с. 49",
                found_value=matches[0],
                expected_value="[N] или [N, с. X]",
                recommendation="Замените круглые скобки на квадратные",
            ))

    # ── Л-3: порядок множественных ссылок ──
    multi_pat = re.compile(r'\[(\d+(?:;\s*\d+)+)\]')
    for para_idx, para in enumerate(doc.paragraphs):
        for m in multi_pat.finditer(para.text):
            nums = [int(n.strip()) for n in m.group(1).split(';')]
            if nums != sorted(nums):
                errors.append(ReportError(
                    id=f"Л-3-{para_idx}",
                    code="Л-3",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Абзац {para_idx + 1}",
                    ),
                    fragment=m.group(0),
                    rule="Несколько источников — в порядке возрастания через ';'",
                    rule_citation="§4.3, с. 49",
                    found_value=m.group(0),
                    expected_value=f"[{'; '.join(str(n) for n in sorted(nums))}]",
                    recommendation="Расположите номера источников по возрастанию",
                ))

    return errors


def validate_volume(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет объём работы по количеству знаков (Ф-11..Ф-13)."""
    errors: list[ReportError] = []

    volume_rules  = rules.get("volume", {})
    total_min     = volume_rules.get("total_chars_min",            90000)
    total_max     = volume_rules.get("total_chars_max",           108000)
    theory_min    = volume_rules.get("theory_chapter_chars_min",   27000)
    theory_max    = volume_rules.get("theory_chapter_chars_max",   36000)
    empirical_min = volume_rules.get("empirical_chapter_chars_min",45000)
    empirical_max = volume_rules.get("empirical_chapter_chars_max",54000)

    current_section = None
    section_texts: dict[str, list[str]] = {}
    all_text: list[str] = []

    for para in doc.paragraphs:
        if para.style and para.style.name in ("Heading 1", "Heading 2"):
            t = para.text.strip()
            tl = t.lower()
            if tl.startswith("глава 1"):
                current_section = "Глава 1"
            elif tl.startswith("глава 2"):
                current_section = "Глава 2"
            elif tl in SERVICE_TITLES:
                current_section = tl
            else:
                current_section = t
        elif para.text.strip():
            all_text.append(para.text)
            if current_section:
                section_texts.setdefault(current_section, []).append(para.text)

    total_chars = len("".join(all_text))
    if total_chars < total_min:
        errors.append(ReportError(
            id="Ф-11-below-min", code="Ф-11", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Документ целиком"),
            fragment=f"Общий объём: {total_chars} знаков",
            rule=f"Объём ВКР: от {total_min} до {total_max} знаков с пробелами",
            rule_citation="§4.1, с. 46",
            found_value=str(total_chars), expected_value=f"{total_min}-{total_max}",
            recommendation=f"Добавьте текст. Не хватает {total_min - total_chars} знаков.",
        ))
    elif total_chars > total_max:
        errors.append(ReportError(
            id="Ф-11-above-max", code="Ф-11", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Документ целиком"),
            fragment=f"Общий объём: {total_chars} знаков",
            rule=f"Объём ВКР: от {total_min} до {total_max} знаков с пробелами",
            rule_citation="§4.1, с. 46",
            found_value=str(total_chars), expected_value=f"{total_min}-{total_max}",
            recommendation=f"Сократите текст. Превышение на {total_chars - total_max} знаков.",
        ))

    for chapter_key, code, cmin, cmax, label in [
        ("Глава 1", "Ф-12", theory_min,    theory_max,    "Теоретическая глава"),
        ("Глава 2", "Ф-13", empirical_min, empirical_max, "Эмпирическая глава"),
    ]:
        ch_text  = "".join(section_texts.get(chapter_key, []))
        ch_chars = len(ch_text)
        if ch_chars == 0:
            continue
        if ch_chars < cmin:
            errors.append(ReportError(
                id=f"{code}-below-min", code=code, type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path=chapter_key),
                fragment=f"{chapter_key}: {ch_chars} знаков",
                rule=f"{label}: от {cmin} до {cmax} знаков",
                rule_citation="§3.4, с. 23",
                found_value=str(ch_chars), expected_value=f"{cmin}-{cmax}",
                recommendation=f"Расширьте {chapter_key}. Не хватает {cmin - ch_chars} знаков.",
            ))
        elif ch_chars > cmax:
            errors.append(ReportError(
                id=f"{code}-above-max", code=code, type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path=chapter_key),
                fragment=f"{chapter_key}: {ch_chars} знаков",
                rule=f"{label}: от {cmin} до {cmax} знаков",
                rule_citation="§3.4, с. 23",
                found_value=str(ch_chars), expected_value=f"{cmin}-{cmax}",
                recommendation=f"Сократите {chapter_key}. Превышение на {ch_chars - cmax} знаков.",
            ))

    return errors


def validate_typography_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет типографику текста (Н-2, Н-4, Н-5, Н-6, Н-7)."""
    errors: list[ReportError] = []

    no_space_pat      = re.compile(r'[А-ЯЁ]\.[А-ЯЁ]\.[А-ЯЁ][а-яё]+')
    wrong_quotes      = re.compile(r'"[^"]*"')
    abbrev_pat        = re.compile(r'\b[А-ЯЁ]{2,}\b')
    explained_pat     = re.compile(r'\([А-ЯЁ]{2,}\)')
    hyphen_nums       = re.compile(r'(\d)\s*-\s*(\d)')
    manual_num_pat    = re.compile(r'^\s*\d+\.\s+')
    bullet_markers    = ['•', '-', '◦', '▪', '‣', '⁃']

    found_abbrevs: set[str] = set()
    in_list           = False
    list_marker_type  = None

    for para_idx, para in enumerate(doc.paragraphs):
        # ИСПРАВЛЕНИЕ #2: не проверяем заголовки на типографику
        if _is_heading_paragraph(para):
            continue

        text = para.text

        # Н-2
        m = no_space_pat.search(text)
        if m:
            errors.append(ReportError(
                id=f"Н-2-{para_idx}", code="Н-2", type="style", severity="warning",
                location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                fragment=text[:100],
                rule="Между инициалами должен быть пробел: И. И. Иванов",
                rule_citation="§4.2, с. 48",
                found_value=m.group(0), expected_value="И. И. Иванов",
                recommendation="Добавьте пробелы между инициалами",
            ))

        # Н-4
        if wrong_quotes.search(text):
            errors.append(ReportError(
                id=f"Н-4-{para_idx}", code="Н-4", type="style", severity="warning",
                location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                fragment=text[:100],
                rule='Кавычки должны быть угловыми: «текст»',
                rule_citation="§4.2, с. 48",
                found_value='"..."', expected_value='«...»',
                recommendation='Замените кавычки "..." на «...»',
            ))

        # Н-5
        hm = hyphen_nums.search(text)
        if hm:
            errors.append(ReportError(
                id=f"Н-5-{para_idx}", code="Н-5", type="style", severity="warning",
                location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                fragment=text[:100],
                rule="Между числами/датами используйте тире (–), не дефис (-)",
                rule_citation="§4.2, с. 48",
                found_value=hm.group(0), expected_value="число – число",
                recommendation="Замените дефис на тире",
            ))

        # Н-7: ручная нумерация
        if manual_num_pat.match(text):
            pPr = para._p.pPr
            if pPr is None or pPr.find(qn('w:numPr')) is None:
                errors.append(ReportError(
                    id=f"Н-7-manual-{para_idx}", code="Н-7", type="style", severity="warning",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                    fragment=text[:100],
                    rule="Используйте автоматическую нумерацию списков",
                    rule_citation="§4.2, с. 48",
                    found_value="ручная нумерация", expected_value="автоматическая нумерация",
                    recommendation="Используйте автоматическую нумерацию",
                ))

        # Н-7: смешанные маркеры
        stripped = text.strip()
        cur_marker = next((mk for mk in bullet_markers if stripped.startswith(mk)), None)
        if cur_marker:
            if not in_list:
                in_list = True
                list_marker_type = cur_marker
            elif list_marker_type != cur_marker:
                errors.append(ReportError(
                    id=f"Н-7-mixed-{para_idx}", code="Н-7", type="style", severity="warning",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                    fragment=text[:100],
                    rule="В одном списке — единый маркер",
                    rule_citation="§4.2, с. 48",
                    found_value=f"маркер '{cur_marker}'", expected_value=f"маркер '{list_marker_type}'",
                    recommendation="Используйте одинаковые маркеры во всём списке",
                ))
        else:
            in_list = False
            list_marker_type = None

        # Расшифровки аббревиатур
        for em in explained_pat.finditer(text):
            found_abbrevs.add(em.group(0)[1:-1])

        # Н-6
        for am in abbrev_pat.finditer(text):
            abbrev = am.group(0)
            if abbrev not in found_abbrevs:
                errors.append(ReportError(
                    id=f"Н-6-{para_idx}-{abbrev}", code="Н-6", type="style", severity="warning",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                    fragment=text[:100],
                    rule="При первом использовании аббревиатуры дайте расшифровку: полное название (АБВ)",
                    rule_citation="§4.1, с. 46",
                    found_value=abbrev, expected_value=f"полное название ({abbrev})",
                    recommendation=f"Расшифруйте аббревиатуру {abbrev} при первом использовании",
                ))
                found_abbrevs.add(abbrev)

    return errors


def validate_toc(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет содержание (Со-1)."""
    errors: list[ReportError] = []

    SKIP = {"содержани", "оглавлени"}
    headings_to_check: list[tuple[int, str]] = []
    for para_idx, para in enumerate(doc.paragraphs):
        if para.style and para.style.name in ("Heading 1", "Heading 2"):
            title = para.text.strip()
            if not title:
                continue
            if any(s in title.lower() for s in SKIP):
                continue
            headings_to_check.append((para_idx, title))

    toc_start = toc_end = None
    for para_idx, para in enumerate(doc.paragraphs):
        tl = para.text.lower()
        if any(s in tl for s in SKIP):
            toc_start = para_idx
            continue
        if toc_start is not None and toc_end is None:
            if para.style and para.style.name == "Heading 1":
                toc_end = para_idx
                break

    if toc_start is None:
        if headings_to_check:
            errors.append(ReportError(
                id="Со-1-no-toc", code="Со-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Структура документа"),
                fragment="Содержание отсутствует",
                rule="Документ должен содержать раздел «Содержание» со всеми заголовками",
                rule_citation="§3.2, с. 12",
                found_value="раздел Содержание отсутствует",
                expected_value="раздел Содержание с перечнем всех заголовков",
                recommendation="Добавьте раздел «Содержание» после титульного листа",
            ))
        return errors

    end = toc_end if toc_end else len(doc.paragraphs)
    toc_paras = [
        doc.paragraphs[i].text.strip()
        for i in range(toc_start + 1, end)
        if doc.paragraphs[i].text.strip()
    ]

    has_toc_field = any(
        'TOC' in p._p.xml or 'w:fldChar' in p._p.xml
        for p in doc.paragraphs[toc_start:end]
    )
    if has_toc_field:
        return errors

    if not toc_paras:
        errors.append(ReportError(
            id="Со-1-empty-toc", code="Со-1", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=toc_start, structural_path="Содержание"),
            fragment="Содержание пустое",
            rule="Содержание должно отражать все заголовки с номерами страниц",
            rule_citation="§3.2, с. 12",
            found_value="содержание пустое", expected_value="перечень всех заголовков",
            recommendation="Заполните содержание или используйте автоматическое оглавление Word",
        ))
        return errors

    def heading_in_toc(title: str, lines: list[str]) -> bool:
        tn = re.sub(r'\s+', ' ', title.lower().strip())
        for line in lines:
            if tn in re.sub(r'\s+', ' ', line.lower()):
                return True
        words = [w for w in tn.split() if len(w) > 3]
        if not words:
            return True
        for line in lines:
            ln = re.sub(r'\s+', ' ', line.lower())
            if sum(1 for w in words if w in ln) / len(words) >= 0.7:
                return True
        return False

    for hidx, title in headings_to_check:
        if not heading_in_toc(title, toc_paras):
            errors.append(ReportError(
                id=f"Со-1-{hidx}", code="Со-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=hidx, structural_path=f"Заголовок «{title[:50]}»"),
                fragment=title[:100],
                rule="Все заголовки должны быть отражены в содержании",
                rule_citation="§3.2, с. 12",
                found_value=f"«{title}» не найден в содержании",
                expected_value="заголовок присутствует в содержании",
                recommendation="Добавьте заголовок в содержание или обновите автооглавление",
            ))

    return errors


def validate_appendix(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет оформление приложений (П-1..П-4)."""
    errors: list[ReportError] = []

    app_heading_pat = re.compile(r'^Приложение\s+([А-ЯЁA-Z\d])\s*$', re.IGNORECASE)
    app_ref_pat     = re.compile(
        r'(?:прил\.\s*([А-ЯЁA-Z\d]+)|\bприложени[еяю]\s+([А-ЯЁA-Z\d]+))',
        re.IGNORECASE,
    )

    all_paragraphs = doc.paragraphs

    def _align(para) -> str | None:
        pPr   = para._p.find(qn('w:pPr'))
        jc_el = pPr.find(qn('w:jc')) if pPr is not None else None
        if jc_el is not None:
            return jc_el.get(qn('w:val'))
        if para.style and para.style.paragraph_format:
            from docx.enum.text import WD_ALIGN_PARAGRAPH as WDA
            mapping = {WDA.RIGHT: "right", WDA.CENTER: "center",
                       WDA.LEFT: "left", WDA.JUSTIFY: "both"}
            return mapping.get(para.style.paragraph_format.alignment)
        return None

    # Порядок ссылок
    refs_order: list[str] = []
    seen_refs: set[str]   = set()
    for para in doc.paragraphs:
        if app_heading_pat.match(para.text.strip()):
            continue
        for m in app_ref_pat.finditer(para.text):
            letter = (m.group(1) or m.group(2) or "").upper().strip()
            if letter and letter not in seen_refs:
                refs_order.append(letter)
                seen_refs.add(letter)

    appendices: list[dict] = []
    paras = doc.paragraphs

    for i, para in enumerate(paras):
        m = app_heading_pat.match(para.text.strip())
        if not m:
            continue
        letter = m.group(1).upper()

        # П-1: разрыв страницы — используем исправленную функцию
        if not _has_page_break_before(para, i, all_paragraphs):
            errors.append(ReportError(
                id=f"П-1-{i}", code="П-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=i, structural_path=f"Приложение {letter}"),
                fragment=para.text.strip()[:100],
                rule="Каждое приложение начинается с новой страницы",
                rule_citation="§4.6, с. 59",
                found_value="нет разрыва страницы", expected_value="разрыв страницы",
                recommendation="Поставьте курсор перед «Приложение» и нажмите Ctrl+Enter",
            ))

        # П-2: выравнивание по правому краю
        if _align(para) != "right":
            errors.append(ReportError(
                id=f"П-2-{i}", code="П-2", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=i, structural_path=f"Приложение {letter}"),
                fragment=para.text.strip()[:100],
                rule="«Приложение N» — выравнивание по правому краю",
                rule_citation="§4.6, с. 59",
                found_value=_align(para) or "не задано", expected_value="right",
                recommendation="Выделите строку «Приложение N» → По правому краю",
            ))

        # Название приложения
        j = i + 1
        while j < len(paras) and not paras[j].text.strip():
            j += 1
        if j < len(paras):
            np_ = paras[j]
            nt  = np_.text.strip()
            if not app_heading_pat.match(nt) and not (np_.style and np_.style.name == "Heading 1"):
                if _align(np_) != "center":
                    errors.append(ReportError(
                        id=f"П-3-align-{j}", code="П-3", type="formatting", severity="error",
                        location=ErrorLocation(paragraph_index=j, structural_path=f"Название приложения {letter}"),
                        fragment=nt[:100],
                        rule="Название приложения — по центру",
                        rule_citation="§4.6, с. 59",
                        found_value=_align(np_) or "не задано", expected_value="center",
                        recommendation="Выделите название → По центру",
                    ))
                if nt.endswith('.'):
                    errors.append(ReportError(
                        id=f"П-3-dot-{j}", code="П-3", type="formatting", severity="error",
                        location=ErrorLocation(paragraph_index=j, structural_path=f"Название приложения {letter}"),
                        fragment=nt[:100],
                        rule="Название приложения не заканчивается точкой",
                        rule_citation="§4.6, с. 59",
                        found_value=nt[-10:], expected_value="без точки",
                        recommendation="Удалите точку в конце названия приложения",
                    ))

        appendices.append({"idx": i, "letter": letter})

    # П-4: порядок
    if refs_order and appendices:
        app_letters = [a["letter"] for a in appendices]
        filtered    = [r for r in refs_order if r in app_letters]
        if filtered and filtered != app_letters[:len(filtered)]:
            errors.append(ReportError(
                id="П-4-order", code="П-4", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=appendices[0]["idx"], structural_path="Приложения"),
                fragment=f"В документе: {', '.join(app_letters)}",
                rule="Приложения нумеруются в порядке упоминания в тексте",
                rule_citation="§4.6, с. 59",
                found_value=f"в документе: {', '.join(app_letters)}",
                expected_value=f"по ссылкам: {', '.join(filtered)}",
                recommendation="Переставьте приложения в порядке их упоминания в тексте",
            ))
        missing = [r for r in refs_order if r not in app_letters]
        if missing:
            errors.append(ReportError(
                id="П-4-missing", code="П-4", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=appendices[0]["idx"], structural_path="Приложения"),
                fragment=f"Отсутствуют: {', '.join(missing)}",
                rule="Все упомянутые приложения должны присутствовать в документе",
                rule_citation="§4.6, с. 59",
                found_value=f"отсутствуют {', '.join(missing)}",
                expected_value=f"добавить {', '.join(missing)}",
                recommendation="Добавьте отсутствующие приложения или исправьте ссылки",
            ))

    return errors


def validate_repeated_references(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Л-2: повторная ссылка — [там же, с. X]."""
    errors: list[ReportError] = []

    ref_with_page  = re.compile(r'\[(\d+),\s*с\.\s*(\d+)\]')
    correct_repeat = re.compile(r'\[там же(?:,\s*с\.\s*\d+)?\]', re.IGNORECASE)

    paras = doc.paragraphs
    for para_idx, para in enumerate(paras):
        text = para.text

        refs_in_para: dict[str, list[str]] = {}
        for m in ref_with_page.finditer(text):
            refs_in_para.setdefault(m.group(1), []).append(m.group(2))

        for src, pages in refs_in_para.items():
            if len(pages) > 1 and not correct_repeat.search(text):
                errors.append(ReportError(
                    id=f"Л-2-same-{para_idx}-{src}", code="Л-2", type="formatting", severity="error",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx + 1}"),
                    fragment=text[:100],
                    rule="Повторная ссылка на тот же источник в абзаце: [там же, с. X]",
                    rule_citation="§4.3, с. 49",
                    found_value=f"[{src}, с. {pages[0]}]...[{src}, с. {pages[1]}]",
                    expected_value=f"[{src}, с. {pages[0]}]...[там же, с. {pages[1]}]",
                    recommendation="Замените второй [N, с. X] на [там же, с. X]",
                ))

        if para_idx + 1 >= len(paras):
            continue
        last_src = None
        for m in ref_with_page.finditer(text):
            last_src = m.group(1)
        if last_src is None:
            continue
        next_text = paras[para_idx + 1].text
        fm = re.match(r'^\s*\[(\d+),\s*с\.\s*\d+\]', next_text)
        if fm and fm.group(1) == last_src and not correct_repeat.search(next_text):
            errors.append(ReportError(
                id=f"Л-2-next-{para_idx + 1}-{last_src}", code="Л-2", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=para_idx + 1, structural_path=f"Абзац {para_idx + 2}"),
                fragment=next_text[:100],
                rule="Повторная ссылка в следующем абзаце: [там же, с. X]",
                rule_citation="§4.3, с. 49",
                found_value=fm.group(0), expected_value="[там же, с. X]",
                recommendation="Замените ссылку на [там же, с. X]",
            ))

    return errors


def validate_list_numbering(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Л-5: сплошная нумерация источников.
    Делегирует в validate_references_format — здесь оставлена для обратной совместимости.
    """
    return []


def validate_format(docx_path: str, rules: dict[str, Any]) -> ValidationReport:
    """Выполняет полную валидацию DOCX-документа."""
    doc    = Document(docx_path)
    errors: list[ReportError] = []

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