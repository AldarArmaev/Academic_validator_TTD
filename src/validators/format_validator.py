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
    
    para_index = 0
    for para in doc.paragraphs:
        # Пропускаем заголовки и пустые абзацы
        if para.style and para.style.name in heading_styles:
            continue
        if not para.text.strip():
            continue
        
        pPr = para._p.pPr
        
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
            else:
                # Атрибут отсутствует — это ошибка
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
                    found_value="0",
                    expected_value=str(expected_first_line_indent),
                    recommendation="Установите отступ первой строки 1.25 см"
                ))
        
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
        
        para_index += 1
    
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


def validate_tables(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """Заглушка — будет реализовано в Спринт 2."""
    return []


def validate_references_format(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет форматирование списка литературы.
    
    Л-1: формат ссылок [N] или [N, с. X]
    Л-3: порядок множественных ссылок
    Л-7: минимум 40 источников
    """
    errors: list[ReportError] = []
    
    # Находим раздел списка литературы
    ref_section_paragraphs = []
    in_refs = False
    
    for para in doc.paragraphs:
        if "список литературы" in para.text.lower():
            in_refs = True
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
