# Формальные требования из методички и ТЗ через TDD

> **Версия 2.0** — исправленная редакция.

---

## Часть 0. Единая схема данных (фиксируется до написания любого теста)

> [!IMPORTANT]
> Все тесты и весь код используют **только** эти классы. Менять их нельзя без изменения тестов.

```python
# schemas.py
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class ErrorLocation(BaseModel):
    page: int
    paragraph_index: int
    chapter: Optional[str] = None

class ReportError(BaseModel):
    id: str                          # уникальный id внутри отчёта
    code: str                        # код требования: "Ф-1", "С-5", "Л-7" и т.д.
    type: Literal["formatting", "style", "citation_check"]
    severity: Literal["error", "warning", "info"]
    location: ErrorLocation
    fragment: str                    # до 100 символов из документа
    rule: str                        # формулировка требования
    rule_citation: str               # цитата из методички: "§4.2, с. 47"
    found_value: str                 # что нашли
    expected_value: str              # что ожидали
    recommendation: str              # инструкция для исправления
    # auto_corrected_text НЕ существует — система не генерирует текст

class ReportSummary(BaseModel):
    total_errors: int
    formatting: int
    style: int
    citations: int

class ValidationReport(BaseModel):
    doc_id: str
    created_at: datetime
    session_expires_at: datetime
    summary: ReportSummary
    errors: list[ReportError]
```

---

## Часть 0.1. Константы university_rules.json

```json
{
  "font": {
    "family": "Times New Roman",
    "size_half_points": 28,
    "size_pt": 14
  },
  "paragraph": {
    "line_spacing_twips": 360,
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
  "page_numbers": {
    "position": "bottom_right",
    "font_pt": 12,
    "starts_at_section": "введение",
    "start_page": 3
  },
  "volume": {
    "total_pages_min": 50,
    "total_pages_max": 60,
    "theory_chapter_pages_min": 15,
    "theory_chapter_pages_max": 20,
    "empirical_chapter_pages_min": 25,
    "empirical_chapter_pages_max": 30
  },
  "references": {
    "min_sources": 40,
    "max_years_old": 10,
    "inline_pattern": "\\[\\d+(?:,\\s*с\\.\\s*\\d+)?\\]",
    "multi_ref_pattern": "\\[\\d+(?:;\\s*\\d+)+\\]",
    "repeated_ref_pattern": "\\[там же(?:,\\s*с\\.\\s*\\d+)?\\]"
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
  "stop_words_colloquial": ["короче", "вообще-то", "на самом деле", "типа", "как бы"]
}
```

---

## Часть 0.2. Фикстуры — создаются программно в conftest.py

> [!IMPORTANT]
> Все фикстуры создаются **кодом**, не вручную в Word. Это единственный способ гарантировать
> что фикстура содержит именно то нарушение, которое мы хотим поймать.

