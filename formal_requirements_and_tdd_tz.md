# Формальные требования из методички и ТЗ через TDD

---

## Часть 1. Формальные требования из методички, реализуемые в системе «Интеллектуальный Нормоконтролёр»

> [!NOTE]
> Источник: «Подготовка, оформление и защита ВКР» (ИГУ, факультет психологии, 2021).
> Ниже выписаны **только** те требования, которые формализуемы и могут быть проверены программно.

---

### 1. Структура документа (Контур А — детерминированный валидатор)

| № | Требование | Раздел методички | Способ проверки |
|---|-----------|-----------------|----------------|
| С-1 | Обязательные разделы: Титульный лист → Содержание → Введение → Глава 1 (≥ 2 параграфа + выводы) → Глава 2 (2–3 параграфа + выводы) → Заключение → Список литературы | §1, с. 7 | Парсинг `w:pStyle` (Heading1/Heading2), проверка наличия разделов по шаблону |
| С-2 | Приложения — опциональны, но при наличии нумеруются арабскими цифрами и имеют ссылки из текста | §3.8, с. 44 | Поиск паттерна «Приложение N» + проверка наличия `(прил. N)` в тексте |
| С-3 | Каждый новый раздел (Содержание, Введение, Глава, Заключение, Список литературы, Приложения) — с новой страницы | §4.2, с. 47 | Проверка наличия `page break` перед разделом |
| С-4 | Параграфы **не** начинаются с новой страницы; отделяются доп. междустрочным интервалом 1,5 | §4.2, с. 47 | Проверка отсутствия `page break` перед параграфами |
| С-5 | Нумерация глав: арабские цифры со словом «Глава» (напр.: «Глава 1. Название») | §4.2, с. 47 | Regex на заголовки Heading1: `^Глава \d+\.\s` |
| С-6 | Нумерация параграфов — многоуровневый список: `1.1.`, `1.1.1.` и т. д. | §4.2, с. 47 | Regex на заголовки Heading2/Heading3 |
| С-7 | Названия разделов и параграфов **не** выделяются (не bold/italic) и **не** подчёркиваются | §4.2, с. 47 | Проверка XML-атрибутов шрифта заголовков |
| С-8 | Все названия выравниваются по центру, без абзацного отступа | §4.2, с. 47 | Проверка `w:jc = "center"` + `w:ind @firstLine = 0` в заголовках |
| С-9 | Точки в конце названий глав и параграфов **не** ставятся | §4.2, с. 47 | Regex: заголовок не заканчивается на `.` |
| С-10 | Внутри параграфов — никаких подзаголовков | §4.2, с. 47 | Проверка отсутствия Heading-стилей внутри секций параграфов |

---

### 2. Форматирование текста (Контур А)

| № | Требование | Значение | Раздел |
|---|-----------|---------|--------|
| Ф-1 | Шрифт основного текста | Times New Roman, 14 пт | §4.2, с. 47 |
| Ф-2 | Межстрочный интервал | 1,5 (полуторный) | §4.2, с. 47 |
| Ф-3 | Выравнивание основного текста | по ширине | §4.2, с. 47 |
| Ф-4 | Поля | лев. 3,0 см; прав. 1,0 см; верх. 2,0 см; ниж. 2,0 см | §4.2, с. 47 |
| Ф-5 | Абзацный отступ (красная строка) | 1,25 см | §4.2, с. 47 |
| Ф-6 | Интервалы перед и после абзаца | 0,0 пт | §4.2, с. 47 |
| Ф-7 | Нумерация страниц: положение | правый нижний угол | §4.2, с. 47 |
| Ф-8 | Нумерация страниц: шрифт | Times New Roman, 12 пт | §4.2, с. 47 |
| Ф-9 | Нумерация начинается с Введения (с. 3) | Титульный лист и содержание без номеров | §4.2, с. 47 |
| Ф-10 | На страницах приложений нет номеров (кроме первой стр. прил. 1) | Без нумерации | §4.2, с. 47 |
| Ф-11 | Объём ВКР | 50—60 с. (без приложений) | §4.1, с. 46 |
| Ф-12 | Теоретическая глава | 15—20 с. | §3.4, с. 23 |
| Ф-13 | Эмпирическая глава | 25—30 с. | §3.5, с. 30 |

