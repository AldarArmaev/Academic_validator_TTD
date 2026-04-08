#!/usr/bin/env python3
"""
CLI для проверки документов ВКР на соответствие требованиям нормоконтроля.

Использование:
    python -m src.main path/to/document.docx
    python -m src.main --help
"""

import argparse
import sys
from pathlib import Path

from src.contour_a.document_loader import load_document


def main():
    parser = argparse.ArgumentParser(
        description="Проверка документов ВКР на соответствие требованиям нормоконтроля"
    )
    parser.add_argument(
        "file",
        type=str,
        help="Путь к DOCX файлу для проверки"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробный вывод информации"
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Ошибка: Файл не найден: {file_path}", file=sys.stderr)
        sys.exit(1)
    
    if file_path.suffix.lower() not in ['.docx', '.doc']:
        print(f"Ошибка: Неподдерживаемый формат файла: {file_path.suffix}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Загрузка и парсинг документа
        print(f"Загрузка документа: {file_path.name}")
        content = load_document(file_path)
        
        # Вывод базовой статистики
        print("\n=== Статистика документа ===")
        print(f"Страниц (приблизительно): {content.total_pages}")
        print(f"Абзацев: {len(content.paragraphs)}")
        print(f"Заголовков: {len(content.headings)}")
        print(f"Таблиц: {len(content.tables)}")
        print(f"Рисунков: {len(content.figures)}")
        print(f"Формул: {len(content.formulas)}")
        print(f"Ссылок: {len(content.references)}")
        print(f"Записей в библиографии: {len(content.bibliography)}")
        print(f"Приложений: {len(content.appendices)}")
        
        # Сводная статистика
        print(f"\nСимволов (без пробелов): {content.char_count_no_spaces}")
        print(f"Символов (с пробелами): {content.char_count_with_spaces}")
        print(f"Слов: {content.word_count}")
        
        # Подробная информация о заголовках
        if args.verbose and content.headings:
            print("\n=== Заголовки ===")
            for heading in content.headings:
                indent = "  " * (heading.level - 1)
                numbering = f"{heading.numbering} " if heading.numbering else ""
                print(f"{indent}{heading.level}. {numbering}{heading.text[:60]}{'...' if len(heading.text) > 60 else ''}")
        
        # Информация о полях страницы
        if 'margins' in content.metadata:
            margins = content.metadata['margins']
            print("\n=== Поля страницы (см) ===")
            print(f"Левое: {margins.get('left_cm', 'N/A')}")
            print(f"Правое: {margins.get('right_cm', 'N/A')}")
            print(f"Верхнее: {margins.get('top_cm', 'N/A')}")
            print(f"Нижнее: {margins.get('bottom_cm', 'N/A')}")
        
        print("\n✓ Документ успешно загружен и распарсен")
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка парсинга: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