```python
# tests/conftest.py
import pytest
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree

# ── Вспомогательные функции ──────────────────────────────────────────────────

def set_paragraph_spacing(para, line_twips: int, space_before: int = 0, space_after: int = 0):
    """Устанавливает межстрочный интервал и отступы до/после абзаца через XML."""
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:line'), str(line_twips))
    spacing.set(qn('w:lineRule'), 'auto')
    spacing.set(qn('w:before'), str(space_before))
    spacing.set(qn('w:after'), str(space_after))
    pPr.append(spacing)

def set_first_line_indent(para, dxa: int):
    """Устанавливает отступ первой строки через XML."""
    pPr = para._p.get_or_add_pPr()
    ind = OxmlElement('w:ind')
    ind.set(qn('w:firstLine'), str(dxa))
    pPr.append(ind)

def set_alignment(para, alignment: str):
    """alignment: 'both' | 'left' | 'center' | 'right'"""
    pPr = para._p.get_or_add_pPr()
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), alignment)
    pPr.append(jc)

def add_correct_paragraph(doc, text: str):
    """Добавляет абзац со всеми правильными параметрами форматирования."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, line_twips=360, space_before=0, space_after=0)
    set_first_line_indent(p, dxa=720)
    set_alignment(p, 'both')
    return p

def make_base_doc():
    """Создаёт документ с правильными полями."""
    doc = Document()
    s = doc.sections[0]
    s.left_margin   = 1701 * 635
    s.right_margin  = 567  * 635
    s.top_margin    = 1134 * 635
    s.bottom_margin = 1134 * 635
    return doc

# ── Фикстуры для Модуля 2 (Контур А) ─────────────────────────────────────────

@pytest.fixture(scope="session")
def correct_docx(tmp_path_factory):
    """Полностью корректный документ — 0 ошибок форматирования."""
    path = tmp_path_factory.mktemp("fix") / "correct.docx"
    doc = make_base_doc()
    for title in ["Введение", "Глава 1. Теоретические основы", "Заключение", "Список литературы"]:
        doc.add_heading(title, level=1)
        add_correct_paragraph(doc, "Текст раздела. Содержательный абзац.")
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_font_docx(tmp_path_factory):
    """Абзац с Arial вместо Times New Roman (нарушение Ф-1)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_font.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    add_correct_paragraph(doc, "Правильный абзац.")
    p = doc.add_paragraph()
    run = p.add_run("Абзац с неправильным шрифтом Arial.")
    run.font.name = "Arial"           # ← нарушение Ф-1
    run.font.size = Pt(14)
    set_paragraph_spacing(p, 360)
    set_first_line_indent(p, 720)
    set_alignment(p, 'both')
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_spacing_docx(tmp_path_factory):
    """Абзац с одинарным интервалом вместо 1.5 (нарушение Ф-2)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_spacing.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    p = doc.add_paragraph()
    run = p.add_run("Абзац с одинарным интервалом.")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, line_twips=240, space_before=0, space_after=0)  # ← 1.0, нарушение Ф-2
    set_first_line_indent(p, 720)
    set_alignment(p, 'both')
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_alignment_docx(tmp_path_factory):
    """Абзац с выравниванием по левому краю (нарушение Ф-3)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_alignment.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    p = doc.add_paragraph()
    run = p.add_run("Абзац выровнен по левому краю.")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, 360)
    set_first_line_indent(p, 720)
    set_alignment(p, 'left')          # ← нарушение Ф-3
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_margins_docx(tmp_path_factory):
    """Левое поле 2 см вместо 3 см (нарушение Ф-4)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_margins.docx"
    doc = Document()
    s = doc.sections[0]
    s.left_margin   = 1134 * 635     # ← 2 см, нарушение Ф-4
    s.right_margin  = 567  * 635
    s.top_margin    = 1134 * 635
    s.bottom_margin = 1134 * 635
    doc.add_heading("Введение", level=1)
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_indent_docx(tmp_path_factory):
    """Абзацный отступ 0 вместо 1.25 см (нарушение Ф-5)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_indent.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    p = doc.add_paragraph()
    run = p.add_run("Абзац без отступа первой строки.")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, 360)
    set_first_line_indent(p, dxa=0)  # ← нарушение Ф-5
    set_alignment(p, 'both')
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_para_spacing_docx(tmp_path_factory):
    """Интервал после абзаца 12 пт вместо 0 (нарушение Ф-6)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_para_spacing.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    p = doc.add_paragraph()
    run = p.add_run("Абзац с отступом после 12 пт.")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    set_paragraph_spacing(p, line_twips=360, space_before=0, space_after=240)  # ← нарушение Ф-6
    set_first_line_indent(p, 720)
    set_alignment(p, 'both')
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def missing_conclusion_docx(tmp_path_factory):
    """Документ без раздела Заключение (нарушение С-1)."""
    path = tmp_path_factory.mktemp("fix") / "missing_conclusion.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    doc.add_heading("Глава 1. Теоретические основы", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def wrong_chapter_name_docx(tmp_path_factory):
    """Заголовок главы без слова 'Глава' (нарушение С-5)."""
    path = tmp_path_factory.mktemp("fix") / "wrong_chapter_name.docx"
    doc = make_base_doc()
    doc.add_heading("Введение", level=1)
    doc.add_heading("1. Теоретические основы", level=1)  # ← нарушение С-5, нет слова "Глава"
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture(scope="session")
def heading_with_period_docx(tmp_path_factory):
    """Заголовок с точкой в конце (нарушение С-9)."""
    path = tmp_path_factory.mktemp("fix") / "heading_with_period.docx"
    doc = make_base_doc()
    doc.add_heading("Введение.", level=1)       # ← нарушение С-9
    doc.add_heading("Заключение", level=1)
    doc.add_heading("Список литературы", level=1)
    doc.save(path)
    return path

@pytest.fixture
def rules(tmp_path):
    import json
    rules_path = (
        __file__
        .__class__.__mro__[0]  # pathlib trick — просто используй Path
    )
    import json
    from pathlib import Path
    rpath = Path(__file__).parent.parent / "normocontroller" / "backend" / "university_rules.json"
    with open(rpath) as f:
        return json.load(f)
```

---

## Часть 1. Формальные требования из методички

> Источник: «Подготовка, оформление и защита ВКР» (ИГУ, факультет психологии, 2021).

### 1. Структура документа (Контур А)

