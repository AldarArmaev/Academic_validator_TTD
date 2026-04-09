# Тестовые фикстуры для валидатора ВКР

## Структура директорий

```
tests/fixtures/
├── __init__.py
├── setup_fixtures.py          # Скрипт создания структуры
├── correct/                   # Эталонный корректный документ
│   └── correct_document.docx
├── formatting/                # Ошибки форматирования (Ф-*)
│   ├── wrong_F_1_font.docx
│   ├── wrong_F_2_spacing.docx
│   ├── wrong_F_3_alignment.docx
│   ├── wrong_F_4_margins.docx
│   ├── wrong_F_5_indent.docx
│   └── wrong_F_6_para_spacing.docx
├── structure/                 # Ошибки структуры (С-*)
│   ├── wrong_C_1_missing_conclusion.docx
│   ├── wrong_C_5_chapter_name.docx
│   ├── wrong_C_7_bold_heading.docx
│   ├── wrong_C_8_heading_alignment.docx
│   └── wrong_C_9_heading_period.docx
├── tables/                    # Ошибки таблиц (Т-*)
│   ├── wrong_T_1_caption_position.docx
│   ├── wrong_T_4_font_size.docx
│   └── wrong_T_12_decimal_point.docx
├── references/                # Ошибки ссылок (Л-*)
│   ├── wrong_L_1_bracket_format.docx
│   ├── wrong_L_3_multiple_order.docx
│   └── wrong_L_7_min_sources.docx
└── typography/                # Типографские ошибки (Н-*)
    ├── wrong_N_2_initials_space.docx
    ├── wrong_N_4_quotes.docx
    └── wrong_N_6_abbreviation.docx
```

## Как использовать

### 1. Создание структуры директорий

Запустите скрипт для создания необходимой иерархии папок:

```bash
cd /workspace
python tests/fixtures/setup_fixtures.py
```

Скрипт выведет список всех ожидаемых файлов с отметками:
- `○` — файл отсутствует (требуется создать вручную)
- `✓` — файл существует

### 2. Создание тестовых файлов

Каждый файл должен содержать **одну конкретную ошибку** согласно своему названию.

#### correct/correct_document.docx
Эталонный документ без ошибок. Должен содержать:
- Шрифт Times New Roman, 14 пт
- Межстрочный интервал 1.5
- Выравнивание по ширине
- Поля: левое 3 см, правое 1 см, верхнее/нижнее 2 см
- Отступ первой строки 1.25 см
- Все обязательные разделы: Введение, Главы, Заключение, Список литературы

#### formatting/wrong_F_1_font.docx
**Ошибка:** шрифт отличается от Times New Roman (например, Arial).

#### formatting/wrong_F_2_spacing.docx
**Ошибка:** неправильный межстрочный интервал (не 1.5).

#### formatting/wrong_F_3_alignment.docx
**Ошибка:** выравнивание не по ширине (например, по левому краю).

#### formatting/wrong_F_4_margins.docx
**Ошибка:** неправильные поля документа.

#### formatting/wrong_F_5_indent.docx
**Ошибка:** неправильный отступ первой строки (не 1.25 см).

#### formatting/wrong_F_6_para_spacing.docx
**Ошибка:** неправильные интервалы до/после абзаца (должны быть 0).

#### structure/wrong_C_1_missing_conclusion.docx
**Ошибка:** отсутствует раздел "Заключение".

#### structure/wrong_C_5_chapter_name.docx
**Ошибка:** заголовок главы без слова "Глава" (например, просто "Теоретические основы").

#### structure/wrong_C_7_bold_heading.docx
**Ошибка:** заголовок не жирным шрифтом.

#### structure/wrong_C_8_heading_alignment.docx
**Ошибка:** неправильное выравнивание заголовка (не по центру).

#### structure/wrong_C_9_heading_period.docx
**Ошибка:** точка в конце заголовка.

#### tables/wrong_T_1_caption_position.docx
**Ошибка:** подпись таблицы снизу (должна быть сверху).

#### tables/wrong_T_4_font_size.docx
**Ошибка:** размер шрифта в таблице меньше 14 пт.

#### tables/wrong_T_12_decimal_point.docx
**Ошибка:** десятичный разделитель — запятая вместо точки (или наоборот).

#### references/wrong_L_1_bracket_format.docx
**Ошибка:** ссылки в квадратных скобках без пробелов (например, `[1]` вместо `[ 1 ]`).

#### references/wrong_L_3_multiple_order.docx
**Ошибка:** множественные ссылки в неправильном порядке (например, `[3, 1]` вместо `[1, 3]`).

#### references/wrong_L_7_min_sources.docx
**Ошибка:** менее 25 источников в списке литературы.

#### typography/wrong_N_2_initials_space.docx
**Ошибка:** нет пробелов между инициалами (например, "И.И.Иванов" вместо "И. И. Иванов").

#### typography/wrong_N_4_quotes.docx
**Ошибка:** используются кавычки "" вместо «».

#### typography/wrong_N_6_abbreviation.docx
**Ошибка:** сокращения оформлены неправильно (например, "г." без пробела перед числом).

## Запуск тестов

После создания файлов запустите тесты:

```bash
# Все тесты
pytest tests/test_format_validation.py -v

# Только тесты с существующими файлами
pytest tests/test_format_validation.py::TestFontFormatting -v

# Конкретный тест
pytest tests/test_format_validation.py::test_F_2_spacing_error -v
```

## Примечание

- Файлы `.docx` должны быть созданы **вручную** пользователем
- Каждый файл должен содержать **только одну ошибку** для чистоты теста
- Для создания файлов используйте Microsoft Word или LibreOffice Writer
- Сохраняйте файлы в формате `.docx` (не `.doc`)
