# tests/fixtures/setup_fixtures.py
"""
Инструмент для создания структуры папок и проверки наличия тестовых .docx фикстур.

Файлы .docx должны быть созданы вручную пользователем в соответствующих директориях.
Этот скрипт только создаёт папки и проверяет наличие файлов.
"""

from pathlib import Path

import pytest


# Описание каждой фикстуры — что именно нарушено в файле
FIXTURE_DESCRIPTIONS: dict[str, str] = {
    "correct/correct_document.docx": (
        "Эталон. TNR 14пт, интервал 1.5, поля 3/1/2/2 см, отступ 1.25см, "
        "выравнивание по ширине. Разделы: Введение, Глава 1. ..., Заключение, Список литературы."
    ),
    "formatting/wrong_F_1_font.docx": (
        "Нарушение Ф-1: хотя бы один абзац основного текста шрифтом Arial "
        "(не Times New Roman). Всё остальное правильно."
    ),
    "formatting/wrong_F_2_spacing.docx": (
        "Нарушение Ф-2: хотя бы один абзац с одинарным межстрочным интервалом. "
        "В Word: Главная → Интервал → 1.0. Всё остальное правильно."
    ),
    "formatting/wrong_F_3_alignment.docx": (
        "Нарушение Ф-3: хотя бы один абзац с выравниванием по левому краю "
        "(не по ширине). В Word: Главная → Выровнять по левому краю. Всё остальное правильно."
    ),
    "formatting/wrong_F_4_margins.docx": (
        "Нарушение Ф-4: левое поле 2см вместо требуемых 3см. "
        "В Word: Макет → Поля → Настраиваемые поля → Левое: 2 см. Всё остальное правильно."
    ),
    "formatting/wrong_F_5_indent.docx": (
        "Нарушение Ф-5: нет отступа первой строки абзаца (1.25см). "
        "В Word: Абзац → Первая строка: (пусто). Всё остальное правильно."
    ),
    "formatting/wrong_F_6_para_spacing.docx": (
        "Нарушение Ф-6: интервал после абзаца 12пт вместо 0. "
        "В Word: Абзац → Интервал → После: 12 пт. Всё остальное правильно."
    ),
    "structure/wrong_C_1_missing_conclusion.docx": (
        "Нарушение С-1: отсутствует раздел 'Заключение'. "
        "Структура: Введение, Главы, Список литературы — без Заключения."
    ),
    "structure/wrong_C_5_chapter_name.docx": (
        "Нарушение С-5: заголовок главы написан как '1. Название' вместо 'Глава 1. Название'. "
        "Отсутствует слово 'Глава' перед номером."
    ),
    "structure/wrong_C_7_bold_heading.docx": (
        "Нарушение С-7: заголовок раздела выделен жирным шрифтом. "
        "Заголовки должны быть обычным начертанием (не жирным)."
    ),
    "structure/wrong_C_8_heading_alignment.docx": (
        "Нарушение С-8: заголовок раздела выровнен по левому краю вместо центрирования. "
        "В Word: Главная → Выровнять по левому краю."
    ),
    "structure/wrong_C_9_heading_period.docx": (
        "Нарушение С-9: точка в конце заголовка раздела. "
        "Заголовки не должны заканчиваться точкой."
    ),
    "tables/wrong_T_1_caption_position.docx": (
        "Нарушение Т-1: подпись таблицы расположена под таблицей вместо положения над ней. "
        "Правильно: 'Таблица 1 — Название' над таблицей."
    ),
    "tables/wrong_T_4_font_size.docx": (
        "Нарушение Т-4: шрифт внутри таблицы 14пт вместо требуемых 12пт. "
        "Выделите ячейки и установите шрифт 14пт."
    ),
    "tables/wrong_T_12_decimal_point.docx": (
        "Нарушение Т-12: числа в таблице записаны с точкой (2.5) вместо запятой (2,5). "
        "В русском языке десятичный разделитель — запятая."
    ),
    "references/wrong_L_1_bracket_format.docx": (
        "Нарушение Л-1: ссылки оформлены круглыми скобками (1) вместо квадратных [1]. "
        "Ссылки на литературу должны быть в квадратных скобках."
    ),
    "references/wrong_L_3_multiple_order.docx": (
        "Нарушение Л-3: множественная ссылка имеет неправильный порядок номеров. "
        "Например: [12; 4; 25] вместо правильного [4; 12; 25] (по возрастанию)."
    ),
    "references/wrong_L_7_min_sources.docx": (
        "Нарушение Л-7: список литературы содержит менее 40 источников. "
        "Добавьте 20-30 источников вместо требуемых 40+."
    ),
    "typography/wrong_N_2_initials_space.docx": (
        "Нарушение Н-2: инициалы и фамилия написаны без пробелов: 'И.И.Иванов' "
        "вместо правильного 'И. И. Иванов' (пробелы между инициалами и фамилией)."
    ),
    "typography/wrong_N_4_quotes.docx": (
        "Нарушение Н-4: использованы английские кавычки \"кавычки\" вместо «ёлочек». "
        "В русском тексте должны быть кавычки-ёлочки: «кавычки»."
    ),
    "typography/wrong_N_6_abbreviation.docx": (
        "Нарушение Н-6: аббревиатура СПТ использована без расшифровки. "
        "Первое упоминание должно быть: 'Средства Программной Технологии (СПТ)'."
    ),
}


