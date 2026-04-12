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
# Константы
# ─────────────────────────────────────────────────────────────────────────────

HEADING_STYLES = {
    "Heading 1", "Heading 2", "Heading 3",
    "Heading 4", "Heading 5", "Heading 6",
}

SERVICE_TITLES = [
    "введение", "заключение", "список литературы",
    "содержание", "оглавление", "библиографический список",
    "выводы", "приложения", "приложение",
]

# Паттерн главы: «1. Название» или «Глава 1. Название» (арабские или римские цифры)
# Основное требование: начинается с числа (арабского или римского), затем точка и текст
CHAPTER_HEADING_PATTERN = r"^(?:Глава\s+)?(?:\d+|[IVX]+)\.?\s.+[^.]$"
# Паттерн параграфа — «2.1. Текст» или «2.1 Текст» (без точки в конце)
PARAGRAPH_HEADING_PATTERN = r"^\d+\.\d+(?:\.\d+)?\.?\s.+[^.]$"


def _is_heading_paragraph(para,
                           chapter_pat: str = CHAPTER_HEADING_PATTERN,
                           para_pat: str = PARAGRAPH_HEADING_PATTERN) -> bool:
    """True если абзац является заголовком."""
    if para.style and para.style.name in HEADING_STYLES:
        return True
    pPr = para._p.pPr
    if pPr is not None and pPr.find(qn('w:outlineLvl')) is not None:
        return True
    text = para.text.strip()
    if not text:
        return False
    tl = text.lower()
    
    # FIX: проверяем служебные заголовки только как полные заголовки, а не как подстроку в тексте
    # Служебный заголовок должен состоять ТОЛЬКО из ключевого слова (возможно с номером или буквой)
    for service in SERVICE_TITLES:
        # Точное совпадение или с номером/буквой (например, "Приложение 1", "Приложение А")
        if re.match(rf'^{re.escape(service)}(\s+\d+)?(\s+[А-ЯA-Z])?$', tl, re.IGNORECASE):
            return True
    
    if re.match(chapter_pat, text) or re.match(para_pat, text):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# FIX #7: корректная проверка межстрочного интервала
# Word при lineRule="auto": 240=одинарный, 360=полуторный, 480=двойной
# Word при lineRule="exact"/"atLeast": значение в twips буквально
# ГОСТ-документы задают ЛИБО 360 (auto), ЛИБО 420 (exact) для 1.5 интервала
# ─────────────────────────────────────────────────────────────────────────────

def _is_line_spacing_15(line_val: int, line_rule: str | None, tolerance: int) -> bool:
    """True если межстрочный интервал соответствует 1.5."""
    # 360 twips при lineRule=auto — стандартный полуторный
    # 420 twips при lineRule=exact — явные 21пт (старый способ)
    for target in (360, 420):
        if abs(line_val - target) <= tolerance:
            return True
    return False


def _has_different_first_page(doc: Document) -> bool:
    """Проверяет, установлен ли флаг 'разная первая страница'."""
    section = doc.sections[0]
    return section._sectPr.titlePg is not None


def _get_first_content_paragraph_index(doc: Document,
                                        chapter_pat: str = CHAPTER_HEADING_PATTERN,
                                        para_pat: str = PARAGRAPH_HEADING_PATTERN) -> int:
    """Возвращает индекс первого содержательного абзаца (после титульного листа)."""
    # Считаем что первая страница (титульник) заканчивается перед первым заголовком раздела
    # или служебным разделом (введение, содержание и т.д.)
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip().lower()
        # Ищем первый заголовок раздела или служебный раздел (введение, заключение и т.д.)
        if any(s in text for s in SERVICE_TITLES):
            return i
        if re.match(chapter_pat, para.text.strip()):
            return i
        if re.match(para_pat, para.text.strip()):
            return i
    # Если не нашли заголовков разделов, начинаем проверку со второго абзаца (считая что первый - титульник)
    # Пропускаем первый непустой абзац (титульник) и все пустые после него
    found_first_non_empty = False
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            if not found_first_non_empty:
                found_first_non_empty = True
                continue
            return i
    return 0


def _is_list_paragraph(para) -> bool:
    """True если абзац является элементом маркированного или нумерованного списка."""
    # Проверяем w:numPr — признак автоматического списка
    pPr = para._p.pPr
    if pPr is not None and pPr.find(qn('w:numPr')) is not None:
        return True
    # Проверяем ручные маркеры списков
    text = para.text.strip()
    if text.startswith(('-', '•', '◦', '▪', '‣', '⁃', '*')):
        return True
    # Проверяем ручную нумерацию (1., 2., а), б) и т.д.)
    if re.match(r'^\d+[\.\)]\s', text) or re.match(r'^[а-яё]\)\s', text, re.IGNORECASE):
        return True
    return False


