"""
Модуль загрузки и парсинга документов для Контура А.
Поддерживает форматы: DOCX, PDF
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class Paragraph:
    """Представление абзаца текста."""
    text: str
    style_name: Optional[str] = None
    font_size: Optional[float] = None  # в пунктах
    font_name: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False
    alignment: Optional[str] = None  # left, center, right, justify
    line_spacing: Optional[float] = None
    indent_left: Optional[float] = None  # в пунктах
    indent_right: Optional[float] = None
    indent_first_line: Optional[float] = None  # в пунктах
    page_number: int = 1


@dataclass
class Heading(Paragraph):
    """Представление заголовка."""
    level: int = 1  # 1-6 уровни заголовков
    numbering: Optional[str] = None  # например: "1.", "1.1", "Глава 1"


@dataclass
class Table:
    """Представление таблицы."""
    rows: int
    columns: int
    caption: Optional[str] = None
    caption_position: str = "top"  # top или bottom
    page_number: int = 1
    cells: List[List[str]] = field(default_factory=list)


@dataclass
class Figure:
    """Представление рисунка/иллюстрации."""
    caption: Optional[str] = None
    caption_position: str = "bottom"  # обычно снизу
    figure_type: str = "image"  # image, formula, diagram
    page_number: int = 1
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class Reference:
    """Представление библиографической ссылки."""
    text: str
    reference_type: str = "gost"  # gost, apa, mla
    position: str = "inline"  # inline, footnote, endnote
    number: Optional[int] = None
    page_number: int = 1


@dataclass
class DocumentContent:
    """Структурированное представление документа."""
    paragraphs: List[Paragraph] = field(default_factory=list)
    headings: List[Heading] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    
    # Метаданные
    total_pages: int = 0
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    
    # Дополнительные данные
    metadata: Dict[str, Any] = field(default_factory=dict)


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
        
        Пока заглушка - будет реализована после написания тестов.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        if not self.supports_format(path.suffix):
            raise ValueError(f"Неподдерживаемый формат: {path.suffix}")
        
        # TODO: Реализация парсинга DOCX
        content = DocumentContent(
            file_path=str(path),
            file_name=path.name
        )
        return content


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
