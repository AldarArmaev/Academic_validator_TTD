# src/validators/paragraph_validator.py
"""Валидатор форматирования абзацев (требования Ф-2 и др.)."""

from typing import Any
from docx.document import Document
from src.schemas import ReportError, ErrorLocation


def check_paragraph_formatting(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет межстрочный интервал основного текста на соответствие требованию Ф-2:
    Межстрочный интервал — 1,5 (w:line = 420 twips, w:lineRule = "auto").
    
    Использует допуск rules['tolerances']['dxa'].
    Пропускает заголовки (стили Heading1-Heading6).
    
    Возвращает список ReportError для всех найденных нарушений.
    """
    errors: list[ReportError] = []
    error_counter = 0
    
    expected_line_spacing = rules['paragraph']['line_spacing_twips']
    tolerance_dxa = rules.get('tolerances', {}).get('dxa', 20)
    
    # Заголовки обычно имеют стиль Heading 1, Heading 2 и т.д.
    heading_styles = {'Heading 1', 'Heading 2', 'Heading 3', 'Heading 4', 'Heading 5', 'Heading 6'}
    
    for para_index, para in enumerate(doc.paragraphs):
        # Пропускаем заголовки
        if para.style and para.style.name in heading_styles:
            continue
        
        # Если абзац пустой, пропускаем
        if not para.text.strip():
            continue
        
        # Получаем элемент pPr для доступа к spacing
        pPr = para._p.get_or_add_pPr()
        spacing = pPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing')
        
        if spacing is None:
            # Нет элемента spacing — это нарушение
            error_counter += 1
            fragment = para.text[:100]
            errors.append(ReportError(
                id=f"Ф-2-{error_counter}",
                code="Ф-2",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_index,
                    structural_path=f"Абзац {para_index + 1}",
                    chapter=None
                ),
                fragment=fragment,
                rule="Межстрочный интервал основного текста должен быть 1,5 (420 twips)",
                rule_citation="§4.2, с. 47",
                found_value="отсутствует",
                expected_value=f"{expected_line_spacing} twips",
                recommendation="Установите межстрочный интервал 1,5"
            ))
            continue
        
        # Получаем значение line (в twips)
        line_value = spacing.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line')
        line_rule = spacing.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule')
        
        if line_value is None:
            # Нет атрибута line — это нарушение
            error_counter += 1
            fragment = para.text[:100]
            errors.append(ReportError(
                id=f"Ф-2-{error_counter}",
                code="Ф-2",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_index,
                    structural_path=f"Абзац {para_index + 1}",
                    chapter=None
                ),
                fragment=fragment,
                rule="Межстрочный интервал основного текста должен быть 1,5 (420 twips)",
                rule_citation="§4.2, с. 47",
                found_value="атрибут line отсутствует",
                expected_value=f"{expected_line_spacing} twips",
                recommendation="Установите межстрочный интервал 1,5"
            ))
            continue
        
        try:
            actual_line_spacing = int(line_value)
        except ValueError:
            actual_line_spacing = 0
        
        # Проверяем значение с допуском
        if abs(actual_line_spacing - expected_line_spacing) > tolerance_dxa:
            error_counter += 1
            fragment = para.text[:100]
            errors.append(ReportError(
                id=f"Ф-2-{error_counter}",
                code="Ф-2",
                type="formatting",
                severity="error",
                location=ErrorLocation(
                    paragraph_index=para_index,
                    structural_path=f"Абзац {para_index + 1}",
                    chapter=None
                ),
                fragment=fragment,
                rule="Межстрочный интервал основного текста должен быть 1,5 (420 twips)",
                rule_citation="§4.2, с. 47",
                found_value=f"{actual_line_spacing} twips",
                expected_value=f"{expected_line_spacing} twips (±{tolerance_dxa})",
                recommendation="Установите межстрочный интервал 1,5"
            ))
    
    return errors
