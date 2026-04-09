# tests/fixtures/setup_fixtures.py
"""
Скрипт для создания структуры директорий тестовых фикстур.

Этот скрипт создаёт необходимую иерархию папок для хранения docx-файлов
с ошибками для каждого требования методички ИГУ факультета психологии.

Файлы .docx должны быть созданы вручную пользователем в соответствующих директориях.
"""

from pathlib import Path


def setup_test_fixtures_dir(base_dir: Path | None = None) -> list[Path]:
    """
    Создаёт структуру директорий для тестовых фикстур.
    
    Args:
        base_dir: Базовая директория для создания структуры. 
                  По умолчанию используется tests/fixtures относительно этого файла.
    
    Returns:
        Список полных путей ко всем файлам (даже если они ещё не существуют).
    """
    if base_dir is None:
        base_dir = Path(__file__).parent
    
    # Определяем структуру директорий и файлов
    fixtures_structure = {
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
    
    created_files = []
    
    for subdir, files in fixtures_structure.items():
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            file_path = dir_path / filename
            created_files.append(file_path)
            
            # Файл не создаём, только выводим путь
            # Пользователь создаст файлы вручную
    
    return created_files


def print_fixture_paths():
    """Выводит полные пути ко всем файлам фикстур."""
    paths = setup_test_fixtures_dir()
    
    print("=" * 70)
    print("Структура директорий тестовых фикстур создана.")
    print("Пути к файлам (файлы должны быть созданы вручную):")
    print("=" * 70)
    
    current_dir = None
    for path in sorted(paths, key=lambda p: str(p)):
        dir_name = path.parent.name
        if dir_name != current_dir:
            current_dir = dir_name
            print(f"\n📁 {current_dir}/")
        
        exists = "✓" if path.exists() else "○"
        print(f"  {exists} {path.name}")
    
    print("\n" + "=" * 70)
    print("Примечание:")
    print("  ✓ — файл существует")
    print("  ○ — файл отсутствует (требуется создать вручную)")
    print("=" * 70)
    
    # Проверка существующих файлов
    existing = sum(1 for p in paths if p.exists())
    missing = len(paths) - existing
    print(f"\nНайдено файлов: {existing}/{len(paths)}")
    print(f"Отсутствует файлов: {missing}")
    
    return paths


if __name__ == "__main__":
    print_fixture_paths()
