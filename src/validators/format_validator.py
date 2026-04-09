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


def check_paragraph_formatting(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет форматирование абзацев.
    
    А) Межстрочный интервал (Ф-2)
    Б) Выравнивание (Ф-3)
    В) Отступ первой строки (Ф-5)
    Г) Интервалы до/после (Ф-6)
    """
    errors: list[ReportError] = []
    
    expected_line_spacing = rules["paragraph"]["line_spacing_twips"]  # 420
    tolerance_dxa = rules["tolerances"]["dxa"]  # 20
    expected_first_line_indent = 720  # DXA
    expected_before_after = 0  # twips
    
    heading_styles = {"Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"}
    
    # Паттерны для распознавания заголовков
    chapter_heading_pattern = rules.get("chapter_heading_pattern", r"^Глава \d+\.\s.+")
    paragraph_heading_pattern = rules.get("paragraph_heading_pattern", r"^\d+\.\d+\.\s.+")
    
    for para_index, para in enumerate(doc.paragraphs):
        # Пропускаем заголовки и пустые абзацы
        if para.style and para.style.name in heading_styles:
            continue
        if not para.text.strip():
            continue
        
        # Пропускаем абзацы, которые являются подписями таблиц или рисунков
        text_stripped = para.text.strip()
        if (text_stripped.startswith('Таблица') or 
            text_stripped.startswith('Рис.') or
            text_stripped.startswith('Рисунок')):
            continue
        
        # Дополнительная проверка: если у абзаца есть w:outlineLvl – это заголовок
        pPr = para._p.pPr
        if pPr is not None:
            outline_lvl = pPr.find(qn('w:outlineLvl'))
            if outline_lvl is not None:
                continue
        
        # Проверка по паттернам заголовков (для пользовательских стилей)
        if (re.match(chapter_heading_pattern, text_stripped) or 
            re.match(paragraph_heading_pattern, text_stripped)):
            continue
        
        # А) Межстрочный интервал (Ф-2)
        spacing_el = pPr.find(qn('w:spacing')) if pPr else None
        if spacing_el is not None:
            line_val = spacing_el.get(qn('w:line'))
            if line_val is not None:
                try:
                    actual_spacing = int(line_val)
                    if abs(actual_spacing - expected_line_spacing) > tolerance_dxa:
                        errors.append(ReportError(
                            id=f"Ф-2-{para_index}",
                            code="Ф-2",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=para_index,
                                structural_path=f"Абзац {para_index + 1}"
                            ),
                            fragment=para.text[:100],
                            rule="Межстрочный интервал должен быть 1.5 (420 twips)",
                            rule_citation="§4.2, с. 47",
                            found_value=str(actual_spacing),
                            expected_value=str(expected_line_spacing),
                            recommendation="Установите межстрочный интервал 1.5"
                        ))
                except ValueError:
                    pass
        
        # Б) Выравнивание (Ф-3)
        jc_el = pPr.find(qn('w:jc')) if pPr else None
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
                        structural_path=f"Абзац {para_index + 1}"
                    ),
                    fragment=para.text[:100],
                    rule="Текст должен быть выровнен по ширине",
                    rule_citation="§4.2, с. 47",
                    found_value=alignment or "не задано",
                    expected_value="both",
                    recommendation="Установите выравнивание по ширине"
                ))
        
        # В) Отступ первой строки (Ф-5)
        ind_el = pPr.find(qn('w:ind')) if pPr else None
        if ind_el is not None:
            first_line = ind_el.get(qn('w:firstLine'))
            if first_line is not None:
                try:
                    actual_first_line = int(first_line)
                    if abs(actual_first_line - expected_first_line_indent) > tolerance_dxa:
                        errors.append(ReportError(
                            id=f"Ф-5-{para_index}",
                            code="Ф-5",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=para_index,
                                structural_path=f"Абзац {para_index + 1}"
                            ),
                            fragment=para.text[:100],
                            rule="Отступ первой строки должен быть 1.25 см (720 DXA)",
                            rule_citation="§4.2, с. 47",
                            found_value=str(actual_first_line),
                            expected_value=str(expected_first_line_indent),
                            recommendation="Установите отступ первой строки 1.25 см"
                        ))
                except ValueError:
                    pass
        
        # Г) Интервалы до/после (Ф-6)
        if spacing_el is not None:
            before_val = spacing_el.get(qn('w:before'))
            after_val = spacing_el.get(qn('w:after'))
            
            if before_val is not None:
                try:
                    actual_before = int(before_val)
                    if actual_before != expected_before_after:
                        errors.append(ReportError(
                            id=f"Ф-6-before-{para_index}",
                            code="Ф-6",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=para_index,
                                structural_path=f"Абзац {para_index + 1}"
                            ),
                            fragment=para.text[:100],
                            rule="Интервалы до и после абзаца должны быть 0",
                            rule_citation="§4.2, с. 47",
                            found_value=str(actual_before),
                            expected_value=str(expected_before_after),
                            recommendation="Установите интервал перед абзацем 0"
                        ))
                except ValueError:
                    pass
            
            if after_val is not None:
                try:
                    actual_after = int(after_val)
                    if actual_after != expected_before_after:
                        errors.append(ReportError(
                            id=f"Ф-6-after-{para_index}",
                            code="Ф-6",
                            type="formatting",
                            severity="error",
                            location=ErrorLocation(
                                paragraph_index=para_index,
                                structural_path=f"Абзац {para_index + 1}"
                            ),
                            fragment=para.text[:100],
                            rule="Интервалы до и после абзаца должны быть 0",
                            rule_citation="§4.2, с. 47",
                            found_value=str(actual_after),
                            expected_value=str(expected_before_after),
                            recommendation="Установите интервал после абзаца 0"
                        ))
                except ValueError:
                    pass
    
    return errors


def check_margins(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет поля документа.
    
    Ожидаемые значения из rules["margins_dxa"]: left, right, top, bottom
    Допуск: rules["tolerances"]["dxa"]
    """
    errors: list[ReportError] = []
    
    section = doc.sections[0]
    EMU_PER_DXA = 635
    tolerance_dxa = rules["tolerances"]["dxa"]
    tolerance_emu = tolerance_dxa * EMU_PER_DXA
    
    margins_config = {
        "left": section.left_margin,
        "right": section.right_margin,
        "top": section.top_margin,
        "bottom": section.bottom_margin
    }
    
    for margin_name, margin_emu in margins_config.items():
        expected_dxa = rules["margins_dxa"][margin_name]
        actual_dxa = round(margin_emu / EMU_PER_DXA)
        
        if abs(actual_dxa - expected_dxa) > tolerance_dxa:
            errors.append(ReportError(
                id=f"Ф-4-{margin_name}",
                code="Ф-4",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=0,
                    structural_path="Поля документа"
                ),
                fragment=f"Поле {margin_name}",
                rule=f"Поле {margin_name} должно быть {expected_dxa} DXA",
                rule_citation="§4.2, с. 47",
                found_value=str(actual_dxa),
                expected_value=str(expected_dxa),
                recommendation=f"Установите поле {margin_name} равным {expected_dxa} DXA"
            ))
    
    return errors