def _get_base_dir(base_dir: Path | None = None) -> Path:
    """Возвращает базовую директорию для фикстур."""
    if base_dir is None:
        base_dir = Path(__file__).parent
    return base_dir


def _get_fixtures_structure() -> dict[str, list[str]]:
    """Возвращает структуру директорий и файлов фикстур."""
    return {
        "correct": [
            "correct_document.docx",
        ],
        "formatting": [
            "wrong_F_1_font.docx",
            "wrong_F_2_spacing.docx",
            "wrong_F_3_alignment.docx",
            "wrong_F_4_margins.docx",
            "wrong_F_5_indent.docx",
            "wrong_F_6_para_spacing.docx",
        ],
        "structure": [
            "wrong_C_1_missing_conclusion.docx",
            "wrong_C_5_chapter_name.docx",
            "wrong_C_7_bold_heading.docx",
            "wrong_C_8_heading_alignment.docx",
            "wrong_C_9_heading_period.docx",
        ],
        "tables": [
            "wrong_T_1_caption_position.docx",
            "wrong_T_4_font_size.docx",
            "wrong_T_12_decimal_point.docx",
        ],
        "references": [
            "wrong_L_1_bracket_format.docx",
            "wrong_L_3_multiple_order.docx",
            "wrong_L_7_min_sources.docx",
        ],
        "typography": [
            "wrong_N_2_initials_space.docx",
            "wrong_N_4_quotes.docx",
            "wrong_N_6_abbreviation.docx",
        ],
    }


def create_fixture_dirs(base_dir: Path | None = None) -> None:
    """
    Создаёт только папки для фикстур. Файлы не трогает.
    
    Args:
        base_dir: Базовая директория для создания структуры.
                  По умолчанию используется директория этого скрипта.
    """
    base_dir = _get_base_dir(base_dir)
    fixtures_structure = _get_fixtures_structure()
    
    for subdir in fixtures_structure.keys():
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)


def check_fixtures(base_dir: Path | None = None) -> dict:
    """
    Проверяет наличие каждого файла фикстуры.
    
    Args:
        base_dir: Базовая директория для проверки.
                  По умолчанию используется директория этого скрипта.
    
    Returns:
        Словарь со статусом проверки:
        {
            "total": int,           # общее количество файлов
            "found": int,           # количество найденных файлов
            "missing": list[str],   # относительные пути отсутствующих файлов
            "ready": bool           # True если все файлы на месте
        }
    """
    base_dir = _get_base_dir(base_dir)
    fixtures_structure = _get_fixtures_structure()
    
    total = 0
    found = 0
    missing: list[str] = []
    
    for subdir, files in fixtures_structure.items():
        for filename in files:
            total += 1
            rel_path = f"{subdir}/{filename}"
            file_path = base_dir / subdir / filename
            
            if file_path.exists():
                found += 1
            else:
                missing.append(rel_path)
    
    return {
        "total": total,
        "found": found,
        "missing": missing,
        "ready": len(missing) == 0,
    }


def print_status(base_dir: Path | None = None) -> None:
    """
    Красиво выводит статус каждого файла фикстуры в консоль.
    
    Формат вывода:
      ✓  correct/correct_document.docx
      ○  formatting/wrong_F_1_font.docx   ← ОТСУТСТВУЕТ
    
    В конце выводится итог:
      Готово: 3/20 файлов
      Отсутствуют (17):
        formatting/wrong_F_1_font.docx
        ...
    
    Args:
        base_dir: Базовая директория для проверки.
                  По умолчанию используется директория этого скрипта.
    """
    base_dir = _get_base_dir(base_dir)
    fixtures_structure = _get_fixtures_structure()
    status = check_fixtures(base_dir)
    
    print("=" * 70)
    print("Статус тестовых фикстур")
    print("=" * 70)
    
    for subdir, files in fixtures_structure.items():
        print(f"\n📁 {subdir}/")
        for filename in files:
            rel_path = f"{subdir}/{filename}"
            file_path = base_dir / subdir / filename
            
            if file_path.exists():
                print(f"  ✓  {rel_path}")
            else:
                print(f"  ○  {rel_path}   ← ОТСУТСТВУЕТ")
    
    print("\n" + "=" * 70)
    print(f"Готово: {status['found']}/{status['total']} файлов")
    
    if status["missing"]:
        print(f"Отсутствуют ({len(status['missing'])}):")
        for missing_path in status["missing"]:
            print(f"  {missing_path}")
    
    print("=" * 70)
    
    # Вывод описаний для отсутствующих файлов
    if status["missing"]:
        print("\nОписание отсутствующих файлов:")
        print("-" * 70)
        for missing_path in status["missing"]:
            description = FIXTURE_DESCRIPTIONS.get(missing_path, "Нет описания")
            print(f"\n{missing_path}:")
            print(f"  {description}")


@pytest.fixture(scope="session", autouse=True)
def ensure_fixtures_exist():
    """
    Проверяет наличие фикстур перед запуском тестов.
    
    Если файлы отсутствуют — пропускает тесты с понятным сообщением.
    """
    status = check_fixtures()
    if not status["ready"]:
        missing_str = "\n  ".join(status["missing"])
        pytest.skip(
            f"Отсутствуют тестовые фикстуры ({status['found']}/{status['total']}).\n"
            f"Создайте файлы вручную в папке tests/fixtures/:\n  {missing_str}\n"
            f"Описание каждого файла: python tests/fixtures/setup_fixtures.py"
        )


if __name__ == "__main__":
    create_fixture_dirs()
    print_status()
