"""
TDD: Тесты для модуля правил валидации.
Сначала пишем тесты (красный этап), затем реализуем функционал.
"""
import pytest
from validators.rules import (
    RuleSeverity, 
    RuleCategory, 
    ValidationResult, 
    Rule,
    RULES_REGISTRY,
    register_rule
)


class TestRuleSeverity:
    """Тесты перечисления уровней критичности."""
    
    def test_severity_values(self):
        """Проверка наличия всех уровней критичности."""
        assert RuleSeverity.ERROR.value == "error"
        assert RuleSeverity.WARNING.value == "warning"
        assert RuleSeverity.INFO.value == "info"
    
    def test_severity_count(self):
        """Проверка количества уровней критичности."""
        assert len(RuleSeverity) == 3


class TestRuleCategory:
    """Тесты перечисления категорий правил."""
    
    def test_category_values(self):
        """Проверка наличия всех категорий."""
        assert RuleCategory.STRUCTURE.value == "structure"
        assert RuleCategory.FORMATTING.value == "formatting"
        assert RuleCategory.REFERENCES.value == "references"
        assert RuleCategory.TABLES_FIGURES.value == "tables_figures"
        assert RuleCategory.HEADINGS.value == "headings"
        assert RuleCategory.PAGE_FORMAT.value == "page_format"
    
    def test_category_count(self):
        """Проверка количества категорий."""
        assert len(RuleCategory) == 6


class TestValidationResult:
    """Тесты результата валидации."""
    
    def test_create_validation_result_minimal(self):
        """Создание результата с минимальными полями."""
        result = ValidationResult(
            rule_id="FONT_001",
            rule_name="Размер шрифта",
            passed=True,
            severity=RuleSeverity.ERROR,
            category=RuleCategory.FORMATTING,
            message="Шрифт соответствует требованиям"
        )
        assert result.rule_id == "FONT_001"
        assert result.passed is True
        assert result.location is None
        assert result.suggestion is None
    
    def test_create_validation_result_full(self):
        """Создание результата со всеми полями."""
        result = ValidationResult(
            rule_id="MARGIN_001",
            rule_name="Поля страницы",
            passed=False,
            severity=RuleSeverity.ERROR,
            category=RuleCategory.PAGE_FORMAT,
            message="Левое поле меньше требуемого",
            location="страница 5",
            suggestion="Установите левое поле 30 мм"
        )
        assert result.passed is False
        assert result.location == "страница 5"
        assert result.suggestion == "Установите левое поле 30 мм"


class TestRule:
    """Тесты правила валидации."""
    
    def test_create_rule(self):
        """Создание правила валидации."""
        def dummy_check(doc):
            return True
        
        rule = Rule(
            id="FONT_001",
            name="Размер шрифта основного текста",
            description="Шрифт должен быть 14pt",
            severity=RuleSeverity.ERROR,
            category=RuleCategory.FORMATTING,
            check_function=dummy_check
        )
        assert rule.id == "FONT_001"
        assert rule.name == "Размер шрифта основного текста"
        assert rule.severity == RuleSeverity.ERROR


class TestRuleRegistry:
    """Тесты реестра правил."""
    
    def test_registry_initial_state(self):
        """Проверка начального состояния реестра."""
        # Реестр должен быть списком
        assert isinstance(RULES_REGISTRY, list)
    
    def test_register_rule_decorator(self):
        """Тест декоратора регистрации правила."""
        initial_count = len(RULES_REGISTRY)
        
        @register_rule(
            rule_id="TEST_001",
            name="Тестовое правило",
            description="Описание теста",
            severity=RuleSeverity.INFO,
            category=RuleCategory.STRUCTURE
        )
        def test_check(doc):
            return True
        
        assert len(RULES_REGISTRY) == initial_count + 1
        registered_rule = RULES_REGISTRY[-1]
        assert registered_rule.id == "TEST_001"
        assert registered_rule.name == "Тестовое правило"
        assert registered_rule.severity == RuleSeverity.INFO