| № | Требование | Раздел методички | Способ проверки |
|---|-----------|-----------------|----------------|
| С-1 | Обязательные разделы: Титульный лист → Содержание → Введение → Глава 1 (≥ 2 параграфа + выводы) → Глава 2 (2–3 параграфа + выводы) → Заключение → Список литературы | §1, с. 7 | Парсинг `w:pStyle` (Heading1/Heading2), проверка наличия разделов по шаблону |
| С-2 | Приложения — опциональны, при наличии нумеруются арабскими цифрами и имеют ссылки из текста | §3.8, с. 44 | Поиск паттерна «Приложение N» + проверка наличия `(прил. N)` в тексте |
| С-3 | Каждый новый раздел (Содержание, Введение, Глава, Заключение, Список литературы, Приложения) — с новой страницы | §4.2, с. 47 | Проверка наличия `w:pageBreakBefore` или `w:br w:type="page"` перед разделом |
| С-4 | Параграфы **не** начинаются с новой страницы | §4.2, с. 47 | Проверка отсутствия `w:pageBreakBefore` перед Heading2/Heading3 |
| С-5 | Нумерация глав: «Глава N. Название» | §4.2, с. 47 | Regex: `^Глава \d+\.\s.+` на заголовки Heading1 |
| С-6 | Нумерация параграфов: `1.1.`, `1.1.1.` | §4.2, с. 47 | Regex: `^\d+\.\d+(\.\d+)?\s.+` на заголовки Heading2/Heading3 |
| С-7 | Названия разделов и параграфов **не** выделяются (не bold/italic) и **не** подчёркиваются | §4.2, с. 47 | Проверка `w:b`, `w:i`, `w:u` в `w:rPr` заголовков |
| С-8 | Все названия выравниваются по центру, без абзацного отступа | §4.2, с. 47 | Проверка `w:jc = "center"` + `w:ind @firstLine = 0` в заголовках |
| С-9 | Точки в конце названий глав и параграфов **не** ставятся | §4.2, с. 47 | Regex: заголовок не заканчивается на `.` |
| С-10 | Внутри параграфов — никаких подзаголовков | §4.2, с. 47 | Проверка отсутствия Heading-стилей внутри секций параграфов |

### 2. Форматирование текста (Контур А)

| № | Требование | Значение | XML-атрибут | Раздел |
|---|-----------|---------|-------------|--------|
| Ф-1 | Шрифт основного текста | Times New Roman, 14 пт | `w:rFonts w:ascii`, `w:sz = 28` | §4.2, с. 47 |
| Ф-2 | Межстрочный интервал | 1,5 → `w:line = 360`, `w:lineRule = "auto"` | `w:spacing w:line` | §4.2, с. 47 |
| Ф-3 | Выравнивание основного текста | по ширине → `"both"` | `w:jc w:val` | §4.2, с. 47 |
| Ф-4 | Поля | лев. 1701 DXA; прав. 567 DXA; верх. 1134 DXA; ниж. 1134 DXA | `w:pgMar` | §4.2, с. 47 |
| Ф-5 | Абзацный отступ | 1,25 см → 720 DXA | `w:ind w:firstLine` | §4.2, с. 47 |
| Ф-6 | Интервалы перед и после абзаца | 0,0 пт → 0 twips | `w:spacing w:before`, `w:spacing w:after` | §4.2, с. 47 |
| Ф-7 | Нумерация страниц: положение | правый нижний угол | поле `PAGE` в нижнем колонтитуле | §4.2, с. 47 |
| Ф-8 | Нумерация страниц: шрифт | Times New Roman, 12 пт | `w:sz = 24` в колонтитуле | §4.2, с. 47 |
| Ф-9 | Нумерация начинается с Введения (с. 3) | Титульный лист и содержание без номеров | `w:titlePg`, `w:pgNumType w:start` | §4.2, с. 47 |
| Ф-10 | На страницах приложений нет номеров | Без нумерации в секции приложений | отдельная `w:sectPr` для приложений | §4.2, с. 47 |
| Ф-11 | Объём ВКР | 50—60 с. (без приложений) | Подсчёт страниц | §4.1, с. 46 |
| Ф-12 | Теоретическая глава | 15—20 с. | Подсчёт страниц главы | §3.4, с. 23 |
| Ф-13 | Эмпирическая глава | 25—30 с. | Подсчёт страниц главы | §3.5, с. 30 |

### 3. Таблицы и рисунки (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| Т-1 | «Таблица N» — **над** таблицей, выравнивание по правому краю | §4.4, с. 50 |
| Т-2 | Название таблицы — ниже, по центру, без абзацного отступа, с прописной | §4.4, с. 50 |
| Т-3 | Точки после номера и названия таблицы **не** ставятся | §4.4, с. 50 |
| Т-4 | Шрифт внутри таблицы: Times New Roman, 12 пт (допустимо 11 пт), интервал 1 | §4.4, с. 51 |
| Т-5 | Автоподбор «по ширине окна»; выравнивание в ячейках — по центру | §4.4, с. 51 |
| Т-6 | Нумерация таблиц и рисунков — сквозная по всей работе | §4.4, с. 50 |
| Т-7 | Подпись рисунка: `Рис. N. Название` — **под** рисунком, по центру, без отступа | §4.4, с. 52 |
| Т-8 | Название рисунка с прописной; точка после «Рис. N.» есть, после названия — нет | §4.4, с. 52 |
| Т-9 | Условные обозначения рисунка — между рисунком и подписью, 12 пт | §4.4, с. 52 |
| Т-10 | Интервал в названиях рисунков — 1; в названиях таблиц — 1,5 | §4.4, с. 51-52 |
| Т-11 | Запрет дублирования: данные не дублируются в таблице и рисунке | §3.5, с. 38 |
| Т-12 | Дробные числа — с запятой (2,5), не с точкой (2.5) | §4.4, с. 51 |

### 4. Ссылки и список литературы (Контуры А + Б)