---

### 3. Таблицы и рисунки (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| Т-1 | Слово «Таблица» + номер (без знака №) — **над** таблицей, выравнивание по правому краю | §4.4, с. 50 |
| Т-2 | Название таблицы — ниже, по центру, без абзацного отступа, начинается с прописной | §4.4, с. 50 |
| Т-3 | Точки после номера и названия таблицы **не** ставятся | §4.4, с. 50 |
| Т-4 | Шрифт внутри таблицы: Times New Roman, 12 пт (допустимо 11 пт), межстрочный 1 (одинарный) | §4.4, с. 51 |
| Т-5 | Автоподбор таблицы «по ширине окна»; выравнивание в ячейках — по центру | §4.4, с. 51 |
| Т-6 | Нумерация таблиц и рисунков — **сквозная** для всей работы, включая приложения | §4.4, с. 50 |
| Т-7 | Подпись рисунка: `Рис. N. Название` — **под** рисунком, по центру, без абзацного отступа | §4.4, с. 52 |
| Т-8 | Название рисунка начинается с прописной; точка после «Рис. N.» ставится, после названия — нет | §4.4, с. 52 |
| Т-9 | Условные обозначения рисунка — между рисунком и подписью, 12 пт, по ширине, отступ 1,25 | §4.4, с. 52 |
| Т-10 | Междустрочный интервал в названиях рисунков — 1 (одинарный), в названиях таблиц — 1,5 (полуторный) | §4.4, с. 51-52 |
| Т-11 | Запрет дублирования: одни и те же данные **не** должны быть одновременно в таблице и рисунке | §3.5, с. 38 |
| Т-12 | Дробные числа — с запятой, не с точкой (напр.: 2,5, а не 2.5) | §4.4, с. 51 |

---

### 4. Ссылки и список литературы (Контуры А + Б)

| № | Требование | Раздел | Контур |
|---|-----------|--------|--------|
| Л-1 | Формат ссылки: `[N]`; страница при цитировании: `[N, с. X]` | §4.3, с. 49 | А |
| Л-2 | Повторная ссылка: `[там же, с. X]` | §4.3, с. 49 | А |
| Л-3 | Несколько источников в одной ссылке: `[4; 12; 25]` — в арифметическом порядке, через `;` | §4.3, с. 49 | А |
| Л-4 | Список литературы: в алфавитном порядке, сначала русские, затем иностранные | §4.5, с. 52 | А |
| Л-5 | Нумерация источников — сплошная и автоматическая | §4.5, с. 53 | А |
| Л-6 | В список **не** включаются учебники и учебные пособия | §3.7, с. 44 | Б (LLM) |
| Л-7 | Не менее 40 источников | §3.7, с. 44 | А |
| Л-8 | Основная часть источников — последние 10 лет | §3.7, с. 44 | А |
| Л-9 | Формат заголовка библ. описания: фамилия через запятую от инициалов (`Выготский, Л. С.`) | §4.5, с. 54 | А |
| Л-10 | URL-ссылки: включать дату обращения в формате `(дата обращения: ДД.ММ.ГГГГ)` | §4.5, с. 58 | А |
| Л-11 | RAG-верификация: каждая ссылка `[N]` должна соответствовать реально существующему источнику в списке | §4.3 | Б |
| Л-12 | Все тире в библиографии — длинные (–) | §4.5, с. 58 | А |

---

### 5. Введение — методологические нормативы (Контур Б — LLM-анализ)

