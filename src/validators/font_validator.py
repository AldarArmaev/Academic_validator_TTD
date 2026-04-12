# src/validators/font_validator.py
"""Валидатор шрифта основного текста (требование Ф-1)."""

from typing import Any
from docx.document import Document
from src.schemas import ReportError, ErrorLocation


def check_font_formatting(doc: Document, rules: dict[str, Any]) -> list[ReportError]:
    """
    Проверяет шрифт основного текста на соответствие требованию Ф-1:
    Times New Roman, 14 пт.
    
    Проходит по всем абзацам (кроме заголовков), читает run.font.name и run.font.size.
    Сравнивает с rules['font']['family'] и rules['font']['size_pt'] (с допуском 0.5 пт).
    
    Возвращает список ReportError для всех найденных нарушений.
    """
    errors: list[ReportError] = []
    error_counter = 0
    
    expected_font = rules['font']['family']
    expected_size = rules['font']['size_pt']
    tolerance = rules.get('tolerances', {}).get('pt', 0.5)
    
    # Заголовки обычно имеют стиль Heading 1, Heading 2 и т.д.
    heading_styles = {'Heading 1', 'Heading 2', 'Heading 3', 'Heading 4', 'Heading 5', 'Heading 6'}
    
    for para_index, para in enumerate(doc.paragraphs):
        # Пропускаем заголовки
        if para.style and para.style.name in heading_styles:
            continue
        
        # Если абзац пустой, пропускаем
        if not para.text.strip():
            continue
        
        # Проверяем каждый run в абзаце
        for run in para.runs:
            if not run.text.strip():
                continue
            
            font_name = run.font.name
            font_size_pt = run.font.size.pt if run.font.size else None
            
            # Проверка шрифта
            if font_name is not None and font_name != expected_font:
                error_counter += 1
                fragment = run.text[:100]
                errors.append(ReportError(
                    id=f"Ф-1-{error_counter}",
                    code="Ф-1",
                    type="formatting",
                    severity="error",
                    location=ErrorLocation(
                        paragraph_index=para_index,
                        structural_path=f"Абзац {para_index + 1}",
                        chapter=None,
                        page_num=None  # TODO: добавить подсчёт страницы
                    ),
                    fragment=fragment,
                    rule="Шрифт основного текста должен быть Times New Roman, 14 пт",
                    rule_citation="§4.2, с. 47",
                    found_value=f"{font_name}",
                    expected_value=expected_font,
                    recommendation=f"Измените шрифт на {expected_font}"
                ))
            
            # Проверка размера шрифта
            if font_size_pt is not None:
                if abs(font_size_pt - expected_size) > tolerance:
                    error_counter += 1
                    fragment = run.text[:100]
                    errors.append(ReportError(
                        id=f"Ф-1-size-{error_counter}",
                        code="Ф-1",
                        type="formatting",
                        severity="error",
                        location=ErrorLocation(
                            paragraph_index=para_index,
                            structural_path=f"Абзац {para_index + 1}",
                            chapter=None,
                            page_num=None  # TODO: добавить подсчёт страницы
                        ),
                        fragment=fragment,
                        rule="Шрифт основного текста должен быть Times New Roman, 14 пт",
                        rule_citation="§4.2, с. 47",
                        found_value=f"{font_size_pt} пт",
                        expected_value=f"{expected_size} пт",
                        recommendation=f"Измените размер шрифта на {expected_size} пт"
                    ))
    
    return errors