def validate_structure(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет структуру документа.
    
    С-1: Обязательные разделы
    С-2: Приложения (нумерация и ссылки)
    С-3: Разделы с новой страницы
    С-4: Параграфы не с новой страницы
    С-5: Формат заголовков глав
    С-6: Нумерация параграфов
    С-7: Заголовки не bold/italic/underline
    С-8: Заголовки по центру без отступа
    С-9: Нет точки в конце заголовка
    С-10: Внутри параграфов нет подзаголовков
    """
    errors: list[ReportError] = []
    
    # Собираем все заголовки
    titles_lower = [
        p.text.strip().lower() 
        for p in doc.paragraphs 
        if p.style and p.style.name in ("Heading 1", "Heading 2")
    ]
    
    # С-1: Обязательные разделы
    for section_name in rules["required_sections"]:
        if not any(section_name.lower() in title for title in titles_lower):
            errors.append(ReportError(
                id=f"С-1-{section_name}",
                code="С-1",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=0,
                    structural_path="Структура документа"
                ),
                fragment=section_name,
                rule=f"Документ должен содержать раздел '{section_name}'",
                rule_citation="§3.2, с. 42",
                found_value="раздел отсутствует",
                expected_value=section_name,
                recommendation=f"Добавьте раздел '{section_name}' в документ"
            ))
    
    # Служебные заголовки для пропуска
    service_titles = ["введение", "заключение", "список литературы", "содержание"]
    
    pattern = rules.get("chapter_heading_pattern", r"^Глава \d+\.\s.+")
    paragraph_heading_pattern = rules.get("paragraph_heading_pattern", r"^\d+\.\d+(\.\d+)?\s.+")
    
    # Для проверки С-2: поиск приложений и ссылок на них
    has_appendix = False
    appendix_pattern = re.compile(r"Приложение\s+[A-ZА-Я]", re.IGNORECASE)
    appendix_ref_pattern = re.compile(r"\(прил\.\s*\d+\)", re.IGNORECASE)
    appendix_references_found = False
    
    # Для проверки С-3: отслеживание текущего раздела
    current_section_start_idx = None
    section_names = ["содержание", "введение", "заключение", "список литературы"]
    
    for para_idx, para in enumerate(doc.paragraphs):
        if not para.style or "Heading" not in para.style.name:
            continue
        
        title = para.text.strip()
        title_lower = title.lower()
        
        # Проверка наличия приложений
        if "приложен" in title_lower:
            has_appendix = True
        
        # Проверка С-3: разделы должны начинаться с новой страницы
        is_new_section = False
        for sec_name in section_names:
            if sec_name in title_lower:
                is_new_section = True
                break
        
        # Также главы считаются новыми разделами
        if para.style.name == "Heading 1" and not any(s in title_lower for s in service_titles):
            is_new_section = True
        
        if is_new_section:
            # Проверяем наличие page break перед этим заголовком
            pPr = para._p.find(qn('w:pPr'))
            has_page_break = False
            
            if pPr is not None:
                # Проверяем w:pageBreakBefore
                page_break_before = pPr.find(qn('w:pageBreakBefore'))
                if page_break_before is not None:
                    val = page_break_before.get(qn('w:val'))
                    if val in ('1', 'true', 'on'):
                        has_page_break = True
                
                # Проверяем наличие разрыва страницы в предыдущем абзаце
                if para_idx > 0:
                    prev_para = doc.paragraphs[para_idx - 1]
                    prev_pPr = prev_para._p.find(qn('w:pPr'))
                    if prev_pPr is not None:
                        # Проверяем w:br w:type="page"
                        for br in prev_pPr.findall(qn('w:br')):
                            br_type = br.get(qn('w:type'))
                            if br_type == 'page':
                                has_page_break = True
                                break
            
            if not has_page_break:
                errors.append(ReportError(
                    id=f"С-3-{para_idx}",
                    code="С-3",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Заголовок '{title[:50]}'"
                    ),
                    fragment=title[:100],
                    rule="Каждый новый раздел должен начинаться с новой страницы",
                    rule_citation="§4.2, с. 47",
                    found_value="нет разрыва страницы",
                    expected_value="разрыв страницы перед разделом",
                    recommendation="Добавьте разрыв страницы перед началом раздела"
                ))
        
        # Проверка С-4: параграфы не должны начинаться с новой страницы
        if para.style.name in ("Heading 2", "Heading 3"):
            pPr = para._p.find(qn('w:pPr'))
            has_page_break = False
            
            if pPr is not None:
                page_break_before = pPr.find(qn('w:pageBreakBefore'))
                if page_break_before is not None:
                    val = page_break_before.get(qn('w:val'))
                    if val in ('1', 'true', 'on'):
                        has_page_break = True
            
            if has_page_break:
                errors.append(ReportError(
                    id=f"С-4-{para_idx}",
                    code="С-4",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Параграф '{title[:50]}'"
                    ),
                    fragment=title[:100],
                    rule="Параграфы не должны начинаться с новой страницы",
                    rule_citation="§4.2, с. 47",
                    found_value="есть разрыв страницы",
                    expected_value="нет разрыва страницы",
                    recommendation="Удалите разрыв страницы перед параграфом"
                ))
        
        # С-5: Формат заголовков глав (пропускаем служебные)
        if para.style.name == "Heading 1":
            if not any(s in title_lower for s in service_titles):
                if not re.match(pattern, title):
                    errors.append(ReportError(
                        id=f"С-5-{para_idx}",
                        code="С-5",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=para_idx,
                            structural_path=f"Заголовок {para_idx + 1}"
                        ),
                        fragment=title[:100],
                        rule="Заголовок главы должен соответствовать паттерну 'Глава N. Название'",
                        rule_citation="§3.3, с. 43",
                        found_value=title[:100],
                        expected_value="Глава N. Название",
                        recommendation="Измените формат заголовка главы"
                    ))
        
        # С-6: Проверка нумерации параграфов (Heading 2, Heading 3)
        if para.style.name in ("Heading 2", "Heading 3"):
            if not re.match(paragraph_heading_pattern, title):
                errors.append(ReportError(
                    id=f"С-6-{para_idx}",
                    code="С-6",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Параграф {para_idx + 1}"
                    ),
                    fragment=title[:100],
                    rule="Параграфы должны иметь нумерацию вида '1.1.' или '1.1.1.'",
                    rule_citation="§4.2, с. 47",
                    found_value=title[:100],
                    expected_value="N.N. Название или N.N.N. Название",
                    recommendation="Измените формат заголовка параграфа"
                ))
        
        # С-7: Заголовки не bold/italic/underline
        has_formatting = False
        for run in para.runs:
            if run.font.bold or run.font.italic or run.font.underline:
                has_formatting = True
                break
        
        if has_formatting:
            errors.append(ReportError(
                id=f"С-7-{para_idx}",
                code="С-7",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}"
                ),
                fragment=title[:100],
                rule="Заголовки не должны быть жирными, курсивом или подчёркнутыми",
                rule_citation="§3.3, с. 43",
                found_value="bold/italic/underline",
                expected_value="обычный текст",
                recommendation="Уберите жирность, курсив и подчёркивание из заголовка"
            ))
        
        # С-8: Заголовки по центру
        pPr = para._p.find(qn('w:pPr'))
        jc_el = pPr.find(qn('w:jc')) if pPr else None
        alignment = jc_el.get(qn('w:val')) if jc_el else None
        
        if alignment != "center":
            errors.append(ReportError(
                id=f"С-8-{para_idx}",
                code="С-8",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}"
                ),
                fragment=title[:100],
                rule="Заголовки должны быть выровнены по центру",
                rule_citation="§3.3, с. 43",
                found_value=alignment or "не задано",
                expected_value="center",
                recommendation="Установите выравнивание заголовка по центру"
            ))
        
        # С-9: Нет точки в конце заголовка
        if title.endswith('.'):
            errors.append(ReportError(
                id=f"С-9-{para_idx}",
                code="С-9",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Заголовок {para_idx + 1}"
                ),
                fragment=title[:100],
                rule="В конце заголовка не должно быть точки",
                rule_citation="§3.3, с. 43",
                found_value=title[-10:] if len(title) > 10 else title,
                expected_value="без точки",
                recommendation="Удалите точку в конце заголовка"
            ))
    
    # С-10: Проверка отсутствия подзаголовков внутри параграфов
    # Ищем heading стили между заголовками параграфов
    in_paragraph = False
    paragraph_start_idx = None
    
    for para_idx, para in enumerate(doc.paragraphs):
        if not para.style:
            continue
        
        style_name = para.style.name
        
        # Определяем начало параграфа (Heading 2 или Heading 3)
        if style_name in ("Heading 2", "Heading 3"):
            in_paragraph = True
            paragraph_start_idx = para_idx
            continue
        
        # Если мы внутри параграфа и нашли заголовок уровня 4+ — это нарушение С-10
        if in_paragraph and style_name in ("Heading 4", "Heading 5", "Heading 6"):
            title = para.text.strip()
            if title:  # Пропускаем пустые заголовки
                errors.append(ReportError(
                    id=f"С-10-{para_idx}",
                    code="С-10",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Подзаголовок внутри параграфа {paragraph_start_idx}"
                    ),
                    fragment=title[:100],
                    rule="Внутри параграфов не должно быть подзаголовков",
                    rule_citation="§4.2, с. 47",
                    found_value=title[:100],
                    expected_value="обычный текст без подзаголовков",
                    recommendation="Удалите подзаголовок или оформите его как обычный текст"
                ))
        
        # Выходим из режима параграфа при встрече основного текста или другого заголовка верхнего уровня
        if in_paragraph:
            # Если встретили Heading 1 (новая глава) или Normal/другой стиль с текстом - выходим из параграфа
            if style_name == "Heading 1":
                in_paragraph = False
            elif style_name not in ("Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"):
                if para.text.strip():  # Если есть текст, считаем что параграф начался
                    in_paragraph = False
    
    # С-2: Проверка приложений (если они есть)
    if has_appendix:
        # Проверяем наличие ссылок на приложения в тексте
        full_text = "\n".join([p.text for p in doc.paragraphs])
        appendix_refs_found = bool(appendix_ref_pattern.search(full_text))
        
        if not appendix_refs_found:
            errors.append(ReportError(
                id="С-2-appx-ref",
                code="С-2",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=0,
                    structural_path="Приложения"
                ),
                fragment="Приложение",
                rule="Приложения должны иметь ссылки из текста в формате '(прил. N)'",
                rule_citation="§3.8, с. 44",
                found_value="ссылки на приложения отсутствуют",
                expected_value="(прил. N)",
                recommendation="Добавьте ссылки на приложения в тексте"
            ))
    
    return errors


def get_effective_font_size(run, doc) -> float | None:
    """
    Получает эффективный размер шрифта для run, учитывая наследование.
    
    Порядок проверки:
    1. Явный атрибут w:sz в w:rPr элемента run
    2. Размер шрифта из стиля абзаца (para.style.font.size)
    3. Размер шрифта по умолчанию (12 пт)
    
    Возвращает размер в пунктах (pt) или None, если не удалось определить.
    """
    from docx.oxml.ns import qn
    
    # 1. Проверяем явный размер через python-docx
    if run.font.size is not None:
        return run.font.size.pt
    
    # 2. Проверяем наличие w:sz в XML напрямую
    rPr = run._element.find(qn('w:rPr'))
    if rPr is not None:
        sz_el = rPr.find(qn('w:sz'))
        if sz_el is not None:
            val = sz_el.get(qn('w:val'))
            if val is not None:
                try:
                    # Значение в полупунктах, делим на 2
                    return int(val) / 2.0
                except ValueError:
                    pass
        
        # Также проверяем w:szCs (для сложного сценария)
        szcs_el = rPr.find(qn('w:szCs'))
        if szcs_el is not None:
            val = szcs_el.get(qn('w:val'))
            if val is not None:
                try:
                    return int(val) / 2.0
                except ValueError:
                    pass
    
    # 3. Пытаемся получить размер из стиля абзаца
    para = run._parent
    while para is not None and not hasattr(para, 'style'):
        para = para._parent
    
    if para is not None and hasattr(para, 'style') and para.style is not None:
        try:
            style_font_size = para.style.font.size
            if style_font_size is not None:
                return style_font_size.pt
        except Exception:
            pass
    
    # 4. Возвращаем значение по умолчанию (12 пт)
    return 12.0


def validate_tables(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет форматирование таблиц.
    
    Т-1: Подпись «Таблица N» над таблицей, выравнивание по правому краю
    Т-4: Шрифт в таблице Times New Roman, 12 пт (допустимо 11 пт)
    Т-12: Дробные числа с запятой, а не с точкой
    """
    errors: list[ReportError] = []
    
    # Получаем элементы body для анализа потока документа
    body = doc.element.body
    
    # Собираем информацию о потоке элементов (параграфы и таблицы)
    elements_flow = []  # список кортежей (type, index, element)
    para_index = 0
    
    for i, child in enumerate(body):
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            elements_flow.append(('paragraph', para_index, child))
            para_index += 1
        elif tag == 'tbl':
            elements_flow.append(('table', len([e for e in elements_flow if e[0] == 'table']), child))
    
    # Т-1: Проверка подписи таблиц
    table_caption_pattern = re.compile(r'^Таблица\s*\d+', re.IGNORECASE)
    
    for elem_type, elem_idx, element in elements_flow:
        if elem_type != 'table':
            continue
        
        table_index = elem_idx
        # Ищем подпись непосредственно перед таблицей
        caption_found = False
        caption_para = None
        caption_para_idx = None
        
        # Проходим назад от таблицы, ищем подпись
        for j in range(elements_flow.index((elem_type, elem_idx, element)) - 1, -1, -1):
            prev_type, prev_idx, prev_element = elements_flow[j]
            if prev_type != 'paragraph':
                break
            
            # Получаем текст параграфа
            para_text = ''
            for t in prev_element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if t.text:
                    para_text += t.text
            para_text = para_text.strip()
            
            # Проверяем, является ли это подписью таблицы
            if table_caption_pattern.match(para_text):
                caption_found = True
                caption_para = prev_element
                caption_para_idx = prev_idx
                
                # Проверяем выравнивание (должно быть right)
                pPr = prev_element.find(qn('w:pPr'))
                jc_el = pPr.find(qn('w:jc')) if pPr is not None else None
                alignment = jc_el.get(qn('w:val')) if jc_el is not None else None
                
                if alignment != 'right':
                    errors.append(ReportError(
                        id=f"Т-1-caption-align-{prev_idx}",
                        code="Т-1",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=prev_idx,
                            structural_path=f"Подпись таблицы {table_index + 1}"
                        ),
                        fragment=para_text[:100],
                        rule="Подпись таблицы должна быть выровнена по правому краю",
                        rule_citation="§4.5, с. 51",
                        found_value=alignment or "не задано",
                        expected_value="right",
                        recommendation="Установите выравнивание подписи таблицы по правому краю"
                    ))
                
                # Проверяем, нет ли точки в конце подписи
                if para_text.endswith('.'):
                    errors.append(ReportError(
                        id=f"Т-1-caption-dot-{prev_idx}",
                        code="Т-1",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=prev_idx,
                            structural_path=f"Подпись таблицы {table_index + 1}"
                        ),
                        fragment=para_text[:100],
                        rule="В конце подписи таблицы не должно быть точки",
                        rule_citation="§4.5, с. 51",
                        found_value=para_text[-10:] if len(para_text) > 10 else para_text,
                        expected_value="без точки",
                        recommendation="Удалите точку в конце подписи таблицы"
                    ))
                
                break
            
            # Если параграф не пустой и не подпись, значит подписи нет непосредственно перед таблицей
            if para_text:
                break
        
        if not caption_found:
            # Подпись не найдена непосредственно перед таблицей
            errors.append(ReportError(
                id=f"Т-1-no-caption-{table_index}",
                code="Т-1",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=0,
                    structural_path=f"Таблица {table_index + 1}"
                ),
                fragment=f"Таблица {table_index + 1}",
                rule="Над таблицей должна быть подпись «Таблица N»",
                rule_citation="§4.5, с. 51",
                found_value="подпись отсутствует или расположена неверно",
                expected_value="Таблица N над таблицей",
                recommendation="Добавьте подпись «Таблица N» непосредственно над таблицей"
            ))
    
    # Т-4: Проверка шрифта в таблицах
    expected_font_name = "Times New Roman"
    min_font_size_pt = 11
    max_font_size_pt = 12
    
    tables_list = list(doc.tables)
    for table_idx, table in enumerate(tables_list):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para in cell.paragraphs:
                    for run in para.runs:
                        font_name = run.font.name
                        
                        # Проверка названия шрифта
                        if font_name and font_name != expected_font_name:
                            errors.append(ReportError(
                                id=f"Т-4-font-name-{table_idx}-{row_idx}-{cell_idx}",
                                code="Т-4",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=0,
                                    structural_path=f"Таблица {table_idx + 1}, ячейка [{row_idx + 1}, {cell_idx + 1}]"
                                ),
                                fragment=para.text[:50],
                                rule="Шрифт в таблице должен быть Times New Roman",
                                rule_citation="§4.5, с. 51",
                                found_value=font_name,
                                expected_value=expected_font_name,
                                recommendation="Установите шрифт Times New Roman"
                            ))
                        
                        # Проверка размера шрифта (11-12 pt) с учётом наследования
                        font_size = get_effective_font_size(run, doc)
                        if font_size is not None:
                            if font_size < min_font_size_pt or font_size > max_font_size_pt:
                                errors.append(ReportError(
                                    id=f"Т-4-font-size-{table_idx}-{row_idx}-{cell_idx}",
                                    code="Т-4",
                                    type="formatting",
                                    severity="error",
                                    location=ErrorLocation(
                                        paragraph_index=0,
                                        structural_path=f"Таблица {table_idx + 1}, ячейка [{row_idx + 1}, {cell_idx + 1}]"
                                    ),
                                    fragment=para.text[:50],
                                    rule="Размер шрифта в таблице должен быть 11-12 пт",
                                    rule_citation="§4.5, с. 51",
                                    found_value=str(font_size),
                                    expected_value=f"{min_font_size_pt}-{max_font_size_pt}",
                                    recommendation="Установите размер шрифта 11-12 пт"
                                ))
    
    # Т-12: Проверка десятичного разделителя (запятая вместо точки)
    # Паттерн для поиска чисел с точкой как десятичным разделителем
    decimal_point_pattern = re.compile(r'\b\d+\.\d+\b')
    
    for table_idx, table in enumerate(tables_list):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para in cell.paragraphs:
                    text = para.text.strip()
                    if not text:
                        continue
                    
                    # Ищем числа с точкой
                    matches = decimal_point_pattern.findall(text)
                    if matches:
                        for match in matches:
                            errors.append(ReportError(
                                id=f"Т-12-decimal-{table_idx}-{row_idx}-{cell_idx}",
                                code="Т-12",
                                type="formatting",
                                severity="error",
                                location=ErrorLocation(
                                    paragraph_index=0,
                                    structural_path=f"Таблица {table_idx + 1}, ячейка [{row_idx + 1}, {cell_idx + 1}]"
                                ),
                                fragment=text[:100],
                                rule="Дробные числа должны использовать запятую как десятичный разделитель",
                                rule_citation="§4.5, с. 51",
                                found_value=match,
                                expected_value=match.replace('.', ','),
                                recommendation="Замените точку на запятую в дробных числах"
                            ))
    
    return errors