| № | Требование | Раздел | Контур |
|---|-----------|--------|--------|
| Л-1 | Формат ссылки: `[N]` или `[N, с. X]` | §4.3, с. 49 | А |
| Л-2 | Повторная ссылка: `[там же, с. X]` | §4.3, с. 49 | А |
| Л-3 | Несколько источников: `[4; 12; 25]` — в арифметическом порядке через `;` | §4.3, с. 49 | А |
| Л-4 | Список литературы: алфавитный порядок, сначала русские, затем иностранные | §4.5, с. 52 | А |
| Л-5 | Нумерация источников — сплошная | §4.5, с. 53 | А |
| Л-6 | В список **не** включаются учебники и учебные пособия | §3.7, с. 44 | Б (LLM) |
| Л-7 | Не менее 40 источников | §3.7, с. 44 | А |
| Л-8 | Основная часть источников — последние 10 лет | §3.7, с. 44 | А |
| Л-9 | Формат автора: `Выготский, Л. С.` (фамилия, пробел, инициалы) | §4.5, с. 54 | А |
| Л-10 | URL-ссылки: дата обращения `(дата обращения: ДД.ММ.ГГГГ)` | §4.5, с. 58 | А |
| Л-11 | RAG-верификация: ссылка `[N]` соответствует источнику в списке | §4.3 | Б |
| Л-12 | Все тире в библиографии — длинные (–) | §4.5, с. 58 | А |

### 5. Введение — методологические нормативы (Контур Б)

| № | Требование | Раздел |
|---|-----------|--------|
| В-1 | Введение содержит все 10 нормативов в строгом порядке: актуальность → цель → объект → предмет → гипотеза → задачи → теоретико-методологическая основа → характеристика выборки → методы и методики → структура и объём ВКР | §3.3, с. 12-13 |
| В-2 | Ключевые слова нормативов выделены (bold/italic/underline) | §4.2, с. 47-48 |
| В-3 | Введение не содержит фраз будущего времени: «мы планируем», «мы будем» | §3.3, с. 13 |
| В-4 | Задач не более 4—5 | §3.3, с. 17 |
| В-5 | Ни одна задача не дублирует цель | §3.3, с. 17 |
| В-6 | Предмет ВКР совпадает с темой ВКР | §3.3, с. 16 |

### 6. Научный стиль (Контур Б)

| № | Требование | Раздел |
|---|-----------|--------|
| Н-1 | Запрет «я», «мне»; для «мы/нам» — рекомендация пассивного залога | §3.3.1 |
| Н-2 | Между инициалами и перед фамилиями — неразрывные пробелы (`И.\u00a0И.\u00a0Иванов`) | §4.2, с. 48 |
| Н-3 | Сокращения `т. д.`, `т. п.` — после точки пробел | §4.2, с. 48 |
| Н-4 | Кавычки — уголки `« »`; кавычки в кавычках — лапки `" "` | §4.2, с. 48 |
| Н-5 | Сложносочинённые слова — дефис (-); между датами/числами — тире (–) | §4.2, с. 48 |
| Н-6 | Аббревиатуры: при первом использовании — полностью + аббревиатура в скобках | §4.1, с. 46 |
| Н-7 | Оригинальность текста — не менее 60% | §2, с. 11 |
| Н-8 | Списки — автоматическая нумерация; единый маркер | §4.2, с. 48 |

### 7. Формулы (Контур А)

| № | Требование | XML | Раздел |
|---|-----------|-----|--------|
| Фр-1 | Формула в редакторе формул, в отдельной строке | `w:oMath` в отдельном `w:p` | §4.2, с. 48 |
| Фр-2 | Идентификатор формулы в скобках: `(1.1)`, `(2.3)` | Regex после `w:oMath` | §4.2 |

### 8. Содержание (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| Со-1 | Содержание отражает все заголовки с номерами страниц | §3.2, с. 12 |
| Со-2 | Выполняется в виде таблицы без границ | §3.2, с. 12 |
| Со-3 | Нумерация страниц в содержании совпадает с реальными | §3.2, с. 12 |

### 9. Приложения (Контур А)

| № | Требование | Раздел |
|---|-----------|--------|
| П-1 | Каждое приложение — с новой страницы | §4.6, с. 59 |
| П-2 | «Приложение N» — в правом верхнем углу | §4.6, с. 59 |
| П-3 | Название приложения — по центру, без отступа, без точки | §4.6, с. 59 |
| П-4 | Нумерация арабскими цифрами в порядке ссылок | §4.6, с. 59 |

---

## Часть 2. Техническое задание в методологии TDD

> [!IMPORTANT]
> Тесты пишутся **до** реализации. Функциональность считается готовой только при прохождении всех тестов.
> Все тесты используют схему из Части 0. Все фикстуры создаются из conftest.py (Часть 0.2).

---

### Модуль 1. Препроцессинг и приватность (Privacy Shield)

#### Сигнатуры функций

```python
def anonymize(text: str) -> tuple[str, dict[str, str]]:
    """Возвращает (анонимизированный текст, маппинг токен→оригинал)."""

def deanonymize(text: str, mapping: dict[str, str]) -> str:
    """Обратная замена токенов на оригиналы."""

def parse_docx(docx_path: str) -> str:
    """Конвертирует DOCX в Markdown с иерархией заголовков."""

def detect_chapters(docx_path: str) -> list[Chapter]:
    """Возвращает список глав с заголовком, уровнем и индексами абзацев."""

def extract_formulas(docx_path: str) -> list[Formula]:
    """Возвращает список формул с latex-представлением и наличием подписи."""
```