| № | Требование | Раздел |
|---|-----------|--------|
| В-1 | Введение содержит **все** 10 методологических нормативов в строгом порядке: актуальность → цель → объект → предмет → гипотеза → задачи → теоретико-методологическая основа → характеристика выборки → методы и методики → структура и объём ВКР | §3.3, с. 12-13 |
| В-2 | Ключевые слова нормативов выделены (bold/italic/underline) | §4.2, с. 47-48 |
| В-3 | Введение **не** должно содержать фраз планирования будущего времени:  «мы планируем», «мы будем», «мы намерены» | §3.3, с. 13 |
| В-4 | Задач не более 4—5 | §3.3, с. 17 |
| В-5 | Ни одна задача не дублирует цель | §3.3, с. 17 |
| В-6 | Предмет ВКР = тема ВКР (дословно или почти) | §3.3, с. 16 |

---

### 6. Научный стиль и оформление текста (Контур Б)

| № | Требование | Раздел |
|---|-----------|--------|
| Н-1 | Запрет местоимений первого лица ед.ч.: «я», «мне»; для «мы/нам» — рекомендация пассивного залога | §3.3.1 ТЗ |
| Н-2 | Между инициалами и перед фамилиями — пробелы (`И. И. Иванов`) | §4.2, с. 48 |
| Н-3 | Сокращения вроде `т. д.`, `т. п.` — после разделительной точки пробел | §4.2, с. 48 |
| Н-4 | Кавычки — уголки `« »`, кавычки в кавычках — лапки `" "` | §4.2, с. 48 |
| Н-5 | Сложносочинённые слова — дефис (-); между датами/числами — тире (–) | §4.2, с. 48 |
| Н-6 | Аббревиатуры: при первом использовании — полностью + аббревиатура в скобках | §4.1, с. 46 |
| Н-7 | Оригинальность текста — не менее 60% | §2, с. 11 |
| Н-8 | Списки — автоматическая нумерация; единый тип маркера для маркированных списков | §4.2, с. 48 |

---

### 7. Формулы (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| Фр-1 | Формулы набираются в редакторе формул, размещаются в отдельной строке | §4.2, с. 48 |
| Фр-2 | Идентификатор формулы в скобках: `(1.1)`, `(2.3)` | §4.2 + ТЗ |

---

### 8. Содержание (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| Со-1 | Содержание отражает **все** заголовки разделов с указанием номера страницы | §3.2, с. 12 |
| Со-2 | Рекомендовано выполнять в виде таблицы без границ | §3.2, с. 12 |
| Со-3 | Нумерация страниц в содержании должна совпадать с реальными номерами страниц | §3.2, с. 12 |

---

### 9. Приложения (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| П-1 | Каждое приложение — с новой страницы | §4.6, с. 59 |
| П-2 | «Приложение N» — в правом верхнем углу, строчными с первой прописной | §4.6, с. 59 |
| П-3 | Название приложения — на отдельной строке по центру, без абзацного отступа, без точки | §4.6, с. 59 |
| П-4 | Нумерация арабскими цифрами в порядке ссылок | §4.6, с. 59 |

---

## Часть 2. Техническое задание в методологии TDD (Test-Driven Development)

> [!IMPORTANT]
> Каждый модуль описывается по схеме: **TEST → CODE → REFACTOR**.
> Тесты пишутся **до** реализации. Функциональность считается готовой только при прохождении всех тестов.

---

### Модуль 1. Препроцессинг и приватность (Privacy Shield)

#### 1.1. RED: Тесты (пишутся первыми)

**`test_anonymization.py`**