def check_paragraph_formatting(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет форматирование абзацев (Ф-2, Ф-3, Ф-5, Ф-6)."""
    errors: list[ReportError] = []

    tolerance_dxa       = rules["tolerances"]["dxa"]   # 20
    expected_first_line = 720                           # DXA
    expected_ba         = 0                             # twips (before/after)

    chapter_pat = rules.get("chapter_heading_pattern",   CHAPTER_HEADING_PATTERN)
    para_pat    = rules.get("paragraph_heading_pattern", PARAGRAPH_HEADING_PATTERN)

    # Всегда пропускаем первую страницу (титульный лист)
    skip_first_page = True
    first_content_idx = _get_first_content_paragraph_index(doc, chapter_pat, para_pat)

    for para_index, para in enumerate(doc.paragraphs):
        # Пропускаем абзацы на первой странице
        if skip_first_page and para_index < first_content_idx:
            continue
        # FIX #1: пропускаем ВСЕ заголовки — они проверяются в validate_structure
        if _is_heading_paragraph(para, chapter_pat, para_pat):
            continue
        if not para.text.strip():
            continue
        ts = para.text.strip()
        if ts.startswith("Таблица") or ts.startswith("Рис.") or ts.startswith("Рисунок"):
            continue

        # FIX #1 (Ф-5): пропускаем элементы списков — у них отступ задаётся через w:left, а не w:firstLine
        is_list_item = _is_list_paragraph(para)

        pPr = para._p.pPr

        # ── Ф-2: межстрочный интервал ──
        spacing_el = pPr.find(qn('w:spacing')) if pPr is not None else None
        if spacing_el is not None:
            line_val  = spacing_el.get(qn('w:line'))
            line_rule = spacing_el.get(qn('w:lineRule'))
            if line_val is not None:
                try:
                    actual = int(line_val)
                    if not _is_line_spacing_15(actual, line_rule, tolerance_dxa):
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
                            rule="Межстрочный интервал — 1.5",
                            rule_citation="§4.2, с. 47",
                            found_value=f"{actual} twips (rule={line_rule or 'auto'})",
                            expected_value="360 (auto) или 420 (exact)",
                            recommendation="Установите межстрочный интервал 1.5 (Абзац → Интервал)",
                        ))
                except ValueError:
                    pass

        # ── Ф-3: выравнивание по ширине ──
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
                    rule="Основной текст выровнен по ширине",
                    rule_citation="§4.2, с. 47",
                    found_value=alignment or "не задано",
                    expected_value="both",
                    recommendation="Установите выравнивание по ширине (Ctrl+J)",
                ))

        # ── Ф-5: отступ первой строки ──
        # FIX #1 (Ф-5): пропускаем элементы списков — у них отступ задаётся через w:left, а не w:firstLine
        if not is_list_item:
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
                                rule="Отступ первой строки — 1.25 см (720 DXA)",
                                rule_citation="§4.2, с. 47",
                                found_value=str(actual_fl),
                                expected_value=str(expected_first_line),
                                recommendation="Установите отступ первой строки 1.25 см",
                            ))
                    except ValueError:
                        pass

        # ── Ф-6: интервалы до/после ──
        # FIX #2 (Ф-6): заголовки и элементы списков должны иметь отбивку, проверяем только основной текст
        if not is_list_item and spacing_el is not None:
            for attr, label in [
                (qn('w:before'), "перед абзацем"),
                (qn('w:after'),  "после абзаца"),
            ]:
                val = spacing_el.get(attr)
                if val is not None:
                    try:
                        sp = int(val)
                        if sp != expected_ba:
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
                                rule="Интервалы до/после абзаца — 0",
                                rule_citation="§4.2, с. 47",
                                found_value=str(sp),
                                expected_value="0",
                                recommendation=f"Установите интервал {label} = 0",
                            ))
                    except ValueError:
                        pass

    return errors


def check_margins(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет поля документа (Ф-4)."""
    errors: list[ReportError] = []

    section       = doc.sections[0]
    EMU_PER_CM    = 360000  # 1 см = 360000 EMU
    tolerance_dxa = rules["tolerances"]["dxa"]
    EMU_PER_DXA   = EMU_PER_CM / 567  # ~635 EMU в 1 DXA

    for margin_name, margin_emu in {
        "left":   section.left_margin,
        "right":  section.right_margin,
        "top":    section.top_margin,
        "bottom": section.bottom_margin,
    }.items():
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
                rule=f"Поле {margin_name} = {rules['margins_cm'][margin_name]} см",
                rule_citation="§4.2, с. 47",
                found_value=str(actual_dxa),
                expected_value=str(expected_dxa),
                recommendation=f"Установите поле {margin_name} = {rules['margins_cm'][margin_name]} см",
            ))

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# FIX #3: w:br[@w:type='page'] находится ВНУТРИ <w:r>, не в <w:pPr>
# ─────────────────────────────────────────────────────────────────────────────

def _has_page_break_before(para, para_idx: int, all_paragraphs) -> bool:
    """True если перед абзацем есть разрыв страницы."""
    # 1. w:pageBreakBefore в pPr абзаца
    pPr = para._p.find(qn('w:pPr'))
    if pPr is not None:
        pb = pPr.find(qn('w:pageBreakBefore'))
        if pb is not None:
            val = pb.get(qn('w:val'))
            if val is None or val in ('1', 'true', 'on'):
                return True

    if para_idx == 0:
        return False

    prev_p = all_paragraphs[para_idx - 1]._p

    # 2. w:br type="page" внутри runs предыдущего абзаца
    for br in prev_p.iter(qn('w:br')):
        if br.get(qn('w:type')) == 'page':
            return True

    # 3. w:lastRenderedPageBreak
    for _ in prev_p.iter(qn('w:lastRenderedPageBreak')):
        return True

    return False


