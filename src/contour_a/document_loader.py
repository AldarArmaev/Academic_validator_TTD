"""
Модуль загрузки и парсинга документов для Контура А.
Поддерживает форматы: DOCX, PDF
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum


class Alignment(str, Enum):
    """Типы выравнивания текста."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class LineSpacingRule(str, Enum):
    """Типы межстрочных интервалов."""
    AUTO = "auto"
    EXACT = "exact"
    AT_LEAST = "at_least"


class ReferenceType(str, Enum):
    """Типы библиографических ссылок."""
    BRACKETED = "bracketed"  # [1], [1, с. 5]
    FOOTNOTE = "footnote"
    BIBLIOGRAPHY = "bibliography"
    SAME_AS = "same_as"  # [там же, с. 5]


@dataclass
class Paragraph:
    """Представление абзаца текста."""
    text: str
    style_name: Optional[str] = None
    font_size: Optional[float] = None  # в пунктах
    font_name: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False
    underline: bool = False
    alignment: Optional[str] = None  # left, center, right, justify
    line_spacing: Optional[float] = None
    line_spacing_rule: str = "auto"  # auto, exact, at_least
    indent_left: float = 0.0  # в пунктах
    indent_right: float = 0.0
    indent_first_line: float = 0.0
    space_before: float = 0.0
    space_after: float = 0.0
    page_number: int = 1
    has_page_break_before: bool = False
    is_list_item: bool = False
    list_level: Optional[int] = None
    list_type: Optional[str] = None  # 'bullet' or 'number'
    raw_xml_id: Optional[str] = None


@dataclass
class Heading(Paragraph):
    """Представление заголовка."""
    level: int = 1  # 1-6 уровни заголовков
    numbering: Optional[str] = None  # например: "1.", "1.1", "Глава 1"
    is_numbered: bool = False


@dataclass
class TableCell:
    """Ячейка таблицы."""
    text: str
    row_span: int = 1
    col_span: int = 1
    paragraph_count: int = 0


@dataclass
class Table:
    """Представление таблицы."""
    rows: int
    columns: int
    caption: Optional[str] = None
    caption_position: str = "top"  # top или bottom
    page_number: int = 1
    table_number: Optional[int] = None
    style_name: Optional[str] = None
    cells: List[List[TableCell]] = field(default_factory=list)
    raw_cells: List[List[str]] = field(default_factory=list)


@dataclass
class Figure:
    """Представление рисунка/иллюстрации."""
    caption: Optional[str] = None
    caption_position: str = "bottom"  # обычно снизу
    figure_type: str = "image"  # image, formula, diagram
    page_number: int = 1
    figure_number: Optional[int] = None
    description: str = ""  # Текст подписи без номера
    width: Optional[float] = None
    height: Optional[float] = None
    width_emu: Optional[int] = None
    height_emu: Optional[int] = None
    image_type: Optional[str] = None


@dataclass
class Formula:
    """Представление математической формулы."""
    omml_xml: str
    latex: Optional[str] = None
    formula_number: Optional[str] = None
    page_number: int = 1


@dataclass
class Reference:
    """Представление библиографической ссылки."""
    text: str
    reference_type: str = "gost"  # gost, apa, mla
    ref_type: ReferenceType = ReferenceType.BRACKETED
    position: str = "inline"  # inline, footnote, endnote
    numbers: List[int] = field(default_factory=list)  # Номера источников [1, 2, 3]
    number: Optional[int] = None  # Для обратной совместимости
    cited_page: Optional[int] = None  # Страница цитирования
    page_number: int = 1
    start_index: int = 0
    end_index: int = 0


@dataclass
class BibliographyEntry:
    """Элемент списка литературы."""
    index: int  # Порядковый номер в списке
    authors: List[str] = field(default_factory=list)
    title: str = ""
    publication_info: str = ""  # Город: Издательство, Год
    pages: Optional[str] = None  # Диапазон страниц
    url: Optional[str] = None
    access_date: Optional[str] = None
    raw_text: str = ""
    entry_type: Optional[str] = None  # book, article, web, etc.


@dataclass
class Appendix:
    """Приложение к документу."""
    letter: str  # А, Б, В...
    title: str
    content: List[Paragraph] = field(default_factory=list)
    page_start: Optional[int] = None