```python
# TEST-1: NER находит и заменяет ФИО
def test_anonymize_fio():
    text = "Студент Иванов Иван Иванович выполнил работу"
    result = anonymize(text)
    assert "[STUDENT_NAME]" in result
    assert "Иванов" not in result

# TEST-2: NER заменяет названия кафедр
def test_anonymize_department():
    text = "Кафедра общей психологии ИГУ"
    result = anonymize(text)
    assert "[DEPARTMENT]" in result

# TEST-3: Email анонимизируется
def test_anonymize_email():
    text = "email: student@isu.ru"
    result = anonymize(text)
    assert "[EMAIL]" in result
    assert "student@isu.ru" not in result

# TEST-4: Телефон анонимизируется
def test_anonymize_phone():
    text = "тел. +7 (3952) 24-18-70"
    result = anonymize(text)
    assert "[PHONE]" in result

# TEST-5: анонимизация выполняется ДО отправки в LLM
def test_anonymize_before_llm(mock_llm_api):
    pipeline = Pipeline(docx_path="test.docx")
    pipeline.run()
    # Все вызовы LLM не содержат персональных данных
    for call in mock_llm_api.calls:
        assert "[STUDENT_NAME]" not in call.text or "Иванов" not in call.text
```

**`test_parsing.py`**

```python
# TEST-6: DOCX конвертируется в Markdown с иерархией
def test_docx_to_markdown():
    md = parse_docx("fixtures/valid_vkr.docx")
    assert "# Глава 1." in md
    assert "## 1.1." in md

# TEST-7: Детектирование глав по w:pStyle
def test_detect_chapters():
    chapters = detect_chapters("fixtures/valid_vkr.docx")
    assert len(chapters) >= 2
    assert chapters[0].style == "Heading1"

# TEST-8: Формулы OMML конвертируются в LaTeX
def test_formula_conversion():
    formulas = extract_formulas("fixtures/vkr_with_formulas.docx")
    for f in formulas:
        assert f.latex is not None or f.has_caption
```

#### 1.2. GREEN: Реализация

- Реализовать `anonymize()` на базе Natasha NER
- Реализовать `parse_docx()` с python-docx → Markdown
- Реализовать `detect_chapters()` по `w:pStyle`
- Реализовать `extract_formulas()` с mathml2latex

#### 1.3. REFACTOR

- Вынести паттерны токенов в конфиг
- Оптимизировать NER-пайплайн

---

### Модуль 2. Контур А — Проверка оформления

#### 2.1. RED: Тесты

**`test_format_validation.py`**

```python
# === Шрифт и интервалы ===

# TEST-9: Основной шрифт — Times New Roman 14пт
def test_main_font():
    errors = validate_format("fixtures/wrong_font.docx")
    assert any(e.code == "Ф-1" and "Times New Roman" in e.message for e in errors)

# TEST-10: Межстрочный интервал = 1.5
def test_line_spacing():
    errors = validate_format("fixtures/wrong_spacing.docx")
    assert any(e.code == "Ф-2" for e in errors)

# TEST-11: Выравнивание по ширине
def test_justify_alignment():
    errors = validate_format("fixtures/wrong_alignment.docx")
    assert any(e.code == "Ф-3" for e in errors)

# TEST-12: Поля документа
def test_margins():
    errors = validate_format("fixtures/wrong_margins.docx")
    assert any(e.code == "Ф-4" for e in errors)

# TEST-13: Абзацный отступ 1.25 см
def test_paragraph_indent():
    errors = validate_format("fixtures/wrong_indent.docx")
    assert any(e.code == "Ф-5" for e in errors)

# TEST-14: Интервалы перед/после абзаца = 0
def test_paragraph_spacing():
    errors = validate_format("fixtures/wrong_para_spacing.docx")
    assert any(e.code == "Ф-6" for e in errors)

# === Структура ===

# TEST-15: Все обязательные разделы присутствуют
def test_required_sections():
    errors = validate_structure("fixtures/missing_conclusion.docx")
    assert any(e.code == "С-1" and "Заключение" in e.message for e in errors)

# TEST-16: Каждый новый раздел с новой страницы
def test_sections_new_page():
    errors = validate_structure("fixtures/no_page_break.docx")
    assert any(e.code == "С-3" for e in errors)

# TEST-17: Заголовки глав: "Глава N. Название"
def test_chapter_naming():
    errors = validate_structure("fixtures/wrong_chapter_name.docx")
    assert any(e.code == "С-5" for e in errors)

# TEST-18: Заголовки не выделены bold/italic/underline
def test_headings_not_decorated():
    errors = validate_format("fixtures/bold_heading.docx")
    assert any(e.code == "С-7" for e in errors)

# TEST-19: Заголовки по центру без отступа
def test_heading_alignment():
    errors = validate_format("fixtures/left_heading.docx")
    assert any(e.code == "С-8" for e in errors)

# TEST-20: Нет точки в конце заголовка
def test_heading_no_period():
    errors = validate_format("fixtures/heading_with_period.docx")
    assert any(e.code == "С-9" for e in errors)

# === Нумерация страниц ===

# TEST-21: Нумерация в правом нижнем углу, 12 пт
def test_page_numbering():
    errors = validate_format("fixtures/wrong_page_numbers.docx")
    assert any(e.code == "Ф-7" for e in errors)

# TEST-22: Нумерация начинается с с. 3 (Введение)
def test_page_numbering_start():
    errors = validate_format("fixtures/numbered_title.docx")
    assert any(e.code == "Ф-9" for e in errors)
```