```python
# Типы данных
from dataclasses import dataclass

@dataclass
class Chapter:
    title: str
    level: int          # 1 или 2
    style: str          # "Heading1" или "Heading2"
    paragraph_indices: list[int]

@dataclass
class Formula:
    paragraph_index: int
    latex: str | None   # None если конвертация не удалась
    has_caption: bool   # есть ли идентификатор вида (1.1) после формулы
```

#### RED: Тесты

```python
# tests/test_anonymization.py

def test_anonymize_fio():
    """NER заменяет ФИО."""
    text = "Студент Иванов Иван Иванович выполнил работу"
    result, mapping = anonymize(text)
    assert "Иванов" not in result
    assert any("STUDENT_NAME" in k or "PER" in k for k in mapping.values())

def test_anonymize_returns_mapping():
    """Маппинг позволяет восстановить оригинал."""
    text = "Студент Иванов Иван Иванович"
    anon, mapping = anonymize(text)
    restored = deanonymize(anon, mapping)
    assert "Иванов" in restored

def test_anonymize_email():
    """Email анонимизируется регуляркой."""
    text = "email: student@isu.ru"
    result, mapping = anonymize(text)
    assert "student@isu.ru" not in result
    assert any("EMAIL" in k for k in mapping)

def test_anonymize_phone():
    """Телефон анонимизируется регуляркой."""
    text = "тел. +7 (3952) 24-18-70"
    result, mapping = anonymize(text)
    assert "+7 (3952) 24-18-70" not in result
    assert any("PHONE" in k for k in mapping)

def test_same_name_same_token():
    """Одно и то же ФИО получает один токен, не два разных."""
    text = "Иванов написал. Работа Иванова проверена."
    result, mapping = anonymize(text)
    name_tokens = [k for k in mapping if "NAME" in k or "PER" in k]
    assert len(name_tokens) == 1, f"Ожидали 1 токен, получили: {name_tokens}"
```

```python
# tests/test_parsing.py

def test_docx_to_markdown_headings(correct_docx):
    """DOCX конвертируется в Markdown с заголовками H1."""
    md = parse_docx(str(correct_docx))
    assert "# Введение" in md or "# " in md

def test_detect_chapters_count(correct_docx):
    """Главы детектируются по стилю Heading1."""
    chapters = detect_chapters(str(correct_docx))
    assert len(chapters) >= 2

def test_detect_chapters_style(correct_docx):
    """Каждая глава имеет правильный стиль."""
    chapters = detect_chapters(str(correct_docx))
    for ch in chapters:
        assert ch.style in ("Heading 1", "Heading 2", "Heading1", "Heading2")
```

#### GREEN: Реализация

- `anonymize()` на базе Natasha NER + regex для email/телефонов
- `parse_docx()` с python-docx → Markdown
- `detect_chapters()` по `w:pStyle = Heading1/Heading2`
- `extract_formulas()` с mathml2latex (при ошибке — `latex=None`)

---

### Модуль 2. Контур А — Проверка оформления

#### Сигнатуры функций

```python
def validate_format(docx_path: str, rules: dict) -> ValidationReport:
    """Объединяет все проверки форматирования и возвращает отчёт."""

def check_font_formatting(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет шрифт и кегль (Ф-1). Пропускает заголовки."""

def check_paragraph_formatting(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет интервал (Ф-2), выравнивание (Ф-3), отступ (Ф-5), интервалы до/после (Ф-6)."""

def check_margins(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет поля документа (Ф-4). Допуск ±50 DXA."""

def validate_structure(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет структуру: разделы (С-1), заголовки (С-5, С-7, С-8, С-9)."""

def validate_tables(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет оформление таблиц (Т-1..Т-6, Т-12)."""

def validate_figures(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет оформление рисунков (Т-7..Т-10)."""

def validate_references(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет ссылки и список литературы (Л-1..Л-5, Л-7..Л-10, Л-12)."""

def validate_volume(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет объём работы (Ф-11..Ф-13)."""

def validate_formulas(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет оформление формул (Фр-1, Фр-2)."""

def validate_appendices(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет оформление приложений (П-1..П-4)."""

def validate_typography(doc: Document, rules: dict) -> list[ReportError]:
    """Проверяет типографику (Н-2..Н-5, Н-8)."""
```

#### RED: Тесты

