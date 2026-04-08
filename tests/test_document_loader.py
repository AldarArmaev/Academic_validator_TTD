"""
TDD: Тесты для модуля загрузки документов.
Сначала пишем тесты (красный этап), затем реализуем функционал.
"""
import pytest
from pathlib import Path
from src.contour_a.document_loader import (
    Paragraph,
    Heading,
    Table,
    Figure,
    Reference,
    DocumentContent,
    DOCXLoader,
    PDFLoader,
    get_loader,
    load_document
)


class TestParagraph:
    """Тесты модели абзаца."""
    
    def test_create_paragraph_minimal(self):
        """Создание абзаца с минимальными полями."""
        para = Paragraph(text="Тестовый текст")
        assert para.text == "Тестовый текст"
        assert para.style_name is None
        assert para.font_size is None
        assert para.is_bold is False
        assert para.page_number == 1
    
    def test_create_paragraph_full(self):
        """Создание абзаца со всеми полями."""
        para = Paragraph(
            text="Основной текст",
            style_name="Normal",
            font_size=14.0,
            font_name="Times New Roman",
            is_bold=False,
            is_italic=False,
            alignment="justify",
            line_spacing=1.5,
            indent_first_line=12.5,
            page_number=5
        )
        assert para.font_size == 14.0
        assert para.font_name == "Times New Roman"
        assert para.alignment == "justify"
        assert para.page_number == 5


class TestHeading:
    """Тесты модели заголовка."""
    
    def test_create_heading_default_level(self):
        """Создание заголовка с уровнем по умолчанию."""
        heading = Heading(text="Введение", level=1)
        assert heading.level == 1
        assert heading.numbering is None
    
    def test_create_heading_with_numbering(self):
        """Создание заголовка с нумерацией."""
        heading = Heading(
            text="Обзор литературы",
            level=2,
            numbering="1.2",
            is_bold=True
        )
        assert heading.level == 2
        assert heading.numbering == "1.2"
        assert heading.is_bold is True


class TestTable:
    """Тесты модели таблицы."""
    
    def test_create_table_minimal(self):
        """Создание таблицы с минимальными полями."""
        table = Table(rows=3, columns=4)
        assert table.rows == 3
        assert table.columns == 4
        assert table.caption is None
        assert table.caption_position == "top"
        assert table.cells == []
    
    def test_create_table_with_caption(self):
        """Создание таблицы с подписью."""
        table = Table(
            rows=2,
            columns=2,
            caption="Результаты эксперимента",
            caption_position="top",
            page_number=10
        )
        assert table.caption == "Результаты эксперимента"
        assert table.page_number == 10


class TestFigure:
    """Тесты модели рисунка."""
    
    def test_create_figure_default(self):
        """Создание рисунка со значениями по умолчанию."""
        fig = Figure()
        assert fig.figure_type == "image"
        assert fig.caption_position == "bottom"
        assert fig.caption is None
    
    def test_create_figure_with_caption(self):
        """Создание рисунка с подписью."""
        fig = Figure(
            caption="Структура системы",
            figure_type="diagram",
            page_number=15
        )
        assert fig.caption == "Структура системы"
        assert fig.figure_type == "diagram"


class TestReference:
    """Тесты модели библиографической ссылки."""
    
    def test_create_reference_default(self):
        """Создание ссылки со значениями по умолчанию."""
        ref = Reference(text="[1] Иванов И.И. Название книги.")
        assert ref.reference_type == "gost"
        assert ref.position == "inline"
        assert ref.number is None
    
    def test_create_reference_numbered(self):
        """Создание нумерованной ссылки."""
        ref = Reference(
            text="[5] Петров П.П. Статья.",
            number=5,
            position="footnote"
        )
        assert ref.number == 5
        assert ref.position == "footnote"


class TestDocumentContent:
    """Тесты модели содержимого документа."""
    
    def test_create_empty_document(self):
        """Создание пустого документа."""
        doc = DocumentContent()
        assert doc.paragraphs == []
        assert doc.headings == []
        assert doc.tables == []
        assert doc.figures == []
        assert doc.references == []
        assert doc.total_pages == 0
        assert doc.file_path is None
    
    def test_create_document_with_metadata(self):
        """Создание документа с метаданными."""
        doc = DocumentContent(
            file_path="/path/to/document.docx",
            file_name="vkf.docx",
            total_pages=65
        )
        assert doc.file_path == "/path/to/document.docx"
        assert doc.file_name == "vkf.docx"
        assert doc.total_pages == 65


class TestDOCXLoader:
    """Тесты загрузчика DOCX."""
    
    def test_supports_docx_format(self):
        """Проверка поддержки формата .docx."""
        loader = DOCXLoader()
        assert loader.supports_format('.docx') is True
        assert loader.supports_format('.DOCX') is True
        assert loader.supports_format('.doc') is True
    
    def test_not_supports_other_formats(self):
        """Проверка неподдержки других форматов."""
        loader = DOCXLoader()
        assert loader.supports_format('.pdf') is False
        assert loader.supports_format('.txt') is False
    
    def test_load_nonexistent_file(self):
        """Попытка загрузки несуществующего файла."""
        loader = DOCXLoader()
        with pytest.raises(FileNotFoundError):
            loader.load('/nonexistent/path/file.docx')


class TestPDFLoader:
    """Тесты загрузчика PDF."""
    
    def test_supports_pdf_format(self):
        """Проверка поддержки формата .pdf."""
        loader = PDFLoader()
        assert loader.supports_format('.pdf') is True
        assert loader.supports_format('.PDF') is True
    
    def test_not_supports_other_formats(self):
        """Проверка неподдержки других форматов."""
        loader = PDFLoader()
        assert loader.supports_format('.docx') is False
        assert loader.supports_format('.txt') is False
    
    def test_load_nonexistent_file(self):
        """Попытка загрузки несуществующего файла."""
        loader = PDFLoader()
        with pytest.raises(FileNotFoundError):
            loader.load('/nonexistent/path/file.pdf')


class TestGetLoader:
    """Тесты функции выбора загрузчика."""
    
    def test_get_docx_loader(self):
        """Получение загрузчика для DOCX."""
        loader = get_loader('document.docx')
        assert isinstance(loader, DOCXLoader)
    
    def test_get_pdf_loader(self):
        """Получение загрузчика для PDF."""
        loader = get_loader('document.pdf')
        assert isinstance(loader, PDFLoader)
    
    def test_unsupported_format(self):
        """Попытка получить загрузчик для неподдерживаемого формата."""
        with pytest.raises(ValueError, match="Неподдерживаемый формат"):
            get_loader('document.txt')


class TestLoadDocument:
    """Тесты функции загрузки документа."""
    
    def test_load_nonexistent_file(self):
        """Попытка загрузки несуществующего файла."""
        with pytest.raises(FileNotFoundError):
            load_document('/nonexistent/file.docx')