**`test_tables_figures.py`**

```python
# TEST-23: Подпись таблицы — над таблицей, по правому краю
def test_table_caption_position():
    errors = validate_tables("fixtures/wrong_table_caption.docx")
    assert any(e.code == "Т-1" for e in errors)

# TEST-24: Название таблицы — по центру, без отступа
def test_table_title_alignment():
    errors = validate_tables("fixtures/wrong_table_title.docx")
    assert any(e.code == "Т-2" for e in errors)

# TEST-25: Шрифт внутри таблицы — 12пт, одинарный
def test_table_inner_font():
    errors = validate_tables("fixtures/wrong_table_font.docx")
    assert any(e.code == "Т-4" for e in errors)

# TEST-26: Сквозная нумерация таблиц и рисунков
def test_sequential_numbering():
    errors = validate_tables("fixtures/broken_numbering.docx")
    assert any(e.code == "Т-6" for e in errors)

# TEST-27: Подпись рисунка — под рисунком: "Рис. N. Название"
def test_figure_caption():
    errors = validate_figures("fixtures/wrong_figure_caption.docx")
    assert any(e.code == "Т-7" for e in errors)

# TEST-28: Дробные числа с запятой
def test_decimal_comma():
    errors = validate_tables("fixtures/table_with_dots.docx")
    assert any(e.code == "Т-12" for e in errors)
```

**`test_references.py`**

```python
# TEST-29: Формат ссылки [N] или [N, с. X]
def test_reference_format():
    errors = validate_references("fixtures/wrong_ref_format.docx")
    assert any(e.code == "Л-1" for e in errors)

# TEST-30: Несколько ссылок в арифметическом порядке [4; 12; 25]
def test_multiple_refs_order():
    errors = validate_references("fixtures/unordered_refs.docx")
    assert any(e.code == "Л-3" for e in errors)

# TEST-31: Список литературы — алфавитный порядок
def test_bibliography_order():
    errors = validate_references("fixtures/unordered_bibliography.docx")
    assert any(e.code == "Л-4" for e in errors)

# TEST-32: Не менее 40 источников
def test_min_sources():
    errors = validate_references("fixtures/few_sources.docx")
    assert any(e.code == "Л-7" for e in errors)

# TEST-33: Формат заголовка: "Фамилия, И. О."
def test_author_format():
    errors = validate_references("fixtures/wrong_author_format.docx")
    assert any(e.code == "Л-9" for e in errors)

# TEST-34: URL с датой обращения
def test_url_access_date():
    errors = validate_references("fixtures/url_no_date.docx")
    assert any(e.code == "Л-10" for e in errors)

# TEST-35: Все тире в библиографии — длинные
def test_bibliography_dashes():
    errors = validate_references("fixtures/short_dashes.docx")
    assert any(e.code == "Л-12" for e in errors)
```

