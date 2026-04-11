# ВКР Валидатор — Веб-сервис

Веб-сервис для проверки оформления выпускных квалификационных работ (ВКР) на соответствие требованиям методички ИГУ.

## Запуск сервера

```bash
cd /workspace
uvicorn src.web.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /
Главная страница с информацией о сервисе.

### GET /health
Проверка работоспособности сервиса.

**Ответ:**
```json
{"status": "ok", "service": "ВКР Валидатор"}
```

### POST /validate
Загрузка файла ВКР (.docx) для валидации.

**Параметры:**
- `file` (multipart/form-data): DOCX файл с работой

**Ответ:** ValidationReport со списком ошибок

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/validate \
  -F "file=@work.docx"
```

**Пример ответа:**
```json
{
  "doc_id": "6bccac9e-7cd3-4277-a9bb-83201c348bf8",
  "created_at": "2026-04-11T06:46:52.187644Z",
  "session_expires_at": "2026-04-11T07:46:52.187650Z",
  "summary": {
    "total_errors": 110,
    "formatting": 85,
    "style": 25,
    "citations": 0
  },
  "errors": [
    {
      "id": "Ф-3-27",
      "code": "Ф-3",
      "type": "formatting",
      "severity": "error",
      "location": {
        "paragraph_index": 27,
        "structural_path": "Абзац 28",
        "chapter": null
      },
      "fragment": "2.7. Высокоуровневые требования",
      "rule": "Текст должен быть выровнен по ширине",
      "rule_citation": "§4.2, с. 47",
      "found_value": "center",
      "expected_value": "both",
      "recommendation": "Установите выравнивание по ширине"
    }
  ]
}
```

### GET /docs
Swagger UI документация (интерактивная).

## Структура ответа

### ValidationReport
- `doc_id`: Уникальный идентификатор отчёта
- `created_at`: Дата и время создания отчёта
- `session_expires_at`: Время истечения сессии (1 час)
- `summary`: Статистика по ошибкам
  - `total_errors`: Общее количество ошибок
  - `formatting`: Ошибки форматирования
  - `style`: Стилистические ошибки
  - `citations`: Проблемы с цитированием
- `errors`: Список всех найденных ошибок

### ReportError
- `id`: Уникальный ID ошибки внутри отчёта
- `code`: Код требования ("Ф-1", "С-5", "Л-7" и т.д.)
- `type`: Тип нарушения ("formatting", "style", "citation_check")
- `severity`: Серьёзность ("error", "warning", "info")
- `location`: Местоположение ошибки
  - `paragraph_index`: Индекс абзаца
  - `structural_path`: Путь в структуре документа
  - `chapter`: Глава (если применимо)
- `fragment`: Фрагмент текста (до 100 символов)
- `rule`: Формулировка требования
- `rule_citation`: Цитата из методички
- `found_value`: Что найдено в документе
- `expected_value`: Что ожидалось
- `recommendation`: Инструкция для исправления

## Проверяемые требования

### Контур А (реализован)

#### Структура документа (С-*)
- С-1: Обязательные разделы
- С-3: Разделы с новой страницы
- С-5: Формат заголовков глав
- С-6: Нумерация параграфов

#### Форматирование (Ф-*)
- Ф-1: Шрифт Times New Roman, 14 пт
- Ф-2: Межстрочный интервал 1.5
- Ф-3: Выравнивание по ширине
- Ф-4: Поля документа
- Ф-5: Отступ первой строки 1.25 см
- Ф-6: Интервалы до/после абзаца

#### Таблицы и рисунки (Т-*)
- Т-1—Т-12: Форматирование таблиц и рисунков

#### Списки литературы (Л-*)
- Л-1—Л-12: Оформление ссылок и библиографии

## Технологии

- **FastAPI**: Современный веб-фреймворк
- **python-docx**: Работа с DOCX файлами
- **Pydantic**: Валидация данных
- **Swagger UI**: Интерактивная документация

## Пример использования в коде

```python
import requests

# Загрузка файла на валидацию
with open('work.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/validate',
        files={'file': f}
    )

report = response.json()
print(f"Найдено ошибок: {report['summary']['total_errors']}")

for error in report['errors'][:5]:
    print(f"{error['code']}: {error['rule']}")
    print(f"  Рекомендация: {error['recommendation']}")
```