```python
# tests/test_format_validation.py

def test_main_font_error(wrong_font_docx, rules):
    errors = validate_format(str(wrong_font_docx), rules)
    font_errors = [e for e in errors if e.code == "Ф-1"]
    assert len(font_errors) >= 1, "Ошибка Ф-1 не обнаружена"
    assert any(e.found_value == "Arial" for e in font_errors)

def test_correct_font_no_error(correct_docx, rules):
    errors = validate_format(str(correct_docx), rules)
    assert all(e.code != "Ф-1" for e in errors), "Ложное срабатывание Ф-1"

def test_line_spacing_error(wrong_spacing_docx, rules):
    errors = validate_format(str(wrong_spacing_docx), rules)
    assert any(e.code == "Ф-2" for e in errors), "Ошибка Ф-2 не обнаружена"

def test_alignment_error(wrong_alignment_docx, rules):
    errors = validate_format(str(wrong_alignment_docx), rules)
    assert any(e.code == "Ф-3" for e in errors), "Ошибка Ф-3 не обнаружена"

def test_margins_error(wrong_margins_docx, rules):
    errors = validate_format(str(wrong_margins_docx), rules)
    assert any(e.code == "Ф-4" for e in errors), "Ошибка Ф-4 не обнаружена"

def test_indent_error(wrong_indent_docx, rules):
    errors = validate_format(str(wrong_indent_docx), rules)
    assert any(e.code == "Ф-5" for e in errors), "Ошибка Ф-5 не обнаружена"

def test_para_spacing_error(wrong_para_spacing_docx, rules):
    errors = validate_format(str(wrong_para_spacing_docx), rules)
    assert any(e.code == "Ф-6" for e in errors), "Ошибка Ф-6 не обнаружена"

def test_required_sections_error(missing_conclusion_docx, rules):
    errors = validate_format(str(missing_conclusion_docx), rules)
    conclusion_errors = [e for e in errors if e.code == "С-1" and "Заключение" in e.fragment]
    assert len(conclusion_errors) == 1, "Ошибка С-1 (Заключение) не обнаружена"

def test_chapter_naming_error(wrong_chapter_name_docx, rules):
    errors = validate_format(str(wrong_chapter_name_docx), rules)
    assert any(e.code == "С-5" for e in errors), "Ошибка С-5 не обнаружена"

def test_heading_no_period_error(heading_with_period_docx, rules):
    errors = validate_format(str(heading_with_period_docx), rules)
    assert any(e.code == "С-9" for e in errors), "Ошибка С-9 не обнаружена"

def test_error_has_all_fields(wrong_font_docx, rules):
    """Каждая ошибка содержит все обязательные поля."""
    errors = validate_format(str(wrong_font_docx), rules)
    assert errors, "Нет ошибок для проверки"
    for e in errors:
        assert e.id
        assert e.code
        assert e.type in ("formatting", "style", "citation_check")
        assert e.severity in ("error", "warning", "info")
        assert e.location is not None
        assert e.rule
        assert e.rule_citation   # цитата из методички
        assert e.found_value is not None
        assert e.expected_value is not None
        assert len(e.recommendation) > 10

def test_summary_matches_errors(wrong_font_docx, rules):
    """summary.total_errors совпадает с len(errors)."""
    report = validate_format(str(wrong_font_docx), rules)
    assert report.summary.total_errors == len(report.errors)
    assert report.summary.formatting == sum(1 for e in report.errors if e.type == "formatting")

def test_no_auto_corrected_text(wrong_font_docx, rules):
    """Система не генерирует исправленный текст."""
    report = validate_format(str(wrong_font_docx), rules)
    for e in report.errors:
        assert not hasattr(e, "auto_corrected_text"), "Поле auto_corrected_text не должно существовать"
```

```python
# tests/test_references.py
# Фикстуры для ссылок создаются прямо в тестах через tmp_path

def test_reference_format_error(tmp_path, rules):
    """Неправильный формат ссылки (1) вместо [1] → ошибка Л-1."""
    doc = Document()
    doc.add_paragraph("Как показано в исследовании (1), результаты значимы.")
    path = tmp_path / "wrong_ref.docx"
    doc.save(path)
    errors = validate_references(Document(str(path)), rules)
    assert any(e.code == "Л-1" for e in errors)

def test_multiple_refs_order_error(tmp_path, rules):
    """Ссылки в неправильном порядке [12; 4; 25] → ошибка Л-3."""
    doc = Document()
    doc.add_paragraph("По данным ряда авторов [12; 4; 25] выявлено следующее.")
    path = tmp_path / "wrong_order.docx"
    doc.save(path)
    errors = validate_references(Document(str(path)), rules)
    assert any(e.code == "Л-3" for e in errors)

def test_min_sources_error(tmp_path, rules):
    """Менее 40 источников → ошибка Л-7."""
    doc = Document()
    doc.add_heading("Список литературы", level=1)
    for i in range(5):   # только 5 источников
        doc.add_paragraph(f"{i+1}. Иванов, И.И. Книга. – М.: Изд-во, 2020. – 200 с.")
    path = tmp_path / "few_sources.docx"
    doc.save(path)
    errors = validate_references(Document(str(path)), rules)
    assert any(e.code == "Л-7" for e in errors)
    err = next(e for e in errors if e.code == "Л-7")
    assert err.found_value == "5"
    assert err.expected_value == "40"
```