@dataclass
class DocumentMetadata:
    """Метаданные документа."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    # Поля страницы (в см)
    margin_top_cm: float = 2.0
    margin_bottom_cm: float = 2.0
    margin_left_cm: float = 3.0
    margin_right_cm: float = 1.0
    page_width_cm: float = 21.0  # A4
    page_height_cm: float = 29.7


@dataclass
class DocumentContent:
    """Структурированное представление документа."""
    paragraphs: List[Paragraph] = field(default_factory=list)
    headings: List[Heading] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    formulas: List[Formula] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    bibliography: List[BibliographyEntry] = field(default_factory=list)
    appendices: List[Appendix] = field(default_factory=list)
    
    # Метаданные
    total_pages: int = 0
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    
    # Дополнительные данные
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Сводная статистика
    char_count_no_spaces: int = 0
    char_count_with_spaces: int = 0
    word_count: int = 0
    
    def get_headings_by_level(self, level: int) -> List[Heading]:
        """Получить заголовки определенного уровня."""
        return [h for h in self.headings if h.level == level]
    
    def get_tables_on_page(self, page: int) -> List[Table]:
        """Получить таблицы на странице."""
        return [t for t in self.tables if t.page_number == page]
    
    def get_figures_on_page(self, page: int) -> List[Figure]:
        """Получить рисунки на странице."""
        return [f for f in self.figures if f.page_number == page]


class DocumentLoader(ABC):
    """Абстрактный базовый класс для загрузчиков документов."""
    
    @abstractmethod
    def load(self, file_path: str | Path) -> DocumentContent:
        """
        Загрузить документ из файла.
        
        Args:
            file_path: Путь к файлу документа
            
        Returns:
            DocumentContent: Структурированное содержимое документа
            
        Raises:
            FileNotFoundError: Файл не найден
            ValueError: Неподдерживаемый формат файла
        """
        pass
    
    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """
        Проверить поддержку формата файла.
        
        Args:
            file_extension: Расширение файла (например, '.docx')
            
        Returns:
            bool: True если формат поддерживается
        """
        pass


class DOCXLoader(DocumentLoader):
    """Загрузчик документов формата DOCX."""
    
    def supports_format(self, file_extension: str) -> bool:
        """Проверка поддержки формата DOCX."""
        return file_extension.lower() in ['.docx', '.doc']
    
    def load(self, file_path: str | Path) -> DocumentContent:
        """
        Загрузить документ DOCX.
        
        Args:
            file_path: Путь к файлу DOCX
            
        Returns:
            DocumentContent: Структурированное содержимое документа
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        if not self.supports_format(path.suffix):
            raise ValueError(f"Неподдерживаемый формат: {path.suffix}")
        
        # Вызов парсера DOCX
        from .docx_parser import DOCXParser
        parser = DOCXParser()
        return parser.parse(file_path)


class PDFLoader(DocumentLoader):
    """Загрузчик документов формата PDF."""
    
    def supports_format(self, file_extension: str) -> bool:
        """Проверка поддержки формата PDF."""
        return file_extension.lower() == '.pdf'
    
    def load(self, file_path: str | Path) -> DocumentContent:
        """
        Загрузить документ PDF.
        
        Пока заглушка - будет реализована после написания тестов.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        if not self.supports_format(path.suffix):
            raise ValueError(f"Неподдерживаемый формат: {path.suffix}")
        
        # TODO: Реализация парсинга PDF
        content = DocumentContent(
            file_path=str(path),
            file_name=path.name
        )
        return content


def get_loader(file_path: str | Path) -> DocumentLoader:
    """
    Получить подходящий загрузчик для файла.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        DocumentLoader: Подходящий загрузчик
        
    Raises:
        ValueError: Если формат не поддерживается
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    loaders = [DOCXLoader(), PDFLoader()]
    
    for loader in loaders:
        if loader.supports_format(extension):
            return loader
    
    raise ValueError(f"Неподдерживаемый формат файла: {extension}")


def load_document(file_path: str | Path) -> DocumentContent:
    """
    Удобная функция для загрузки документа.
    
    Args:
        file_path: Путь к файлу документа
        
    Returns:
        DocumentContent: Структурированное содержимое
    """
    loader = get_loader(file_path)
    return loader.load(file_path)
