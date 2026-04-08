"""
Модуль с правилами валидации для Контура А.
Правила основаны на ГОСТ и методических указаниях ИГУ.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Callable


class RuleSeverity(Enum):
    """Уровень критичности нарушения."""
    ERROR = "error"       # Критическое нарушение
    WARNING = "warning"   # Предупреждение
    INFO = "info"         # Информационное сообщение


class RuleCategory(Enum):
    """Категория правила."""
    STRUCTURE = "structure"      # Структура документа
    FORMATTING = "formatting"    # Форматирование текста
    REFERENCES = "references"    # Список литературы
    TABLES_FIGURES = "tables_figures"  # Таблицы и рисунки
    HEADINGS = "headings"        # Заголовки
    PAGE_FORMAT = "page_format"  # Параметры страницы


@dataclass
class ValidationResult:
    """Результат проверки одного правила."""
    rule_id: str
    rule_name: str
    passed: bool
    severity: RuleSeverity
    category: RuleCategory
    message: str
    location: Optional[str] = None  # Например: "страница 5, строка 12"
    suggestion: Optional[str] = None  # Рекомендация по исправлению


@dataclass
class Rule:
    """Описание правила валидации."""
    id: str
    name: str
    description: str
    severity: RuleSeverity
    category: RuleCategory
    check_function: Callable  # Функция проверки


# Реестр правил (будет заполняться по мере реализации)
RULES_REGISTRY: List[Rule] = []


def register_rule(rule_id: str, name: str, description: str, 
                  severity: RuleSeverity, category: RuleCategory):
    """Декоратор для регистрации правила."""
    def decorator(func: Callable):
        rule = Rule(
            id=rule_id,
            name=name,
            description=description,
            severity=severity,
            category=category,
            check_function=func
        )
        RULES_REGISTRY.append(rule)
        return func
    return decorator