**`test_volume.py`**

```python
# TEST-36: Объём ВКР 50–60 с.
def test_total_pages():
    errors = validate_volume("fixtures/short_vkr.docx")
    assert any(e.code == "Ф-11" for e in errors)

# TEST-37: Теоретическая глава 15–20 с.
def test_theoretical_chapter_volume():
    errors = validate_volume("fixtures/short_theory.docx")
    assert any(e.code == "Ф-12" for e in errors)

# TEST-38: Эмпирическая глава 25–30 с.
def test_empirical_chapter_volume():
    errors = validate_volume("fixtures/short_empirical.docx")
    assert any(e.code == "Ф-13" for e in errors)
```

**`test_formulas.py`**

```python
# TEST-39: Формула в отдельной строке
def test_formula_separate_line():
    errors = validate_formulas("fixtures/inline_formula.docx")
    assert any(e.code == "Фр-1" for e in errors)

# TEST-40: Формула имеет идентификатор (1.1)
def test_formula_identifier():
    errors = validate_formulas("fixtures/formula_no_id.docx")
    assert any(e.code == "Фр-2" for e in errors)
```

**`test_appendices.py`**

```python
# TEST-41: Каждое приложение с новой страницы
def test_appendix_new_page():
    errors = validate_appendices("fixtures/appendix_no_break.docx")
    assert any(e.code == "П-1" for e in errors)

# TEST-42: "Приложение N" в правом верхнем углу
def test_appendix_header():
    errors = validate_appendices("fixtures/wrong_appendix_header.docx")
    assert any(e.code == "П-2" for e in errors)
```

**`test_typography.py`**

```python
# TEST-43: Пробел между инициалами "И. И. Иванов"
def test_initials_space():
    errors = validate_typography("fixtures/no_space_initials.docx")
    assert any(e.code == "Н-2" for e in errors)

# TEST-44: Кавычки-уголки «»
def test_angle_quotes():
    errors = validate_typography("fixtures/wrong_quotes.docx")
    assert any(e.code == "Н-4" for e in errors)

# TEST-45: Дефис vs тире
def test_dash_vs_hyphen():
    errors = validate_typography("fixtures/wrong_dashes.docx")
    assert any(e.code == "Н-5" for e in errors)
```

#### 2.2. GREEN: Реализация

- Конфиг `university_rules.json` с констнтами из таблиц выше
- FastAPI endpoint `POST /validate/format`
- Pydantic-модель отчёта `ValidationError(code, message, location, fragment, rule_citation, recommendation)`

#### 2.3. REFACTOR

- Вынести все regex-паттерны в конфиг
- Обобщить проверки шрифтов в единый `FontValidator`

---

### Модуль 3. Контур Б — Семантический анализ

#### 3.1. RED: Тесты

**`test_scientific_style.py`**

```python
# TEST-46: Обнаружение "я" в тексте
def test_first_person_singular():
    errors = validate_style("Я считаю, что данная проблема актуальна.")
    assert any(e.code == "Н-1" for e in errors)

# TEST-47: Рекомендация пассивного залога
def test_passive_voice_recommendation():
    errors = validate_style("Мы провели исследование")
    assert any("пассивный залог" in e.recommendation.lower() for e in errors)

# TEST-48: Разговорные обороты
def test_colloquial_phrases():
    errors = validate_style("Короче говоря, результат хороший")
    assert len(errors) > 0

# TEST-49: Аббревиатура без расшифровки
def test_abbreviation_first_use():
    errors = validate_style("СПТ используется для коррекции")
    assert any(e.code == "Н-6" for e in errors)
```

**`test_introduction_structure.py`**