def validate_structure(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет структуру документа (С-1..С-10)."""
    errors: list[ReportError] = []
    all_paragraphs = doc.paragraphs

    def _effective_alignment(para) -> str | None:
        """Получает эффективное выравнивание абзаца с учётом наследования от стиля."""
        pPr   = para._p.find(qn('w:pPr'))
        jc_el = pPr.find(qn('w:jc')) if pPr is not None else None
        # FIX #3 (С-8): если есть явное w:jc, используем его
        if jc_el is not None:
            return jc_el.get(qn('w:val'))
        # FIX #3 (С-8): если нет явного выравнивания, берём из стиля
        if para.style and para.style.paragraph_format:
            from docx.enum.text import WD_ALIGN_PARAGRAPH as WDA
            mapping = {WDA.CENTER: "center", WDA.LEFT: "left",
                       WDA.JUSTIFY: "both", WDA.RIGHT: "right"}
            a = mapping.get(para.style.paragraph_format.alignment)
            if a:
                return a
        # FIX #3 (С-8): для заголовков по умолчанию возвращаем center
        if para.style and "Heading" in para.style.name:
            return "center"
        return None

    chapter_pat = rules.get("chapter_heading_pattern",   CHAPTER_HEADING_PATTERN)
    para_pat    = rules.get("paragraph_heading_pattern", PARAGRAPH_HEADING_PATTERN)

    titles_lower = [
        p.text.strip().lower()
        for p in doc.paragraphs
        if p.style and p.style.name in ("Heading 1", "Heading 2")
    ]

    # ── С-1 ──
    for section_name in rules["required_sections"]:
        if not any(section_name.lower() in t for t in titles_lower):
            errors.append(ReportError(
                id=f"С-1-{section_name}", code="С-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Структура документа"),
                fragment=section_name,
                rule=f"Документ должен содержать раздел «{section_name}»",
                rule_citation="§3.2, с. 42",
                found_value="раздел отсутствует", expected_value=section_name,
                recommendation=f"Добавьте раздел «{section_name}»",
            ))

    has_appendix     = False
    appendix_ref_pat = re.compile(r'\(прил\.\s*\d+\)', re.IGNORECASE)

    for para_idx, para in enumerate(doc.paragraphs):
        # Проверяем заголовки по стилю или по паттерну
        is_heading_by_style = para.style and "Heading" in para.style.name
        is_heading_by_pattern = _is_heading_paragraph(para, chapter_pat, para_pat)
        
        if not is_heading_by_style and not is_heading_by_pattern:
            continue

        title       = para.text.strip()
        title_lower = title.lower()

        if "приложен" in title_lower:
            has_appendix = True

        is_service = any(s in title_lower for s in SERVICE_TITLES)

        # ── С-3: H1 с новой страницы (только для глав, не для служебных разделов) ──
        # Глава = стиль Heading 1 ИЛИ паттерн главы (но не Heading 2/3)
        is_chapter = (
            para.style.name == "Heading 1" or 
            (is_heading_by_pattern and para.style.name not in ("Heading 2", "Heading 3"))
        )
        if is_chapter and not is_service:
            if not _has_page_break_before(para, para_idx, all_paragraphs):
                errors.append(ReportError(
                    id=f"С-3-{para_idx}", code="С-3", type="formatting", severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Заголовок «{title[:50]}»",
                    ),
                    fragment=title[:100],
                    rule="Раздел начинается с новой страницы",
                    rule_citation="§4.2, с. 47",
                    found_value="нет разрыва страницы",
                    expected_value="разрыв страницы",
                    recommendation="Добавьте Ctrl+Enter перед заголовком",
                ))

        # ── С-4: H2/H3 НЕ с новой страницы ──
        if para.style.name in ("Heading 2", "Heading 3"):
            # Проверяем pageBreakBefore в pPr
            pPr  = para._p.find(qn('w:pPr'))
            pb_e = pPr.find(qn('w:pageBreakBefore')) if pPr is not None else None
            has_pbb = False
            if pb_e is not None:
                val = pb_e.get(qn('w:val'))
                if val is None or val in ('1', 'true', 'on'):
                    has_pbb = True
            
            # Проверяем w:br type="page" в предыдущем абзаце
            has_br_page = False
            if para_idx > 0:
                prev_p = all_paragraphs[para_idx - 1]._p
                for br in prev_p.iter(qn('w:br')):
                    if br.get(qn('w:type')) == 'page':
                        has_br_page = True
                        break
            
            # Проверяем w:lastRenderedPageBreak в предыдущем абзаце
            has_lpb = False
            if para_idx > 0:
                prev_p = all_paragraphs[para_idx - 1]._p
                for _ in prev_p.iter(qn('w:lastRenderedPageBreak')):
                    has_lpb = True
                    break
            
            if has_pbb or has_br_page or has_lpb:
                errors.append(ReportError(
                    id=f"С-4-{para_idx}", code="С-4", type="formatting", severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Параграф «{title[:50]}»",
                    ),
                    fragment=title[:100],
                    rule="Параграфы не начинаются с новой страницы",
                    rule_citation="§4.2, с. 47",
                    found_value="есть разрыв страницы",
                    expected_value="нет",
                    recommendation="Уберите «С новой страницы» у параграфа",
                ))

        # ── С-5: формат заголовка главы (только не-служебные H1) ──
        if para.style.name == "Heading 1" and not is_service:
            if not re.match(chapter_pat, title):
                errors.append(ReportError(
                    id=f"С-5-{para_idx}", code="С-5", type="formatting", severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Заголовок {para_idx + 1}",
                    ),
                    fragment=title[:100],
                    rule="Заголовок главы: «Глава N. Название»",
                    rule_citation="§3.3, с. 43",
                    found_value=title[:100], expected_value="Глава N. Название",
                    recommendation="Исправьте формат заголовка главы",
                ))

        # ── С-6: нумерация параграфов (только не-служебные H2/H3) ──
        # FIX #2: паттерн теперь принимает «2.1.» с точкой
        if para.style.name in ("Heading 2", "Heading 3") and not is_service:
            if not re.match(para_pat, title):
                errors.append(ReportError(
                    id=f"С-6-{para_idx}", code="С-6", type="formatting", severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Параграф {para_idx + 1}",
                    ),
                    fragment=title[:100],
                    rule="Параграфы нумеруются: «1.1.» или «1.1.1.»",
                    rule_citation="§4.2, с. 47",
                    found_value=title[:100],
                    expected_value="N.N. Название",
                    recommendation="Исправьте нумерацию параграфа",
                ))

        # ── С-7: без bold/italic/underline ──
        if any(r.font.bold or r.font.italic or r.font.underline for r in para.runs):
            errors.append(ReportError(
                id=f"С-7-{para_idx}", code="С-7", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}",
                ),
                fragment=title[:100],
                rule="Заголовки без bold/italic/underline",
                rule_citation="§3.3, с. 43",
                found_value="bold/italic/underline", expected_value="обычный текст",
                recommendation="Уберите форматирование из заголовка",
            ))

        # ── С-8: заголовки по центру ──
        # FIX #1: заголовки параграфов (2.1., 2.7. и т.д.) — тоже по центру,
        # а не по ширине. Ф-3 их пропускает, С-8 проверяет именно заголовки.
        if _effective_alignment(para) != "center":
            errors.append(ReportError(
                id=f"С-8-{para_idx}", code="С-8", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}",
                ),
                fragment=title[:100],
                rule="Заголовки по центру (без абзацного отступа)",
                rule_citation="§3.3, с. 43",
                found_value=_effective_alignment(para) or "не задано",
                expected_value="center",
                recommendation="Установите выравнивание по центру",
            ))

        # ── С-9: нет точки в конце заголовка ──
        if title.endswith('.'):
            errors.append(ReportError(
                id=f"С-9-{para_idx}", code="С-9", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}",
                ),
                fragment=title[:100],
                rule="В конце заголовка нет точки",
                rule_citation="§3.3, с. 43",
                found_value=title[-10:] if len(title) > 10 else title,
                expected_value="без точки",
                recommendation="Удалите точку в конце заголовка",
            ))

    # ── С-10: подзаголовки без нумерации ──
    in_chapter = False
    chapter_start_idx = None
    for para_idx, para in enumerate(doc.paragraphs):
        if not para.style:
            continue
        sn    = para.style.name
        title = para.text.strip()
        if sn == "Heading 1":
            in_chapter        = True
            chapter_start_idx = para_idx
            continue
        if in_chapter and sn == "Heading 2" and not re.match(r'^\d+\.\d+', title):
            errors.append(ReportError(
                id=f"С-10-{para_idx}", code="С-10", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Подзаголовок в главе {chapter_start_idx}",
                ),
                fragment=title[:100],
                rule="Внутри параграфов нет ненумерованных подзаголовков",
                rule_citation="§4.2, с. 47",
                found_value=title[:100], expected_value="N.N или текст",
                recommendation="Добавьте нумерацию или оформите как текст",
            ))
        if in_chapter and sn in ("Heading 3", "Heading 4", "Heading 5", "Heading 6") and title:
            errors.append(ReportError(
                id=f"С-10-sub-{para_idx}", code="С-10", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Подзаголовок в главе {chapter_start_idx}",
                ),
                fragment=title[:100],
                rule="Внутри параграфов нет подзаголовков",
                rule_citation="§4.2, с. 47",
                found_value=title[:100], expected_value="обычный текст",
                recommendation="Удалите подзаголовок или оформите как текст",
            ))

    # ── С-2 ──
    if has_appendix:
        full_text = "\n".join(p.text for p in doc.paragraphs)
        if not appendix_ref_pat.search(full_text):
            errors.append(ReportError(
                id="С-2-appx-ref", code="С-2", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Приложения"),
                fragment="Приложение",
                rule="Приложения должны иметь ссылки в тексте «(прил. N)»",
                rule_citation="§3.8, с. 44",
                found_value="ссылки отсутствуют", expected_value="(прил. N)",
                recommendation="Добавьте ссылки на приложения",
            ))

    return errors


def get_effective_font_size(run, doc) -> float | None:
    """Возвращает размер шрифта run в пт."""
    if run.font.size is not None:
        return run.font.size.pt
    rPr = run._element.find(qn('w:rPr'))
    if rPr is not None:
        for tag in (qn('w:sz'), qn('w:szCs')):
            el = rPr.find(tag)
            if el is not None:
                v = el.get(qn('w:val'))
                if v:
                    try:
                        return int(v) / 2.0
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
    """Проверяет форматирование таблиц и рисунков (Т-1, Т-4, Т-6, Т-12)."""
    errors: list[ReportError] = []

    body          = doc.element.body
    elements_flow = []
    para_index    = 0

    for child in body:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            elements_flow.append(('paragraph', para_index, child))
            para_index += 1
        elif tag == 'tbl':
            tbl_idx = sum(1 for e in elements_flow if e[0] == 'table')
            elements_flow.append(('table', tbl_idx, child))

    # ── Т-1: подпись «Таблица N» над таблицей ──
    # FIX #8: ищем назад через пустые параграфы, до 5 непустых шагов
    # FIX #7: используем search вместо match для поиска подписи в тексте параграфа
    table_caption_pattern = re.compile(r'^Таблица\s*\d+', re.IGNORECASE)

    for i, (etype, eidx, element) in enumerate(elements_flow):
        if etype != 'table':
            continue

        caption_found = False
        nonempty_steps = 0

        for j in range(i - 1, -1, -1):
            ptype, pidx, pelement = elements_flow[j]
            if ptype != 'paragraph':
                break

            para_text = ''.join(
                t.text for t in pelement.iter(
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
                ) if t.text
            ).strip()

            if not para_text:
                continue   # пустые параграфы пропускаем

            nonempty_steps += 1
            if nonempty_steps > 5:
                break      # слишком далеко

            # Проверяем, начинается ли текст с "Таблица N"
            if table_caption_pattern.search(para_text):
                caption_found = True
                pPr   = pelement.find(qn('w:pPr'))
                jc_el = pPr.find(qn('w:jc')) if pPr is not None else None
                align = jc_el.get(qn('w:val')) if jc_el is not None else None
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
                        rule="Подпись «Таблица N» — по правому краю",
                        rule_citation="§4.5, с. 51",
                        found_value=align or "не задано", expected_value="right",
                        recommendation="Выровняйте подпись по правому краю",
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
                        rule="В конце подписи таблицы нет точки",
                        rule_citation="§4.5, с. 51",
                        found_value=para_text[-10:], expected_value="без точки",
                        recommendation="Удалите точку",
                    ))
                break
            else:
                # Нашли непустой параграф — но это не подпись, дальше не ищем
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
                found_value="подпись отсутствует",
                expected_value="Таблица N (над таблицей)",
                recommendation="Добавьте подпись «Таблица N» над таблицей",
            ))

    # ── Т-4: шрифт в таблицах ──
    tables_list = list(doc.tables)
    for table_idx, table in enumerate(tables_list):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para in cell.paragraphs:
                    for run in para.runs:
                        fn = run.font.name
                        if fn and fn != "Times New Roman":
                            errors.append(ReportError(
                                id=f"Т-4-fn-{table_idx}-{row_idx}-{cell_idx}",
                                code="Т-4",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=0,
                                    structural_path=f"Таблица {table_idx+1}, [{row_idx+1},{cell_idx+1}]",
                                ),
                                fragment=para.text[:50],
                                rule="Шрифт в таблице — Times New Roman",
                                rule_citation="§4.5, с. 51",
                                found_value=fn, expected_value="Times New Roman",
                                recommendation="Установите Times New Roman",
                            ))
                        fs = get_effective_font_size(run, doc)
                        if fs is not None and (fs < 11 or fs > 12):
                            errors.append(ReportError(
                                id=f"Т-4-fs-{table_idx}-{row_idx}-{cell_idx}",
                                code="Т-4",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=0,
                                    structural_path=f"Таблица {table_idx+1}, [{row_idx+1},{cell_idx+1}]",
                                ),
                                fragment=para.text[:50],
                                rule="Размер шрифта в таблице — 11-12 пт",
                                rule_citation="§4.5, с. 51",
                                found_value=str(fs), expected_value="11-12",
                                recommendation="Установите 11-12 пт",
                            ))

    # ── Т-6: сквозная нумерация ──
    table_numbers  = []
    figure_numbers = []
    fig_cap_pat    = re.compile(r'^Рис\.?\s*(\d+)', re.IGNORECASE)

    for i, (etype, eidx, element) in enumerate(elements_flow):
        if etype != 'table':
            continue
        for j in range(i - 1, -1, -1):
            ptype, _, pelement = elements_flow[j]
            if ptype != 'paragraph':
                break
            pt = ''.join(
                t.text for t in pelement.iter(
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
                ) if t.text
            ).strip()
            if not pt:
                continue
            m = re.match(r'^Таблица\s*(\d+)', pt, re.IGNORECASE)
            if m:
                table_numbers.append(int(m.group(1)))
            break

    for para in doc.paragraphs:
        m = fig_cap_pat.match(para.text.strip())
        if m:
            figure_numbers.append(int(m.group(1)))

    for nums, label in [(table_numbers, "Таблица"), (figure_numbers, "Рис.")]:
        for i, (actual, expected) in enumerate(zip(nums, range(1, len(nums) + 1))):
            if actual != expected:
                errors.append(ReportError(
                    id=f"Т-6-{label}-{i}", code="Т-6", type="formatting", severity="error",
                    location=ErrorLocation(paragraph_index=0, structural_path=f"{label} {i+1}"),
                    fragment=f"{label} {actual}",
                    rule=f"Нумерация {label} — сквозная",
                    rule_citation="§4.4, с. 50-52",
                    found_value=str(actual), expected_value=str(expected),
                    recommendation=f"Исправьте номер на {expected}",
                ))
                break

    # ── Т-12: запятая вместо точки ──
    decimal_pat = re.compile(r'\b\d+\.\d+\b')
    for table_idx, table in enumerate(tables_list):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para in cell.paragraphs:
                    for match in decimal_pat.findall(para.text):
                        errors.append(ReportError(
                            id=f"Т-12-{table_idx}-{row_idx}-{cell_idx}",
                            code="Т-12",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=0,
                                structural_path=f"Таблица {table_idx+1}, [{row_idx+1},{cell_idx+1}]",
                            ),
                            fragment=para.text[:100],
                            rule="Дробные числа — с запятой",
                            rule_citation="§4.5, с. 51",
                            found_value=match, expected_value=match.replace('.', ','),
                            recommendation="Замените точку на запятую",
                        ))

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# FIX #5: автонумерованный список (w:numPr)
# ─────────────────────────────────────────────────────────────────────────────

def _build_list_counters(doc: Document) -> dict[int, int]:
    """Для каждого абзаца с w:numPr возвращает его порядковый номер (1-based)."""
    counters: dict[tuple, int] = {}
    para_numbers: dict[int, int] = {}

    for idx, para in enumerate(doc.paragraphs):
        pPr = para._p.find(qn('w:pPr'))
        if pPr is None:
            continue
        numPr = pPr.find(qn('w:numPr'))
        if numPr is None:
            continue
        numId_el = numPr.find(qn('w:numId'))
        ilvl_el  = numPr.find(qn('w:ilvl'))
        if numId_el is None:
            continue
        num_id = int(numId_el.get(qn('w:val'), 0))
        ilvl   = int(ilvl_el.get(qn('w:val'), 0)) if ilvl_el is not None else 0

        for (nid, lvl) in list(counters.keys()):
            if nid == num_id and lvl > ilvl:
                del counters[(nid, lvl)]

        counters[(num_id, ilvl)] = counters.get((num_id, ilvl), 0) + 1
        para_numbers[idx] = counters[(num_id, ilvl)]

    return para_numbers


def validate_references_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет список литературы (Л-1, Л-3..Л-12)."""
    errors: list[ReportError] = []

    # Находим раздел
    ref_section_start_idx = 0
    in_refs = False
    ref_paras: list[tuple[int, Any]] = []

    for para_idx, para in enumerate(doc.paragraphs):
        tl = para.text.lower()
        if "список литературы" in tl or "библиографический список" in tl:
            in_refs = True
            ref_section_start_idx = para_idx + 1
            continue
        if in_refs:
            if para.style and "Heading" in para.style.name:
                break
            if para.text.strip():
                ref_paras.append((para_idx, para))

    ref_section_paragraphs = [p.text.strip() for _, p in ref_paras]

    # ── Л-7 ──
    min_sources = rules.get("references", {}).get("min_sources", 40)
    if len(ref_section_paragraphs) < min_sources:
        errors.append(ReportError(
            id="Л-7-count", code="Л-7", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Список литературы"),
            fragment="Список литературы",
            rule=f"Не менее {min_sources} источников",
            rule_citation="§3.7, с. 44",
            found_value=str(len(ref_section_paragraphs)), expected_value=str(min_sources),
            recommendation="Добавьте источники",
        ))

    # ── FIX #5: определяем тип нумерации ──
    list_counters = _build_list_counters(doc)
    auto_paras    = [(gi, p, p.text.strip()) for gi, p in ref_paras if gi in list_counters]
    numbering_pat = re.compile(r'^(\d+)[\.\)]\s')
    manual_paras  = [(gi, p, p.text.strip()) for gi, p in ref_paras
                     if numbering_pat.match(p.text.strip())]

    uses_auto      = len(auto_paras) > len(manual_paras)
    source_numbers: list[int] = []

    if uses_auto:
        for seq, (gi, _, _) in enumerate(auto_paras, start=1):
            source_numbers.append(seq)
            expected_num = list_counters.get(gi, seq)
            if expected_num != seq:
                errors.append(ReportError(
                    id=f"Л-5-auto-{gi}", code="Л-5", type="formatting", severity="error",
                    location=ErrorLocation(paragraph_index=gi, structural_path="Список литературы"),
                    fragment=auto_paras[seq - 1][2][:100],
                    rule="Нумерация источников — сквозная",
                    rule_citation="§4.5, с. 52",
                    found_value=str(expected_num), expected_value=str(seq),
                    recommendation="Исправьте нумерацию",
                ))
                break
    else:
        for text in ref_section_paragraphs:
            m = numbering_pat.match(text)
            if m:
                source_numbers.append(int(m.group(1)))

        if not source_numbers and ref_section_paragraphs:
            errors.append(ReportError(
                id="Л-5-no-numbering", code="Л-5", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=ref_section_start_idx,
                                       structural_path="Список литературы"),
                fragment=ref_section_paragraphs[0][:100],
                rule="Источники нумеруются сплошной нумерацией",
                rule_citation="§4.5, с. 52",
                found_value="нет нумерации", expected_value="1, 2, 3, ...",
                recommendation="Добавьте нумерацию",
            ))
        else:
            for i, (actual, expected) in enumerate(
                zip(source_numbers, range(1, len(source_numbers) + 1))
            ):
                if actual != expected:
                    errors.append(ReportError(
                        id=f"Л-5-num-{i}", code="Л-5", type="formatting", severity="error",
                        location=ErrorLocation(
                            paragraph_index=ref_section_start_idx + i,
                            structural_path="Список литературы",
                        ),
                        fragment=ref_section_paragraphs[i][:100],
                        rule="Нумерация сплошная",
                        rule_citation="§4.5, с. 52",
                        found_value=str(actual), expected_value=str(expected),
                        recommendation=f"Исправьте на {expected}",
                    ))
                    break

    # ── Л-4: алфавитный порядок ──
    # FIX #3: нормализуем ё→е для корректной сортировки
    def _norm_ru(s: str) -> str:
        return s.replace('ё', 'е').replace('Ё', 'Е')

    def extract_surname(text: str) -> tuple[str, str]:
        clean  = re.sub(r'^(\d+[\.\)]\s*)?', '', text.strip())
        part   = re.split(r'[,.]', clean)[0].strip()
        is_cyr = bool(re.search(r'[А-ЯЁа-яё]', part))
        return (_norm_ru(part.lower()), 'cyrillic' if is_cyr else 'latin')

    def sort_key(item):
        _, text = item
        surname, lang = extract_surname(text)
        return (0 if lang == 'cyrillic' else 1, surname)

    if len(ref_section_paragraphs) > 1:
        indexed = list(enumerate(ref_section_paragraphs))
        sorted_ = sorted(indexed, key=sort_key)
        for i, (oi, _) in enumerate(indexed):
            si, _ = sorted_[i]
            if oi != si:
                cs, _ = extract_surname(ref_section_paragraphs[oi])
                ns, _ = extract_surname(ref_section_paragraphs[si])
                errors.append(ReportError(
                    id=f"Л-4-order-{i}", code="Л-4", type="formatting", severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_section_start_idx + oi,
                        structural_path="Список литературы",
                    ),
                    fragment=ref_section_paragraphs[oi][:100],
                    rule="Алфавитный порядок: русские, затем иностранные",
                    rule_citation="§4.5, с. 52",
                    found_value=f"«{cs}» после «{ns}»", expected_value=f"«{ns}» перед «{cs}»",
                    recommendation="Расположите по алфавиту",
                ))
                break

    # ── Л-8: актуальность ──
    current_year   = datetime.now().year
    max_years_old  = rules.get("references", {}).get("max_years_old", 10)
    year_threshold = current_year - max_years_old
    year_pat       = re.compile(r'\b(19|20)\d{2}\b')
    recent = total_yp = 0
    for text in ref_section_paragraphs:
        m = year_pat.search(text)
        if m:
            total_yp += 1
            if int(m.group(0)) >= year_threshold:
                recent += 1
    if total_yp > 0 and (recent / total_yp) < 0.70:
        errors.append(ReportError(
            id="Л-8-recency", code="Л-8", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Список литературы"),
            fragment="Список литературы",
            rule=f"≥70 % источников — за последние {max_years_old} лет",
            rule_citation="§4.5, с. 52",
            found_value=f"{recent / total_yp * 100:.1f}%", expected_value="≥70%",
            recommendation="Добавьте свежие источники",
        ))

    # ── Л-9: формат автора ──
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
                id=f"Л-9-{idx}", code="Л-9", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы",
                ),
                fragment=text[:100],
                rule="Автор: Фамилия, И. О.",
                rule_citation="§4.5, с. 52",
                found_value=text[:50], expected_value="Фамилия, И. О.",
                recommendation="Исправьте формат автора",
            ))

    # ── Л-10: URL с датой обращения ──
    url_pat    = re.compile(r'https?://\S+')
    access_pat = re.compile(r'\(дата обращения:\s*\d{2}\.\d{2}\.\d{4}\)')
    for idx, text in enumerate(ref_section_paragraphs):
        if url_pat.search(text) and not access_pat.search(text):
            errors.append(ReportError(
                id=f"Л-10-{idx}", code="Л-10", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы",
                ),
                fragment=text[:100],
                rule="Для URL — дата обращения: (дата обращения: ДД.ММ.ГГГГ)",
                rule_citation="§4.5, с. 52",
                found_value="URL без даты", expected_value="(дата обращения: ДД.ММ.ГГГГ)",
                recommendation="Добавьте дату обращения",
            ))

    # ── Л-11: ссылки соответствуют списку ──
    valid_nums: set[int] = set(source_numbers)
    ref_inline = re.compile(r'\[(\d+)(?:\s*,\s*с\.\s*\d+)?\]')
    for para_idx, para in enumerate(doc.paragraphs):
        for m in ref_inline.finditer(para.text):
            n = int(m.group(1))
            if valid_nums and n not in valid_nums:
                errors.append(ReportError(
                    id=f"Л-11-{para_idx}-{n}", code="Л-11", type="formatting", severity="error",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                    fragment=m.group(0),
                    rule="Ссылка соответствует источнику в списке",
                    rule_citation="§4.3, с. 49",
                    found_value=f"№{n}", expected_value=f"1–{len(valid_nums)}",
                    recommendation=f"Добавьте источник №{n} или исправьте ссылку",
                ))

    # ── Л-12: длинные тире ──
    hyphen_dash = re.compile(r'\s-\s|\d-\d')
    for idx, text in enumerate(ref_section_paragraphs):
        if hyphen_dash.search(text):
            errors.append(ReportError(
                id=f"Л-12-{idx}", code="Л-12", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы",
                ),
                fragment=text[:100],
                rule="В библиографии — длинное тире «–», не дефис",
                rule_citation="§4.5, с. 52",
                found_value="-", expected_value="–",
                recommendation="Замените дефис на тире",
            ))

    # ── Л-1: квадратные скобки ──
    round_bkt = re.compile(r'\(\d+\)')
    for para_idx, para in enumerate(doc.paragraphs):
        ms = round_bkt.findall(para.text)
        if ms:
            errors.append(ReportError(
                id=f"Л-1-{para_idx}", code="Л-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                fragment=para.text[:100],
                rule="Ссылки в квадратных скобках [N]",
                rule_citation="§4.3, с. 49",
                found_value=ms[0], expected_value="[N]",
                recommendation="Замените круглые скобки на квадратные",
            ))

    # ── Л-3: порядок множественных ссылок ──
    multi_pat = re.compile(r'\[(\d+(?:;\s*\d+)+)\]')
    for para_idx, para in enumerate(doc.paragraphs):
        for m in multi_pat.finditer(para.text):
            nums = [int(n.strip()) for n in m.group(1).split(';')]
            if nums != sorted(nums):
                errors.append(ReportError(
                    id=f"Л-3-{para_idx}", code="Л-3", type="formatting", severity="error",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                    fragment=m.group(0),
                    rule="Несколько источников — по возрастанию через «;»",
                    rule_citation="§4.3, с. 49",
                    found_value=m.group(0),
                    expected_value=f"[{'; '.join(str(n) for n in sorted(nums))}]",
                    recommendation="Расположите по возрастанию",
                ))

    return errors