def validate_references_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет форматирование списка литературы.
    
    Л-1: формат ссылок [N] или [N, с. X]
    Л-3: порядок множественных ссылок
    Л-4: алфавитный порядок (сначала русские, затем иностранные)
    Л-5: сплошная нумерация источников
    Л-7: минимум 40 источников
    Л-8: 70% источников за последние 10 лет
    Л-9: формат автора "Фамилия, И. О."
    Л-10: URL с датой обращения
    Л-11: ссылка соответствует источнику в списке
    Л-12: длинные тире в библиографии
    """
    errors: list[ReportError] = []
    
    # Находим раздел списка литературы
    ref_section_paragraphs = []
    ref_section_start_idx = 0
    in_refs = False
    
    for para_idx, para in enumerate(doc.paragraphs):
        if "список литературы" in para.text.lower():
            in_refs = True
            ref_section_start_idx = para_idx + 1
            continue
        if in_refs and para.style and "Heading" in para.style.name:
            break
        if in_refs and para.text.strip():
            ref_section_paragraphs.append(para.text.strip())
    
    # Л-7: минимум 40 источников
    min_sources = rules.get("references", {}).get("min_sources", 40)
    if len(ref_section_paragraphs) < min_sources:
        errors.append(ReportError(
            id="Л-7-count",
            code="Л-7",
            type="formatting",
            severity="error",
            location=ErrorLocation(
                paragraph_index=0,
                structural_path="Список литературы"
            ),
            fragment="Список литературы",
            rule=f"Список литературы должен содержать не менее {min_sources} источников",
            rule_citation="§3.7, с. 44",
            found_value=str(len(ref_section_paragraphs)),
            expected_value=str(min_sources),
            recommendation="Добавьте недостающие источники в список литературы"
        ))
    
    # Л-5: проверка сплошной нумерации (1, 2, 3, ...)
    numbering_pattern = re.compile(r'^(\d+)\.')
    source_numbers = []
    for idx, para_text in enumerate(ref_section_paragraphs):
        match = numbering_pattern.match(para_text)
        if match:
            source_numbers.append(int(match.group(1)))
    
    # Проверка непрерывности нумерации
    if source_numbers:
        expected_numbers = list(range(1, len(source_numbers) + 1))
        for i, (actual, expected) in enumerate(zip(source_numbers, expected_numbers)):
            if actual != expected:
                errors.append(ReportError(
                    id=f"Л-5-num-{i}",
                    code="Л-5",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_section_start_idx + i,
                        structural_path="Список литературы"
                    ),
                    fragment=ref_section_paragraphs[i][:100],
                    rule="Нумерация источников должна быть сплошной: 1, 2, 3, ...",
                    rule_citation="§4.5, с. 52",
                    found_value=str(actual),
                    expected_value=str(expected),
                    recommendation=f"Исправьте номер источника на {expected}"
                ))
                break  # Сообщаем только о первой ошибке
    
    # Л-4: проверка алфавитного порядка (сначала кириллица, затем латиница)
    def extract_surname(text: str) -> tuple[str, str]:
        """Извлекает фамилию автора и определяет язык (cyrillic/latin)."""
        # Удаляем номер в начале
        clean_text = re.sub(r'^\d+\.\s*', '', text.strip())
        # Берём часть до первой запятой или точки
        author_part = re.split(r'[,.]', clean_text)[0].strip()
        # Определяем тип символов
        is_cyrillic = bool(re.search(r'[А-ЯЁа-яё]', author_part))
        return (author_part.lower(), 'cyrillic' if is_cyrillic else 'latin')
    
    def surname_sort_key(item: tuple[int, str]):
        """Ключ сортировки: сначала кириллица, потом латиница, внутри - по алфавиту."""
        idx, text = item
        surname, lang = extract_surname(text)
        # Кириллица < латиница (0 < 1)
        lang_order = 0 if lang == 'cyrillic' else 1
        return (lang_order, surname)
    
    if len(ref_section_paragraphs) > 1:
        indexed_sources = list(enumerate(ref_section_paragraphs))
        sorted_sources = sorted(indexed_sources, key=surname_sort_key)
        
        for i, (orig_idx, _) in enumerate(indexed_sources):
            sorted_idx, _ = sorted_sources[i]
            if orig_idx != sorted_idx:
                # Нашли нарушение порядка
                curr_surname, curr_lang = extract_surname(ref_section_paragraphs[orig_idx])
                next_surname, next_lang = extract_surname(ref_section_paragraphs[sorted_idx])
                
                errors.append(ReportError(
                    id=f"Л-4-order-{i}",
                    code="Л-4",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_section_start_idx + orig_idx,
                        structural_path="Список литературы"
                    ),
                    fragment=ref_section_paragraphs[orig_idx][:100],
                    rule="Источники должны быть расположены по алфавиту: сначала русские, затем иностранные",
                    rule_citation="§4.5, с. 52",
                    found_value=f"«{curr_surname}» после «{next_surname}»",
                    expected_value=f"«{next_surname}» перед «{curr_surname}»",
                    recommendation="Расположите источники в алфавитном порядке"
                ))
                break  # Только первая ошибка
    
    # Л-8: проверка актуальности источников (70% за последние 10 лет)
    current_year = datetime.now().year
    year_threshold = current_year - 10
    year_pattern = re.compile(r'\b(19|20)\d{2}\b')
    
    recent_sources_count = 0
    total_sources_with_year = 0
    
    for para_text in ref_section_paragraphs:
        year_match = year_pattern.search(para_text)
        if year_match:
            total_sources_with_year += 1
            year = int(year_match.group(0))
            if year >= year_threshold:
                recent_sources_count += 1
    
    if total_sources_with_year > 0:
        recent_percentage = (recent_sources_count / total_sources_with_year) * 100
        if recent_percentage < 70:
            errors.append(ReportError(
                id="Л-8-recency",
                code="Л-8",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx,
                    structural_path="Список литературы"
                ),
                fragment="Список литературы",
                rule=f"Не менее 70% источников должны быть опубликованы в последние {10} лет",
                rule_citation="§4.5, с. 52",
                found_value=f"{recent_percentage:.1f}%",
                expected_value=">= 70%",
                recommendation="Добавьте более свежие источники"
            ))
    
    # Л-9: проверка формата автора "Фамилия, И. О."
    # Русский паттерн: Фамилия, И. О.
    ru_author_pattern = re.compile(r'^\d+\.\s*[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?,\s[А-ЯЁ]\.\s[А-ЯЁ]\.')
    # Английский паттерн: Surname, I. I.
    en_author_pattern = re.compile(r'^\d+\.\s*[A-Z][a-z]+(?:-[A-Z][a-z]+)?,\s[A-Z]\.\s[A-Z]\.')
    
    for idx, para_text in enumerate(ref_section_paragraphs):
        # Пропускаем источники без автора (начинаются с названия, URLs и т.д.)
        if not re.match(r'^\d+\.\s*[А-ЯЁA-Z]', para_text):
            continue
        
        ru_match = ru_author_pattern.match(para_text)
        en_match = en_author_pattern.match(para_text)
        
        if not ru_match and not en_match:
            errors.append(ReportError(
                id=f"Л-9-author-{idx}",
                code="Л-9",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы"
                ),
                fragment=para_text[:100],
                rule="Автор должен быть указан в формате: Фамилия, И. О.",
                rule_citation="§4.5, с. 52",
                found_value=para_text[:50],
                expected_value="Фамилия, И. О.",
                recommendation="Исправьте формат указания автора"
            ))
    
    # Л-10: проверка URL с датой обращения
    url_pattern = re.compile(r'https?://[^\s]+')
    access_date_pattern = re.compile(r'\(дата обращения:\s*\d{2}\.\d{2}\.\d{4}\)')
    
    for idx, para_text in enumerate(ref_section_paragraphs):
        if url_pattern.search(para_text):
            if not access_date_pattern.search(para_text):
                errors.append(ReportError(
                    id=f"Л-10-url-{idx}",
                    code="Л-10",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_section_start_idx + idx,
                        structural_path="Список литературы"
                    ),
                    fragment=para_text[:100],
                    rule="Для URL-источников должна быть указана дата обращения в формате (дата обращения: ДД.ММ.ГГГГ)",
                    rule_citation="§4.5, с. 52",
                    found_value="URL без даты обращения",
                    expected_value="(дата обращения: ДД.ММ.ГГГГ)",
                    recommendation="Добавьте дату обращения после URL"
                ))
    
    # Л-11: проверка соответствия ссылок в тексте источникам в списке
    # Собираем все номера источников из списка литературы
    valid_source_numbers = set(source_numbers)
    
    # Находим все ссылки в тексте [N] и [N, с. X]
    ref_pattern = re.compile(r'\[(\d+)(?:\s*,\s*с\.\s*\d+)?\]')
    
    for para_idx, para in enumerate(doc.paragraphs):
        for match in ref_pattern.finditer(para.text):
            ref_number = int(match.group(1))
            if ref_number not in valid_source_numbers:
                errors.append(ReportError(
                    id=f"Л-11-ref-{para_idx}-{ref_number}",
                    code="Л-11",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Абзац {para_idx + 1}"
                    ),
                    fragment=match.group(0),
                    rule="Ссылка в тексте должна соответствовать источнику в списке литературы",
                    rule_citation="§4.3, с. 49",
                    found_value=f"№{ref_number}",
                    expected_value=f"номер от 1 до {len(valid_source_numbers)}",
                    recommendation=f"Исправьте ссылку или добавьте источник №{ref_number} в список литературы"
                ))
    
    # Л-12: проверка длинных тире (не дефисы)
    # Ищем дефисы, используемые как тире (между словами/числами, с пробелами)
    hyphen_as_dash_pattern = re.compile(r'\s-\s|\d-\d')
    
    for idx, para_text in enumerate(ref_section_paragraphs):
        if hyphen_as_dash_pattern.search(para_text):
            errors.append(ReportError(
                id=f"Л-12-hyphen-{idx}",
                code="Л-12",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_section_start_idx + idx,
                    structural_path="Список литературы"
                ),
                fragment=para_text[:100],
                rule="В библиографии должны использоваться длинные тире «–» (U+2013), а не дефисы «-»",
                rule_citation="§4.5, с. 52",
                found_value="-",
                expected_value="–",
                recommendation="Замените дефис на длинное тире"
            ))
    
    # Л-1: формат ссылок [N] или [N, с. X] — круглые скобки нарушение
    inline_pattern = re.compile(r'\(\d+\)')
    for para_idx, para in enumerate(doc.paragraphs):
        matches = inline_pattern.findall(para.text)
        if matches:
            errors.append(ReportError(
                id=f"Л-1-{para_idx}",
                code="Л-1",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Абзац {para_idx + 1}"
                ),
                fragment=para.text[:100],
                rule="Ссылки оформляются в квадратных скобках: [N] или [N, с. X]",
                rule_citation="§4.3, с. 49",
                found_value=matches[0],
                expected_value="[N] или [N, с. X]",
                recommendation="Замените круглые скобки на квадратные"
            ))
    
    # Л-3: порядок множественных ссылок
    multi_pattern = re.compile(r'\[(\d+(?:;\s*\d+)+)\]')
    for para_idx, para in enumerate(doc.paragraphs):
        for match in multi_pattern.finditer(para.text):
            nums = [int(n.strip()) for n in match.group(1).split(';')]
            if nums != sorted(nums):
                errors.append(ReportError(
                    id=f"Л-3-{para_idx}",
                    code="Л-3",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Абзац {para_idx + 1}"
                    ),
                    fragment=match.group(0),
                    rule="Несколько источников указываются в арифметическом порядке через ';'",
                    rule_citation="§4.3, с. 49",
                    found_value=match.group(0),
                    expected_value=f"[{'; '.join(str(n) for n in sorted(nums))}]",
                    recommendation="Расположите номера источников в порядке возрастания"
                ))
    
    return errors


def validate_typography_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет типографику текста.
    
    Н-2: пробелы между инициалами
    Н-4: кавычки-лапки
    Н-6: аббревиатуры без расшифровки
    """
    errors: list[ReportError] = []
    
    # Паттерны
    no_space_pattern = re.compile(r'[А-ЯЁ]\.[А-ЯЁ]\.[А-ЯЁ][а-яё]+')
    wrong_quotes = re.compile(r'"[^"]*"')
    abbrev_pattern = re.compile(r'\b[А-ЯЁ]{2,}\b')
    explained_pattern = re.compile(r'\([А-ЯЁ]{2,}\)')
    
    found_abbrevs: set[str] = set()
    
    for para_idx, para in enumerate(doc.paragraphs):
        text = para.text
        
        # Н-2: пробелы между инициалами
        match_no_space = no_space_pattern.search(text)
        if match_no_space:
            errors.append(ReportError(
                id=f"Н-2-{para_idx}",
                code="Н-2",
                type="style",
                severity="warning",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Абзац {para_idx + 1}"
                ),
                fragment=text[:100],
                rule="Между инициалами и перед фамилией должен быть пробел: И. И. Иванов",
                rule_citation="§4.2, с. 48",
                found_value=match_no_space.group(0),
                expected_value="И. И. Иванов",
                recommendation="Добавьте пробелы между инициалами"
            ))
        
        # Н-4: кавычки-лапки
        if wrong_quotes.search(text):
            errors.append(ReportError(
                id=f"Н-4-{para_idx}",
                code="Н-4",
                type="style",
                severity="warning",
                location=ErrorLocation(
                    paragraph_index=para_idx,
                    structural_path=f"Абзац {para_idx + 1}"
                ),
                fragment=text[:100],
                rule="Кавычки должны быть угловыми: «текст»",
                rule_citation="§4.2, с. 48",
                found_value='"..."',
                expected_value='«...»',
                recommendation='Замените кавычки "..." на «...»'
            ))
        
        # Расшифровки аббревиатур
        for m in explained_pattern.finditer(text):
            found_abbrevs.add(m.group(0)[1:-1])
        
        # Н-6: аббревиатуры без расшифровки
        for m in abbrev_pattern.finditer(text):
            abbrev = m.group(0)
            if abbrev not in found_abbrevs:
                errors.append(ReportError(
                    id=f"Н-6-{para_idx}-{abbrev}",
                    code="Н-6",
                    type="style",
                    severity="warning",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Абзац {para_idx + 1}"
                    ),
                    fragment=text[:100],
                    rule="При первом использовании аббревиатуры дайте расшифровку: полное название (АБВ)",
                    rule_citation="§4.1, с. 46",
                    found_value=abbrev,
                    expected_value=f"полное название ({abbrev})",
                    recommendation=f"Расшифруйте аббревиатуру {abbrev} при первом использовании"
                ))
                found_abbrevs.add(abbrev)
    
    return errors


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
    errors: list[ReportError] = []
    
    # Запускаем все проверки
    errors.extend(check_font_formatting(doc, rules))
    errors.extend(check_paragraph_formatting(doc, rules))
    errors.extend(check_margins(doc, rules))
    errors.extend(validate_structure(doc, rules))
    errors.extend(validate_tables(doc, rules))
    errors.extend(validate_references_format(doc, rules))
    errors.extend(validate_typography_format(doc, rules))
    
    # Подсчитываем статистику
    formatting_count = sum(1 for e in errors if e.type == "formatting")
    style_count = sum(1 for e in errors if e.type == "style")
    citation_count = sum(1 for e in errors if e.type == "citation_check")
    
    return ValidationReport(
        doc_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        summary=ReportSummary(
            total_errors=len(errors),
            formatting=formatting_count,
            style=style_count,
            citations=citation_count
        ),
        errors=errors
    )