```python
# tests/test_typography.py

def test_initials_no_space_error(tmp_path, rules):
    """Инициалы без пробела И.И.Иванов → ошибка Н-2."""
    doc = Document()
    doc.add_paragraph("Исследование И.И.Иванова показало следующее.")
    path = tmp_path / "no_space.docx"
    doc.save(path)
    errors = validate_typography(Document(str(path)), rules)
    assert any(e.code == "Н-2" for e in errors)

def test_wrong_quotes_error(tmp_path, rules):
    """Кавычки-лапки вместо уголков → ошибка Н-4."""
    doc = Document()
    doc.add_paragraph('Понятие "стресс" введено Г. Селье.')
    path = tmp_path / "wrong_quotes.docx"
    doc.save(path)
    errors = validate_typography(Document(str(path)), rules)
    assert any(e.code == "Н-4" for e in errors)
```

---

### Модуль 3. Контур Б — Семантический анализ

#### Сигнатуры функций

```python
def validate_style(text: str, rules: dict) -> list[ReportError]:
    """Проверяет научный стиль: местоимения (Н-1), разговорные обороты, аббревиатуры (Н-6)."""

def detect_methodological_norms(intro_text: str) -> dict[str, int]:
    """Возвращает dict {норматив: позиция_в_тексте} для 10 нормативов введения."""

def validate_intro(intro_text: str) -> list[ReportError]:
    """Проверяет структуру введения (В-1..В-6) через LLM."""

def verify_citation(
    ref_number: int,
    page: int,
    pdf_index         # EmbeddingIndex или None
) -> CitationResult:
    """RAG-верификация ссылки."""

def audit_chapter(chapter_title: str, chapter_text: str, methodology_context: str) -> ChapterAudit:
    """LLM-анализ соответствия содержания главы её заголовку."""

def audit_all_chapters(docx_path: str) -> list[ChapterAudit]:
    """Map-Reduce: анализирует каждую главу отдельно, возвращает список аудитов."""
```

```python
# Типы данных
from dataclasses import dataclass
from typing import Literal

@dataclass
class CitationResult:
    ref_number: int
    status: Literal["verified", "not_verified", "source_missing"]
    score: float | None  # cosine similarity, None если source_missing

@dataclass
class ChapterAudit:
    chapter_title: str
    is_relevant: bool
    score: float        # 0.0–1.0
    issues: list[str]   # список замечаний
```

#### RED: Тесты

```python
# tests/test_scientific_style.py

def test_first_person_singular(rules):
    errors = validate_style("Я считаю, что данная проблема актуальна.", rules)
    assert any(e.code == "Н-1" for e in errors)

def test_passive_voice_recommendation(rules):
    errors = validate_style("Мы провели исследование.", rules)
    style_errors = [e for e in errors if e.code == "Н-1"]
    assert any("пассивный залог" in e.recommendation.lower() for e in style_errors)

def test_abbreviation_no_explanation(rules):
    errors = validate_style("СПТ используется для коррекции стресса.", rules)
    assert any(e.code == "Н-6" for e in errors)

def test_abbreviation_with_explanation_no_error(rules):
    errors = validate_style(
        "Социально-психологический тренинг (СПТ) используется. Затем СПТ применяли снова.", rules
    )
    assert all(e.code != "Н-6" for e in errors)
```

```python
# tests/test_cross_referencing.py

def test_rag_verified(mock_pdf_index):
    """
    mock_pdf_index — pytest fixture, создаёт EmbeddingIndex с проиндексированным PDF,
    в котором заведомо есть текст на стр. 12.
    """
    result = verify_citation(ref_number=1, page=12, pdf_index=mock_pdf_index)
    assert result.status == "verified"
    assert result.score >= 0.6

def test_rag_not_verified(mock_pdf_index):
    """Страница 999 в PDF отсутствует — not_verified."""
    result = verify_citation(ref_number=1, page=999, pdf_index=mock_pdf_index)
    assert result.status == "not_verified"

def test_rag_source_missing():
    """pdf_index=None → source_missing."""
    result = verify_citation(ref_number=99, page=1, pdf_index=None)
    assert result.status == "source_missing"
    assert result.score is None

@pytest.fixture
def mock_pdf_index(tmp_path):
    """Создаёт реальный EmbeddingIndex из минимального PDF."""
    from preprocessing.pdf_utils import create_test_pdf
    from contour_b.embedder import EmbeddingIndex
    pdf_path = tmp_path / "source_1.pdf"
    # Создаёт PDF с текстом "Исследование показало значимые результаты" на стр. 12
    create_test_pdf(pdf_path, page=12, text="Исследование показало значимые результаты.")
    index = EmbeddingIndex()
    index.add_document("source_1", str(pdf_path))
    return index
```

```python
# tests/test_logical_audit.py

def test_chapter_relevance(mocker):
    """Мок LLM возвращает {'is_relevant': True, 'score': 0.9, 'issues': []}."""
    mocker.patch(
        "contour_b.llm_client.LLMClient.analyze_chapter",
        return_value=ChapterAudit(
            chapter_title="Глава 1. Теоретический анализ",
            is_relevant=True,
            score=0.9,
            issues=[]
        )
    )
    result = audit_chapter(
        chapter_title="Глава 1. Теоретический анализ",
        chapter_text="Текст главы...",
        methodology_context="Требования методички..."
    )
    assert result.is_relevant
    assert result.score >= 0.5

def test_map_reduce_calls_llm_per_chapter(mocker, correct_docx):
    """audit_all_chapters делает отдельный LLM-вызов на каждую главу."""
    mock_analyze = mocker.patch(
        "contour_b.llm_client.LLMClient.analyze_chapter",
        return_value=ChapterAudit("", True, 0.8, [])
    )
    results = audit_all_chapters(str(correct_docx))
    assert len(results) >= 1
    assert mock_analyze.call_count == len(results)
```