```python
# TEST-50: Все 10 нормативов введения присутствуют
def test_all_intro_norms():
    intro = extract_introduction("fixtures/valid_vkr.docx")
    norms = detect_methodological_norms(intro)
    required = ["актуальность", "цель", "объект", "предмет",
                "гипотеза", "задачи", "теоретико-методологическая основа",
                "характеристика выборки", "методы и методики", "структура и объём"]
    for norm in required:
        assert norm in norms, f"Отсутствует норматив: {norm}"

# TEST-51: Порядок нормативов строгий
def test_intro_norms_order():
    intro = extract_introduction("fixtures/wrong_order_intro.docx")
    norms = detect_methodological_norms(intro)
    # Нормативы должны идти в заданном порядке
    assert is_ordered(norms)

# TEST-52: Нет слов будущего времени
def test_no_future_tense():
    intro = extract_introduction("fixtures/future_tense_intro.docx")
    errors = validate_intro(intro)
    assert any(e.code == "В-3" for e in errors)

# TEST-53: Задач не более 5
def test_max_tasks():
    intro = extract_introduction("fixtures/too_many_tasks.docx")
    errors = validate_intro(intro)
    assert any(e.code == "В-4" for e in errors)
```

**`test_cross_referencing.py`**

```python
# TEST-54: Ссылка [N] соответствует источнику в списке
def test_ref_exists_in_bibliography():
    errors = validate_cross_refs("fixtures/missing_ref_source.docx")
    assert any(e.code == "Л-11" for e in errors)

# TEST-55: RAG-верификация — текст найден в PDF
def test_rag_verification_found(mock_pdf_index):
    result = verify_citation(ref_number=5, page=140, pdf_index=mock_pdf_index)
    assert result.status == "verified"

# TEST-56: RAG-верификация — текст не найден
def test_rag_verification_not_found(mock_pdf_index):
    result = verify_citation(ref_number=5, page=999, pdf_index=mock_pdf_index)
    assert result.status == "not_verified"

# TEST-57: PDF не загружен
def test_rag_source_missing():
    result = verify_citation(ref_number=99, page=1, pdf_index=None)
    assert result.status == "source_missing"
```

**`test_logical_audit.py`**

```python
# TEST-58: Содержание главы релевантно заголовку
def test_chapter_relevance(mock_llm):
    mock_llm.set_response({"relevant": True, "score": 0.9})
    result = audit_chapter("Глава 1. Теоретический анализ ...", chapter_text="...")
    assert result.is_relevant

# TEST-59: Каждая глава анализируется отдельно (Map-Reduce)
def test_map_reduce_chapters(mock_llm):
    results = audit_all_chapters("fixtures/valid_vkr.docx")
    assert len(results) >= 2  # минимум 2 главы
    assert mock_llm.call_count >= 2
```

#### 3.2. GREEN: Реализация

- `validate_style()` — regex + стоп-слова
- `detect_methodological_norms()` — LLM-запрос с промптом из методички
- `verify_citation()` — RAG с pdfplumber + sentence-transformers
- `audit_chapter()` — Map-Reduce LLM

#### 3.3. REFACTOR

- Стоп-слова → конфигурируемый YAML
- Промпты → шаблоны Jinja2

---

### Модуль 4. Pipeline и интеграция

#### 4.1. RED: Тесты

```python
# TEST-60: Полный pipeline — валидный документ → 0 критических ошибок
def test_full_pipeline_valid():
    report = pipeline_run("fixtures/valid_vkr.docx")
    critical = [e for e in report.errors if e.severity == "critical"]
    assert len(critical) == 0

# TEST-61: Pipeline вызывает контуры А и Б параллельно
def test_parallel_execution(mock_executor):
    pipeline_run("fixtures/valid_vkr.docx")
    assert mock_executor.concurrent_calls >= 2

# TEST-62: Отчёт содержит обязательные поля
def test_report_schema():
    report = pipeline_run("fixtures/valid_vkr.docx")
    for error in report.errors:
        assert error.type is not None
        assert error.location is not None
        assert error.fragment is not None
        assert error.rule_citation is not None
        assert error.recommendation is not None

# TEST-63: Система НЕ генерирует исправленный текст
def test_no_auto_fix():
    report = pipeline_run("fixtures/errors_vkr.docx")
    for error in report.errors:
        assert error.auto_corrected_text is None

# TEST-64: Временные файлы очищаются после выполнения
def test_cleanup(tmp_path):
    pipeline_run("fixtures/valid_vkr.docx", temp_dir=tmp_path)
    assert len(list(tmp_path.iterdir())) == 0
```

