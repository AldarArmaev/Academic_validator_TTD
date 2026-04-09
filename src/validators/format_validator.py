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
    С-5: Формат заголовков глав
    С-7: Заголовки не bold/italic/underline
    С-8: Заголовки по центру без отступа
    С-9: Нет точки в конце заголовка
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
    
    for para_idx, para in enumerate(doc.paragraphs):
        if not para.style or "Heading" not in para.style.name:
            continue
        
        title = para.text.strip()
        title_lower = title.lower()
        
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
    Л-4: алфавитный порядок (русские, затем иностранные)
    Л-5: сплошная нумерация источников
    Л-7: минимум 40 источников
    Л-8: 70% источников за последние 10 лет
    Л-9: формат автора "Фамилия, И. О."
    Л-10: дата обращения для URL
    Л-11: соответствие ссылок источникам
    Л-12: длинные тире в библиографии
    """
    errors: list[ReportError] = []
    
    # Находим раздел списка литературы
    ref_section_paragraphs = []
    ref_start_para_idx = 0
    in_refs = False
    
    for para_idx, para in enumerate(doc.paragraphs):
        if "список литературы" in para.text.lower():
            in_refs = True
            ref_start_para_idx = para_idx
            continue
        if in_refs and para.style and "Heading" in para.style.name:
            break
        if in_refs and para.text.strip():
            # Проверяем, что строка похожа на источник в списке литературы
            # (начинается с цифры и точки, или это продолжение предыдущего источника)
            if re.match(r'^\d+\.', para.text.strip()):
                ref_section_paragraphs.append(para.text.strip())
            elif len(ref_section_paragraphs) > 0:
                # Это может быть продолжение предыдущего источника (многострочный)
                # Но для простоты игнорируем такие строки
                pass
    
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
    
    # ============================================
    # Л-4: Алфавитный порядок (русские, затем иностранные)
    # ============================================
    def extract_author_name(text: str) -> tuple[str, bool]:
        """
        Извлекает фамилию первого автора из строки библиографии.
        Возвращает (фамилия, is_cyrillic).
        """
        text = text.strip()
        if not text:
            return ("", True)
        
        # Сначала удаляем номер источника в начале (например, "1. ")
        text_without_num = re.sub(r'^\d+\.\s*', '', text)
        
        # Попытка найти фамилию до первой запятой или точки
        # Формат: "Фамилия, И. О." или "Familiya, I. O."
        match = re.match(r'^([А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?|[A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)?),', text_without_num)
        if match:
            surname = match.group(1)
            is_cyrillic = bool(re.search(r'[А-ЯЁа-яё]', surname))
            return (surname.lower(), is_cyrillic)
        
        # Если нет запятой, пробуем найти до точки (для иностранных источников)
        match = re.match(r'^([А-ЯЁ][а-яё]+|[A-Z][a-zA-Z]+)\.', text_without_num)
        if match:
            surname = match.group(1)
            is_cyrillic = bool(re.search(r'[А-ЯЁа-яё]', surname))
            return (surname.lower(), is_cyrillic)
        
        # Если ничего не найдено, используем начало строки
        first_word = text_without_num.split()[0] if text_without_num.split() else ""
        is_cyrillic = bool(re.search(r'[А-ЯЁа-яё]', first_word))
        return (first_word.lower(), is_cyrillic)
    
    def compare_authors(author1: tuple[str, bool], author2: tuple[str, bool]) -> int:
        """
        Сравнивает двух авторов с учётом приоритета кириллицы.
        Возвращает -1, 0, или 1.
        """
        name1, cyrillic1 = author1
        name2, cyrillic2 = author2
        
        # Кириллица перед латиницей
        if cyrillic1 and not cyrillic2:
            return -1
        if not cyrillic1 and cyrillic2:
            return 1
        
        # Сравниваем по алфавиту
        if name1 < name2:
            return -1
        elif name1 > name2:
            return 1
        return 0
    
    if len(ref_section_paragraphs) >= 2:
        authors = [extract_author_name(p) for p in ref_section_paragraphs]
        for i in range(len(authors) - 1):
            cmp_result = compare_authors(authors[i], authors[i + 1])
            if cmp_result > 0:
                current_name = ref_section_paragraphs[i].split(',')[0] if ',' in ref_section_paragraphs[i] else ref_section_paragraphs[i].split('.')[0]
                next_name = ref_section_paragraphs[i + 1].split(',')[0] if ',' in ref_section_paragraphs[i + 1] else ref_section_paragraphs[i + 1].split('.')[0]
                errors.append(ReportError(
                    id=f"Л-4-order-{i}",
                    code="Л-4",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_start_para_idx + i + 1,
                        structural_path=f"Список литературы, источник {i + 1}"
                    ),
                    fragment=ref_section_paragraphs[i][:100],
                    rule="Источники должны быть расположены по алфавиту: сначала русские (кириллица), затем иностранные (латиница)",
                    rule_citation="§4.5, с. 52",
                    found_value=f"{current_name} ... {next_name}",
                    expected_value=f"{next_name} должен быть после {current_name}",
                    recommendation=f"Переместите источник «{next_name}» после «{current_name}»"
                ))
    
    # ============================================
    # Л-5: Сплошная нумерация источников
    # ============================================
    numbering_pattern = re.compile(r'^(\d+)\.')
    source_numbers = []
    for idx, ref_text in enumerate(ref_section_paragraphs):
        match = numbering_pattern.match(ref_text)
        if match:
            source_numbers.append((idx, int(match.group(1))))
        else:
            # Строка без номера
            source_numbers.append((idx, None))
    
    # Проверка непрерывности нумерации
    expected_num = 1
    for idx, num in source_numbers:
        if num is None:
            errors.append(ReportError(
                id=f"Л-5-missing-{idx}",
                code="Л-5",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_start_para_idx + idx + 1,
                    structural_path=f"Список литературы, источник {idx + 1}"
                ),
                fragment=ref_section_paragraphs[idx][:100],
                rule="Нумерация источников должна быть сплошной: 1, 2, 3, ...",
                rule_citation="§4.5, с. 52",
                found_value="номер отсутствует",
                expected_value=str(expected_num),
                recommendation=f"Добавьте номер {expected_num}. перед источником"
            ))
        elif num != expected_num:
            errors.append(ReportError(
                id=f"Л-5-wrong-{idx}",
                code="Л-5",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=ref_start_para_idx + idx + 1,
                    structural_path=f"Список литературы, источник {idx + 1}"
                ),
                fragment=ref_section_paragraphs[idx][:100],
                rule="Нумерация источников должна быть сплошной: 1, 2, 3, ...",
                rule_citation="§4.5, с. 52",
                found_value=str(num),
                expected_value=str(expected_num),
                recommendation=f"Исправьте номер источника на {expected_num}"
            ))
            expected_num = num + 1
        else:
            expected_num += 1
    
    # ============================================
    # Л-8: Основная часть источников — последние 10 лет (>= 70%)
    # ============================================
    current_year = datetime.now().year
    min_year = current_year - 10
    year_pattern = re.compile(r'\b(19|20)\d{2}\b')
    
    recent_count = 0
    total_with_year = 0
    
    for idx, ref_text in enumerate(ref_section_paragraphs):
        years = year_pattern.findall(ref_text)
        if years:
            # Берём последний найденный год (обычно это год публикации)
            year_matches = list(year_pattern.finditer(ref_text))
            if year_matches:
                last_match = year_matches[-1]
                year = int(last_match.group(0))
                total_with_year += 1
                if year >= min_year:
                    recent_count += 1
    
    if total_with_year > 0:
        recent_percentage = (recent_count / total_with_year) * 100
        if recent_percentage < 70:
            errors.append(ReportError(
                id="Л-8-freshness",
                code="Л-8",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=0,
                    structural_path="Список литературы"
                ),
                fragment="Список литературы",
                rule=f"Не менее 70% источников должны быть опубликованы в последние {min_year}-{current_year} гг.",
                rule_citation="§4.5, с. 52",
                found_value=f"{recent_percentage:.1f}% ({recent_count}/{total_with_year})",
                expected_value=">= 70%",
                recommendation="Добавьте более свежие источники или замените устаревшие"
            ))
    
    # ============================================
    # Л-9: Формат автора: "Фамилия, И. О."
    # ============================================
    # Русский паттерн: Фамилия, И. О.
    ru_author_pattern = re.compile(r'^[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?,\s[А-ЯЁ]\.\s[А-ЯЁ]\.')
    # Английский паттерн: Surname, I. O.
    en_author_pattern = re.compile(r'^[A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)?,\s[A-Z]\.\s?[A-Z]?\.?')
    
    for idx, ref_text in enumerate(ref_section_paragraphs):
        text_stripped = ref_text.strip()
        if not text_stripped:
            continue
        
        # Проверяем русский формат
        if re.search(r'[А-ЯЁа-яё]', text_stripped):
            if not ru_author_pattern.match(text_stripped):
                # Пробуем понять, есть ли вообще автор в начале
                has_author_like = re.match(r'^[А-ЯЁ][а-яё]+,', text_stripped)
                if has_author_like:
                    # Есть фамилия с запятой, но формат инициалов неверный
                    errors.append(ReportError(
                        id=f"Л-9-author-{idx}",
                        code="Л-9",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=ref_start_para_idx + idx + 1,
                            structural_path=f"Список литературы, источник {idx + 1}"
                        ),
                        fragment=text_stripped[:100],
                        rule="Автор должен быть указан в формате: Фамилия, И. О. (например, «Выготский, Л. С.»)",
                        rule_citation="§4.5, с. 52",
                        found_value=text_stripped.split(',')[0] + ',' if ',' in text_stripped else text_stripped[:30],
                        expected_value="Фамилия, И. О.",
                        recommendation="Исправьте формат автора на «Фамилия, И. О.»"
                    ))
        else:
            # Иностранный источник
            if not en_author_pattern.match(text_stripped):
                has_author_like = re.match(r'^[A-Z][a-zA-Z]+,', text_stripped)
                if has_author_like:
                    errors.append(ReportError(
                        id=f"Л-9-author-en-{idx}",
                        code="Л-9",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=ref_start_para_idx + idx + 1,
                            structural_path=f"Список литературы, источник {idx + 1}"
                        ),
                        fragment=text_stripped[:100],
                        rule="Автор должен быть указан в формате: Surname, I. O.",
                        rule_citation="§4.5, с. 52",
                        found_value=text_stripped.split(',')[0] + ',' if ',' in text_stripped else text_stripped[:30],
                        expected_value="Surname, I. O.",
                        recommendation="Исправьте формат автора на «Surname, I. O.»"
                    ))
    
    # ============================================
    # Л-10: URL-ссылки: дата обращения (дата обращения: ДД.ММ.ГГГГ)
    # ============================================
    url_pattern = re.compile(r'https?://[^\s]+')
    access_date_pattern = re.compile(r'\(дата обращения:\s*\d{2}\.\d{2}\.\d{4}\)', re.IGNORECASE)
    
    for idx, ref_text in enumerate(ref_section_paragraphs):
        if url_pattern.search(ref_text):
            if not access_date_pattern.search(ref_text):
                errors.append(ReportError(
                    id=f"Л-10-url-{idx}",
                    code="Л-10",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_start_para_idx + idx + 1,
                        structural_path=f"Список литературы, источник {idx + 1}"
                    ),
                    fragment=ref_text[:100],
                    rule="Для URL-источников должна быть указана дата обращения в формате (дата обращения: ДД.ММ.ГГГГ)",
                    rule_citation="§4.5, с. 52",
                    found_value="URL без даты обращения",
                    expected_value="(дата обращения: ДД.ММ.ГГГГ)",
                    recommendation="Добавьте дату обращения после URL"
                ))
    
    # ============================================
    # Л-11: Ссылка [N] соответствует источнику в списке литературы
    # ============================================
    # Собираем все номера источников из списка литературы
    valid_source_nums = set()
    for _, num in source_numbers:
        if num is not None:
            valid_source_nums.add(num)
    
    # Находим все ссылки в тексте
    citation_pattern = re.compile(r'\[(\d+)(?:,\s*с\.\s*\d+)?\]')
    
    for para_idx, para in enumerate(doc.paragraphs):
        for match in citation_pattern.finditer(para.text):
            ref_num = int(match.group(1))
            if ref_num not in valid_source_nums:
                errors.append(ReportError(
                    id=f"Л-11-ref-{para_idx}-{ref_num}",
                    code="Л-11",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_idx,
                        structural_path=f"Абзац {para_idx + 1}"
                    ),
                    fragment=match.group(0),
                    rule="Каждая ссылка [N] должна соответствовать источнику №N в списке литературы",
                    rule_citation="§4.3, с. 49",
                    found_value=f"[{ref_num}]",
                    expected_value=f"источник №{ref_num} в списке литературы",
                    recommendation=f"Добавьте источник №{ref_num} в список литературы или исправьте ссылку"
                ))
    
    # ============================================
    # Л-12: Все тире в библиографии — длинные (–)
    # ============================================
    # Ищем дефисы, которые используются как разделители (не внутри слов)
    # Дефис между словами/числами: пробел-дефис-пробел или число-дефис-число
    hyphen_as_dash = re.compile(r'(?<!\w)-(?!\w)|(?<=\d)-(?=\d)|\s-\s')
    proper_dash = '–'  # U+2013
    
    for idx, ref_text in enumerate(ref_section_paragraphs):
        if hyphen_as_dash.search(ref_text):
            # Находим конкретное место с дефисом
            match = hyphen_as_dash.search(ref_text)
            if match:
                context = ref_text[max(0, match.start()-10):match.end()+10]
                errors.append(ReportError(
                    id=f"Л-12-dash-{idx}",
                    code="Л-12",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=ref_start_para_idx + idx + 1,
                        structural_path=f"Список литературы, источник {idx + 1}"
                    ),
                    fragment=context,
                    rule="В списке литературы должны использоваться длинные тире «–» (U+2013), а не дефисы «-»",
                    rule_citation="§4.5, с. 52",
                    found_value="-",
                    expected_value="–",
                    recommendation="Замените дефис «-» на длинное тире «–»"
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
