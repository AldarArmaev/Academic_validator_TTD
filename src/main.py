# src/main.py
"""Веб-сервис для валидации ВКР."""

import json
import tempfile
from pathlib import Path
from datetime import timezone

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from docx import Document

from src.schemas import ValidationReport
from src.validators.format_validator import validate_format


app = FastAPI(
    title="ВКР Валидатор",
    description="Сервис для проверки оформления выпускных квалификационных работ",
    version="1.0.0"
)


def load_rules() -> dict:
    """Загружает правила валидации из university_rules.json."""
    rules_path = Path(__file__).parent.parent / "university_rules.json"
    if not rules_path.exists():
        # Правила по умолчанию если файл не найден
        return {
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
            "margins_cm": {
                "left": 3.0,
                "right": 1.0,
                "top": 2.0,
                "bottom": 2.0
            },
            "volume": {
                "total_chars_min": 90000,
                "total_chars_max": 108000,
                "theory_chapter_chars_min": 27000,
                "theory_chapter_chars_max": 36000,
                "empirical_chapter_chars_min": 45000,
                "empirical_chapter_chars_max": 54000
            },
            "references": {
                "min_sources": 40,
                "max_years_old": 10,
                "inline_pattern": r"\[\d+(?:,\s*с\.\s*\d+)?\]",
                "multi_ref_pattern": r"\[\d+(?:;\s*\d+)+\]",
                "repeated_ref_pattern": r"\[там же(?:,\s*с\.\s*\d+)?\]"
            },
            "table_font": {
                "size_pt_normal": 12,
                "size_pt_min": 11,
                "line_spacing_twips": 240
            },
            "required_sections": [
                "введение",
                "заключение",
                "список литературы"
            ],
            "chapter_heading_pattern": "^Глава \\d+\\.\\s.+",
            "paragraph_heading_pattern": "^\\d+\\.\\d+(\\.\\d+)?\\s.+",
            "stop_words_style": ["я ", "мне ", "мой ", "моя "],
            "stop_words_colloquial": ["короче", "вообще-то", "на самом деле", "типа", "как бы"],
            "tolerances": {
                "dxa": 20,
                "pt": 0.5
            }
        }
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.get("/")
async def root():
    """Главная страница сервиса."""
    return {
        "message": "ВКР Валидатор - сервис для проверки оформления выпускных квалификационных работ",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/validate/",
            "docs": "/docs"
        }
    }


@app.post("/validate/")
async def validate_work(file: UploadFile = File(...)):
    """
    Загрузка работы на валидацию.
    
    Принимает DOCX файл и возвращает отчёт об ошибках форматирования.
    """
    # Проверка расширения файла
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Неверный формат файла. Пожалуйста, загрузите файл в формате .docx"
        )
    
    try:
        # Читаем содержимое файла
        content = await file.read()
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Проверяем что это действительно DOCX файл
            try:
                doc = Document(tmp_path)
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка чтения файла: {str(e)}. Убедитесь что файл является корректным DOCX документом."
                )
            
            # Загружаем правила
            rules = load_rules()
            
            # Выполняем валидацию
            report = validate_format(tmp_path, rules)
            
            # Возвращаем результат
            return JSONResponse(
                content=report.model_dump(mode='json'),
                status_code=200
            )
        
        finally:
            # Удаляем временный файл
            Path(tmp_path).unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.get("/health/")
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