#### 4.2. GREEN: Реализация

- `POST /validate` — сквозной endpoint
- Параллелизация контуров через `asyncio.gather`
- `contextlib.ExitStack` для очистки

---

### Модуль 5. Frontend

#### 5.1. RED: Тесты (browser-based / Playwright)

```python
# TEST-65: Загрузка файла и получение отчёта
def test_upload_and_report(page):
    page.goto("http://localhost:3000")
    page.set_input_files("#file-upload", "fixtures/valid_vkr.docx")
    page.click("#submit-btn")
    page.wait_for_selector("#report-container")
    assert page.inner_text("#report-container") != ""

# TEST-66: Отображается прогресс-бар
def test_progress_bar(page):
    page.goto("http://localhost:3000")
    page.set_input_files("#file-upload", "fixtures/valid_vkr.docx")
    page.click("#submit-btn")
    assert page.is_visible("#progress-bar")

# TEST-67: Ошибки подсвечиваются в тексте
def test_error_highlight(page):
    page.goto("http://localhost:3000")
    # ... загрузка файла с ошибками
    highlights = page.query_selector_all(".error-highlight")
    assert len(highlights) > 0
```

---

### Золотой сет и критерии приёмки (TDD Benchmark)

| Метрика | Порог | Тест |
|---------|-------|------|
| Precision (Контур А) | ≥ 90% | `test_benchmark_precision_format()` |
| Recall (Контур А) | ≥ 85% | `test_benchmark_recall_format()` |
| Precision (Контур Б) | ≥ 80% | `test_benchmark_precision_semantic()` |
| Recall (Контур Б) | ≥ 75% | `test_benchmark_recall_semantic()` |
| Время обработки 60 с. | ≤ 120 сек | `test_benchmark_performance()` |
| Анонимизация | 100% ПДн замещены | `test_benchmark_privacy()` |

```python
# TEST-68: Золотой сет — Контур А precision ≥ 90%
def test_benchmark_precision_format():
    results = run_golden_set("golden_set/", contour="A")
    assert results.precision >= 0.90

# TEST-69: Золотой сет — Контур А recall ≥ 85%
def test_benchmark_recall_format():
    results = run_golden_set("golden_set/", contour="A")
    assert results.recall >= 0.85

# TEST-70: Золотой сет — производительность
def test_benchmark_performance():
    import time
    start = time.time()
    pipeline_run("golden_set/sample_60pages.docx")
    elapsed = time.time() - start
    assert elapsed <= 120
```

---

### План спринтов (TDD)

| Спринт | Срок | Фокус | RED (тесты) | GREEN (реализация) |
|--------|------|-------|------------|-------------------|
| 1 | 2 нед. | Контур А | TEST 9-45 + фикстуры (5 DOCX) | `validate_format`, `validate_structure`, `university_rules.json` |
| 2 | 2 нед. | Контур Б | TEST 46-59 + RAG-моки | `validate_style`, `verify_citation`, `audit_chapter` |
| 3 | 1 нед. | Privacy + Pipeline | TEST 1-8, 60-64 | `anonymize`, `pipeline_run`, интеграция |
| 4 | 2 нед. | Frontend + Benchmark | TEST 65-70 | React UI, золотой сет, бенчмарк |

---

### Этический кодекс системы

1. Система **не** генерирует исправленный текст — только указывает ошибки и рекомендации
2. Система **не** передаёт персональные данные третьим сторонам
3. Все проверки прозрачны — каждая ошибка содержит цитату из методички