---

### Модуль 4. Pipeline и интеграция

#### Сигнатура

```python
def pipeline_run(
    docx_path: str,
    methodology_pdf: str | None = None,
    source_pdfs: list[str] | None = None,
    temp_dir: str | None = None   # если None — создаётся автоматически и удаляется
) -> ValidationReport:
    """Полный pipeline: препроцессинг → Контур А ∥ Контур Б → агрегация → очистка."""
```

#### RED: Тесты

```python
# tests/test_pipeline.py

def test_full_pipeline_valid(correct_docx, rules):
    report = pipeline_run(str(correct_docx))
    critical = [e for e in report.errors if e.severity == "error" and e.code.startswith("Ф-")]
    # Корректный документ — нет критических ошибок форматирования
    assert len(critical) == 0

def test_report_schema(correct_docx):
    """Все обязательные поля отчёта заполнены."""
    report = pipeline_run(str(correct_docx))
    assert report.doc_id
    assert report.created_at
    assert report.session_expires_at > report.created_at
    assert report.summary.total_errors == len(report.errors)
    for error in report.errors:
        assert error.code
        assert error.rule_citation
        assert error.recommendation

def test_cleanup(correct_docx, tmp_path):
    """Временные файлы удаляются после выполнения."""
    pipeline_run(str(correct_docx), temp_dir=str(tmp_path))
    remaining = list(tmp_path.iterdir())
    assert len(remaining) == 0, f"Временные файлы не удалены: {remaining}"

def test_no_auto_corrected_text_in_pipeline(wrong_font_docx):
    """Pipeline не добавляет исправленный текст ни в одну ошибку."""
    report = pipeline_run(str(wrong_font_docx))
    for error in report.errors:
        assert not hasattr(error, "auto_corrected_text")
```

---

### Золотой сет и критерии приёмки

#### Сигнатура

```python
@dataclass
class BenchmarkResult:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int

def run_golden_set(
    golden_dir: str,            # директория с .docx + .json аннотациями
    contour: Literal["A", "B"]  # какой контур тестировать
) -> BenchmarkResult:
    """
    Формат аннотации golden_dir/sample.json:
    {"errors": [{"code": "Ф-1", "paragraph_index": 5}, ...]}
    """
```

| Метрика | Порог | Тест |
|---------|-------|------|
| Precision (Контур А) | ≥ 90% | `test_benchmark_precision_format` |
| Recall (Контур А) | ≥ 85% | `test_benchmark_recall_format` |
| Precision (Контур Б) | ≥ 80% | `test_benchmark_precision_semantic` |
| Recall (Контур Б) | ≥ 75% | `test_benchmark_recall_semantic` |
| Время (60 стр. + 3 PDF) | ≤ 120 сек | `test_benchmark_performance` |
| Анонимизация | 100% ПДн замещены | `test_benchmark_privacy` |

```python
# tests/test_benchmark.py

def test_benchmark_precision_format():
    results = run_golden_set("tests/golden_set/", contour="A")
    assert results.precision >= 0.90, f"Precision={results.precision:.2f} < 0.90"

def test_benchmark_recall_format():
    results = run_golden_set("tests/golden_set/", contour="A")
    assert results.recall >= 0.85, f"Recall={results.recall:.2f} < 0.85"

def test_benchmark_performance(correct_docx):
    import time
    start = time.time()
    pipeline_run(str(correct_docx))
    elapsed = time.time() - start
    assert elapsed <= 120, f"Время выполнения {elapsed:.1f}с > 120с"
```

---

### План спринтов (TDD)

| Спринт | Срок | Фокус | RED (тесты) | GREEN (реализация) |
|--------|------|-------|------------|-------------------|
| 1 | 2 нед. | Контур А | Тесты Модуля 2 + фикстуры из conftest.py | `check_font_formatting`, `check_paragraph_formatting`, `check_margins`, `validate_structure`, `university_rules.json` |
| 2 | 2 нед. | Контур Б | Тесты Модуля 3 + `mock_pdf_index` fixture | `validate_style`, `verify_citation`, `audit_chapter` |
| 3 | 1 нед. | Privacy + Pipeline | Тесты Модулей 1 и 4 | `anonymize`, `parse_docx`, `pipeline_run` |
| 4 | 2 нед. | Frontend + Benchmark | Тесты Модуля 5 + `test_benchmark.py` | React UI, `run_golden_set`, бенчмарк |

---

### Этический кодекс системы

1. Система **не** генерирует исправленный текст — поле `auto_corrected_text` **не существует** в схеме
2. Система **не** передаёт персональные данные третьим сторонам без анонимизации
3. Каждая ошибка содержит поле `rule_citation` — цитату из методички
4. LLM работает только с загруженными файлами (`temperature=0`, системный промпт запрещает внешние знания)
