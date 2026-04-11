# ВКР Валидатор - Веб-сервис для проверки оформления выпускных квалификационных работ

## Описание

Веб-сервис на базе FastAPI для автоматической проверки оформления ВКР (выпускных квалификационных работ) согласно требованиям методички ИГУ.

## Запуск сервера

```bash
cd /workspace
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

После запуска сервер будет доступен по адресу: http://localhost:8000

## API Endpoints

### GET /
Главная страница сервиса с информацией о версии и доступных endpoints.

### GET /health/
Проверка работоспособности сервиса.

**Ответ:**
```json
{"status": "ok"}
```

### POST /validate/
Загрузка работы на валидацию.

**Параметры:**
- `file` (multipart/form-data): DOCX файл для проверки

**Ответ при успехе (200):**
```json
{
    "doc_id": "uuid-идентификатор",
    "created_at": "2024-01-01T12:00:00Z",
    "session_expires_at": "2024-01-01T13:00:00Z",
    "summary": {
        "total_errors": 10,
        "formatting": 8,
        "style": 2,
        "citations": 0
    },
    "errors": [
        {
            "id": "Ф-1-0",
            "code": "Ф-1",
            "type": "formatting",
            "severity": "error",
            "location": {
                "paragraph_index": 0,
                "structural_path": "Абзац 1",
                "chapter": null
            },
            "fragment": "Текст абзаца...",
            "rule": "Шрифт должен быть Times New Roman, 14 пт",
            "rule_citation": "§4.2, с. 47",
            "found_value": "Arial",
            "expected_value": "Times New Roman",
            "recommendation": "Измените шрифт на Times New Roman"
        }
    ]
}
```

**Ответ при ошибке (400):**
```json
{
    "detail": "Неверный формат файла. Пожалуйста, загрузите файл в формате .docx"
}
```

## Swagger UI

Интерактивная документация доступна по адресу: http://localhost:8000/docs

## Пример использования через curl

```bash
# Проверка работы сервиса
curl http://localhost:8000/health/

# Загрузка файла на валидацию
curl -X POST http://localhost:8000/validate/ \
  -F "file=@path/to/your/work.docx"

# Сохранение результата в файл
curl -X POST http://localhost:8000/validate/ \
  -F "file=@path/to/your/work.docx" > report.json
```

## Пример использования через Python

```python
import requests

# Загрузка файла на валидацию
with open('work.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/validate/',
        files={'file': f}
    )

if response.status_code == 200:
    report = response.json()
    print(f"Найдено ошибок: {report['summary']['total_errors']}")
    for error in report['errors']:
        print(f"- {error['code']}: {error['rule']}")
else:
    print(f"Ошибка: {response.json()['detail']}")
```

## Структура проекта

```
/workspace/
├── src/
│   ├── __init__.py
│   ├── schemas.py              # Pydantic модели данных
│   ├── main.py                 # FastAPI приложение
│   └── validators/
│       ├── __init__.py
│       ├── font_validator.py   # Валидация шрифтов
│       └── format_validator.py # Общая валидация форматирования
├── university_rules.json       # Правила валидации
└── README.md                   # Этот файл
```

## Проверяемые требования

Сервис проверяет следующие требования из методички:

### Структура документа (С-)
- С-1: Обязательные разделы
- С-3: Разделы с новой страницы
- С-5: Формат заголовков глав
- С-6: Нумерация параграфов
- С-7: Заголовки не bold/italic/underline
- С-8: Заголовки по центру без отступа
- С-9: Нет точки в конце заголовка

### Форматирование текста (Ф-)
- Ф-1: Шрифт Times New Roman, 14 пт
- Ф-2: Межстрочный интервал 1.5
- Ф-3: Выравнивание по ширине
- Ф-4: Поля (левое 3см, правое 1см, верхнее/нижнее 2см)
- Ф-5: Отступ первой строки 1.25 см
- Ф-6: Интервалы до/после абзаца 0

### Таблицы и рисунки (Т-)
- Т-1 to Т-12: Форматирование таблиц и рисунков

### Ссылки и литература (Л-)
- Л-1 to Л-12: Формат ссылок и списка литературы

## Требования

- Python 3.12+
- FastAPI 0.116+
- python-docx
- uvicorn
- python-multipart

## Лицензия

Проект создан для образовательных целей.