def validate_volume(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет объём работы (Ф-11..Ф-13)."""
    errors: list[ReportError] = []

    vr            = rules.get("volume", {})
    total_min     = vr.get("total_chars_min",            90000)
    total_max     = vr.get("total_chars_max",           108000)
    theory_min    = vr.get("theory_chapter_chars_min",   27000)
    theory_max    = vr.get("theory_chapter_chars_max",   36000)
    empirical_min = vr.get("empirical_chapter_chars_min",45000)
    empirical_max = vr.get("empirical_chapter_chars_max",54000)

    current_section = None
    section_texts: dict[str, list[str]] = {}
    all_text: list[str] = []

    for para in doc.paragraphs:
        if para.style and para.style.name in ("Heading 1", "Heading 2"):
            tl = para.text.strip().lower()
            if tl.startswith("глава 1"):
                current_section = "Глава 1"
            elif tl.startswith("глава 2"):
                current_section = "Глава 2"
            elif tl in SERVICE_TITLES:
                current_section = tl
            else:
                current_section = para.text.strip()
        elif para.text.strip():
            all_text.append(para.text)
            if current_section:
                section_texts.setdefault(current_section, []).append(para.text)

    total_chars = len("".join(all_text))
    if total_chars < total_min:
        errors.append(ReportError(
            id="Ф-11-below-min", code="Ф-11", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Документ"),
            fragment=f"Объём: {total_chars} знаков",
            rule=f"Объём ВКР: {total_min}–{total_max} знаков",
            rule_citation="§4.1, с. 46",
            found_value=str(total_chars), expected_value=f"{total_min}-{total_max}",
            recommendation=f"Добавьте текст. Не хватает {total_min - total_chars} знаков.",
        ))
    elif total_chars > total_max:
        errors.append(ReportError(
            id="Ф-11-above-max", code="Ф-11", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=0, structural_path="Документ"),
            fragment=f"Объём: {total_chars} знаков",
            rule=f"Объём ВКР: {total_min}–{total_max} знаков",
            rule_citation="§4.1, с. 46",
            found_value=str(total_chars), expected_value=f"{total_min}-{total_max}",
            recommendation=f"Сократите. Превышение на {total_chars - total_max} знаков.",
        ))

    for chapter_key, code, cmin, cmax, label in [
        ("Глава 1", "Ф-12", theory_min,    theory_max,    "Теоретическая глава"),
        ("Глава 2", "Ф-13", empirical_min, empirical_max, "Эмпирическая глава"),
    ]:
        ch_chars = len("".join(section_texts.get(chapter_key, [])))
        if ch_chars == 0:
            continue
        if ch_chars < cmin:
            errors.append(ReportError(
                id=f"{code}-below-min", code=code, type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path=chapter_key),
                fragment=f"{chapter_key}: {ch_chars} знаков",
                rule=f"{label}: {cmin}–{cmax} знаков",
                rule_citation="§3.4, с. 23",
                found_value=str(ch_chars), expected_value=f"{cmin}-{cmax}",
                recommendation=f"Расширьте {chapter_key}. Не хватает {cmin - ch_chars} знаков.",
            ))
        elif ch_chars > cmax:
            errors.append(ReportError(
                id=f"{code}-above-max", code=code, type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path=chapter_key),
                fragment=f"{chapter_key}: {ch_chars} знаков",
                rule=f"{label}: {cmin}–{cmax} знаков",
                rule_citation="§3.4, с. 23",
                found_value=str(ch_chars), expected_value=f"{cmin}-{cmax}",
                recommendation=f"Сократите. Превышение на {ch_chars - cmax} знаков.",
            ))

    return errors


def validate_typography_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Проверяет типографику (Н-2, Н-4, Н-5, Н-6, Н-7)."""
    errors: list[ReportError] = []

    no_space_pat   = re.compile(r'[А-ЯЁ]\.[А-ЯЁ]\.[А-ЯЁ][а-яё]+')
    wrong_quotes   = re.compile(r'"[^"]*"')
    abbrev_pat     = re.compile(r'\b[А-ЯЁ]{2,}\b')
    explained_pat  = re.compile(r'\([А-ЯЁ]{2,}\)')
    hyphen_nums    = re.compile(r'(\d)\s*-\s*(\d)')
    manual_num_pat = re.compile(r'^\s*\d+\.\s+')
    bullet_markers = ['•', '◦', '▪', '‣', '⁃']

    found_abbrevs: set[str] = set()
    in_list          = False
    list_marker_type = None

    # FIX #5: граница раздела литературы — аббревиатуры там не проверяем
    refs_start_idx: int | None = None
    for para_idx, para in enumerate(doc.paragraphs):
        tl = para.text.lower()
        if "список литературы" in tl or "библиографический список" in tl:
            refs_start_idx = para_idx
            break

    for para_idx, para in enumerate(doc.paragraphs):
        in_bibliography = refs_start_idx is not None and para_idx >= refs_start_idx

        if _is_heading_paragraph(para):
            continue
        if not para.text.strip():
            continue

        text = para.text

        # Н-2: пробелы между инициалами
        # FIX #6 (Н-2): понижаем severity до info, т.к. требование избыточно жёсткое
        m = no_space_pat.search(text)
        if m:
            errors.append(ReportError(
                id=f"Н-2-{para_idx}", code="Н-2", type="style", severity="info",
                location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                fragment=text[:100],
                rule="Между инициалами — пробел: И. И. Иванов",
                rule_citation="§4.2, с. 48",
                found_value=m.group(0), expected_value="И. И. Иванов",
                recommendation="Добавьте пробелы между инициалами",
            ))

        if not in_bibliography:
            # Н-4: угловые кавычки
            if wrong_quotes.search(text):
                errors.append(ReportError(
                    id=f"Н-4-{para_idx}", code="Н-4", type="style", severity="warning",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                    fragment=text[:100],
                    rule="Кавычки — угловые «текст»",
                    rule_citation="§4.2, с. 48",
                    found_value='"..."', expected_value='«...»',
                    recommendation='Замените "..." на «...»',
                ))

            # Н-5: тире между числами
            hm = hyphen_nums.search(text)
            if hm:
                errors.append(ReportError(
                    id=f"Н-5-{para_idx}", code="Н-5", type="style", severity="warning",
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                    fragment=text[:100],
                    rule="Между числами — тире (–), не дефис",
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
                        location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                        fragment=text[:100],
                        rule="Используйте автоматическую нумерацию",
                        rule_citation="§4.2, с. 48",
                        found_value="ручная нумерация", expected_value="автонумерация",
                        recommendation="Используйте автоматическую нумерацию",
                    ))

            # Н-7: смешанные маркеры
            stripped   = text.strip()
            cur_marker = next((mk for mk in bullet_markers if stripped.startswith(mk)), None)
            if cur_marker:
                if not in_list:
                    in_list = True
                    list_marker_type = cur_marker
                elif list_marker_type != cur_marker:
                    errors.append(ReportError(
                        id=f"Н-7-mixed-{para_idx}", code="Н-7", type="style", severity="warning",
                        location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                        fragment=text[:100],
                        rule="В списке — единый маркер",
                        rule_citation="§4.2, с. 48",
                        found_value=f"'{cur_marker}'", expected_value=f"'{list_marker_type}'",
                        recommendation="Используйте одинаковые маркеры",
                    ))
            else:
                in_list = False
                list_marker_type = None

            # FIX #4 (Н-6): аббревиатуры — проверяем с учётом всех найденных расшифровок
            # Сначала собираем расшифровки из текущего абзаца
            for em in explained_pat.finditer(text):
                found_abbrevs.add(em.group(0)[1:-1])
            # Ищем расшифровки в формате «Полное название (АБВ)»
            full_name_pattern = re.compile(r'([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*)\s*\(([А-ЯЁ]{2,})\)')
            for match in full_name_pattern.finditer(text):
                found_abbrevs.add(match.group(2))
            
            for am in abbrev_pat.finditer(text):
                abbrev = am.group(0)
                # FIX #4 (Н-6): проверяем наличие расшифровки во всём документе
                if abbrev not in found_abbrevs:
                    errors.append(ReportError(
                        id=f"Н-6-{para_idx}-{abbrev}", code="Н-6", type="style", severity="warning",
                        location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                        fragment=text[:100],
                        rule="При первом использовании аббревиатуры — расшифровка (АБВ)",
                        rule_citation="§4.1, с. 46",
                        found_value=abbrev, expected_value=f"полное название ({abbrev})",
                        recommendation=f"Расшифруйте {abbrev}",
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

    # FIX #4/#9: заголовок «Содержание» может быть в любом стиле
    toc_start = toc_end = None
    for para_idx, para in enumerate(doc.paragraphs):
        tl = para.text.strip().lower()
        if any(s in tl for s in SKIP) and len(tl) < 25:
            toc_start = para_idx
            continue
        if toc_start is not None and toc_end is None:
            if para.style and para.style.name == "Heading 1" and para_idx != toc_start:
                toc_end = para_idx
                break

    if toc_start is None:
        if headings_to_check:
            errors.append(ReportError(
                id="Со-1-no-toc", code="Со-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=0, structural_path="Структура"),
                fragment="Содержание отсутствует",
                rule="Документ должен содержать «Содержание»",
                rule_citation="§3.2, с. 12",
                found_value="отсутствует", expected_value="раздел Содержание",
                recommendation="Добавьте «Содержание» после титульного листа",
            ))
        return errors

    end = toc_end if toc_end else len(doc.paragraphs)

    # FIX #9: автоматическое оглавление Word — поле TOC в XML
    has_toc_field = False
    for i in range(toc_start, end):
        p_xml = doc.paragraphs[i]._p.xml
        if (' TOC ' in p_xml or 'TOC \\' in p_xml or
                'w:fldChar' in p_xml or 'HYPERLINK' in p_xml):
            has_toc_field = True
            break

    if has_toc_field:
        return errors   # автоматическое оглавление — считаем корректным

    toc_paras = [
        doc.paragraphs[i].text.strip()
        for i in range(toc_start + 1, end)
        if doc.paragraphs[i].text.strip()
    ]

    if not toc_paras:
        errors.append(ReportError(
            id="Со-1-empty-toc", code="Со-1", type="formatting", severity="error",
            location=ErrorLocation(paragraph_index=toc_start, structural_path="Содержание"),
            fragment="Содержание пустое",
            rule="Содержание должно отражать все заголовки",
            rule_citation="§3.2, с. 12",
            found_value="пустое", expected_value="перечень заголовков",
            recommendation="Заполните содержание или используйте автоматическое (F9)",
        ))
        return errors

    # FIX #9: мягкое совпадение — убираем цифры/точки из сравнения
    def _norm(s: str) -> str:
        return re.sub(r'[\s\d\.…]+', ' ', s.lower()).strip()

    def heading_in_toc(title: str, lines: list[str]) -> bool:
        tn = _norm(title)
        for line in lines:
            if tn in _norm(line):
                return True
        words = [w for w in tn.split() if len(w) > 3]
        if not words:
            return True
        for line in lines:
            ln = _norm(line)
            if sum(1 for w in words if w in ln) / len(words) >= 0.6:
                return True
        return False

    for hidx, title in headings_to_check:
        if not heading_in_toc(title, toc_paras):
            errors.append(ReportError(
                id=f"Со-1-{hidx}", code="Со-1", type="formatting", severity="error",
                location=ErrorLocation(
                    paragraph_index=hidx,
                    structural_path=f"Заголовок «{title[:50]}»",
                ),
                fragment=title[:100],
                rule="Все заголовки должны быть в содержании",
                rule_citation="§3.2, с. 12",
                found_value=f"«{title}» не найден",
                expected_value="присутствует в содержании",
                recommendation="Обновите оглавление (F9) или добавьте вручную",
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

        if not _has_page_break_before(para, i, all_paragraphs):
            errors.append(ReportError(
                id=f"П-1-{i}", code="П-1", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=i, structural_path=f"Приложение {letter}"),
                fragment=para.text.strip()[:100],
                rule="Приложение начинается с новой страницы",
                rule_citation="§4.6, с. 59",
                found_value="нет разрыва", expected_value="разрыв страницы",
                recommendation="Ctrl+Enter перед «Приложение»",
            ))
        if _align(para) != "right":
            errors.append(ReportError(
                id=f"П-2-{i}", code="П-2", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=i, structural_path=f"Приложение {letter}"),
                fragment=para.text.strip()[:100],
                rule="«Приложение N» — по правому краю",
                rule_citation="§4.6, с. 59",
                found_value=_align(para) or "не задано", expected_value="right",
                recommendation="Выровняйте по правому краю",
            ))

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
                        location=ErrorLocation(paragraph_index=j, structural_path=f"Название прил. {letter}"),
                        fragment=nt[:100],
                        rule="Название приложения — по центру",
                        rule_citation="§4.6, с. 59",
                        found_value=_align(np_) or "не задано", expected_value="center",
                        recommendation="Выровняйте по центру",
                    ))
                if nt.endswith('.'):
                    errors.append(ReportError(
                        id=f"П-3-dot-{j}", code="П-3", type="formatting", severity="error",
                        location=ErrorLocation(paragraph_index=j, structural_path=f"Название прил. {letter}"),
                        fragment=nt[:100],
                        rule="Название приложения без точки в конце",
                        rule_citation="§4.6, с. 59",
                        found_value=nt[-10:], expected_value="без точки",
                        recommendation="Удалите точку",
                    ))

        appendices.append({"idx": i, "letter": letter})

    if refs_order and appendices:
        app_letters = [a["letter"] for a in appendices]
        filtered    = [r for r in refs_order if r in app_letters]
        if filtered and filtered != app_letters[:len(filtered)]:
            errors.append(ReportError(
                id="П-4-order", code="П-4", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=appendices[0]["idx"], structural_path="Приложения"),
                fragment=f"В документе: {', '.join(app_letters)}",
                rule="Приложения — в порядке упоминания",
                rule_citation="§4.6, с. 59",
                found_value=', '.join(app_letters), expected_value=', '.join(filtered),
                recommendation="Переставьте приложения",
            ))
        missing = [r for r in refs_order if r not in app_letters]
        if missing:
            errors.append(ReportError(
                id="П-4-missing", code="П-4", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=appendices[0]["idx"], structural_path="Приложения"),
                fragment=f"Отсутствуют: {', '.join(missing)}",
                rule="Все упомянутые приложения должны быть в документе",
                rule_citation="§4.6, с. 59",
                found_value=f"нет {', '.join(missing)}", expected_value=', '.join(missing),
                recommendation="Добавьте приложения или исправьте ссылки",
            ))

    return errors


def validate_repeated_references(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Л-2: повторная ссылка → [там же, с. X]."""
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
                    location=ErrorLocation(paragraph_index=para_idx, structural_path=f"Абзац {para_idx+1}"),
                    fragment=text[:100],
                    rule="Повторная ссылка → [там же, с. X]",
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
                id=f"Л-2-next-{para_idx+1}-{last_src}", code="Л-2", type="formatting", severity="error",
                location=ErrorLocation(paragraph_index=para_idx+1, structural_path=f"Абзац {para_idx+2}"),
                fragment=next_text[:100],
                rule="Повторная ссылка в следующем абзаце → [там же, с. X]",
                rule_citation="§4.3, с. 49",
                found_value=fm.group(0), expected_value="[там же, с. X]",
                recommendation="Замените на [там же, с. X]",
            ))

    return errors


def validate_list_numbering(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Устарело — логика в validate_references_format."""
    return []


def validate_format(docx_path: str, rules: dict[str, Any]) -> ValidationReport:
    """Полная валидация DOCX-документа."""
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