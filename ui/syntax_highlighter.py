# ui/syntax_highlighter.py
"""
Подсветка синтаксиса 1С (BSL) для QPlainTextEdit.
Использует Pygments для лексического анализа и QSyntaxHighlighter для рендеринга.

Основан на реализации Spyder IDE:
https://github.com/spyder-ide/spyder/blob/master/spyder/utils/syntaxhighlighters.py
"""

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt
import re

try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name
    from pygments.token import (
        Token, Keyword, Name, Comment, String, Number, Operator,
        Punctuation, Literal, Error, Whitespace, Text
    )
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class OneCHighlighter(QSyntaxHighlighter):
    """
    Подсветка синтаксиса 1С:Enterprise (BSL) на основе Pygments.
    
    Для работы требует установки: pip install pygments-bsl
    
    Особенности:
    - Асинхронная подсветка через QSyntaxHighlighter (не блокирует UI)
    - Гибкая настройка цветовой схемы
    - Поддержка комментариев, строк, ключевых слов, функций
    - Автоматическое определение контекста через Pygments
    - Обработка многострочных строк
    """
    
    def __init__(self, parent=None, color_scheme=None):
        super().__init__(parent)
        
        # Цветовая схема по умолчанию (темная тема)
        self.color_scheme = color_scheme or self._get_default_color_scheme()
        
        # Инициализация форматов
        self.formats = {}
        self._setup_formats()
        
        # Pygments лексер для 1С
        self.lexer = None
        if PYGMENTS_AVAILABLE:
            try:
                # Попытка использовать BSL лексер из pygments-bsl
                self.lexer = get_lexer_by_name('bsl')
            except:
                raise RuntimeError("pygments-bsl не установлен. Установите: pip install pygments-bsl")
        else:
            raise RuntimeError("Pygments не установлен. Установите: pip install Pygments pygments-bsl")
    
    def _get_default_color_scheme(self):
        """Цветовая схема по умолчанию (темная тема в стиле VS Code)"""
        return {
            'keyword': ('#569CD6', True, False),      # Синие жирные
            'builtin': ('#4EC9B0', False, False),     # Бирюзовые
            'function': ('#DCDCAA', False, False),    # Желтоватые
            'comment': ('#6A9955', False, False),     # Зеленые БЕЗ курсива
            'string': ('#CE9178', False, False),      # Оранжевые
            'number': ('#B5CEA8', False, False),      # Светло-зеленые
            'directive': ('#C586C0', False, False),   # Фиолетовые (#Если, #Тогда)
            'operator': ('#D4D4D4', False, False),    # Белые
            'error': ('#F44747', False, False),       # Красные
            'normal': ('#D4D4D4', False, False),      # Белый текст
        }
    
    def _setup_formats(self):
        """Создание QTextCharFormat для каждого типа токена"""
        for name, (color, bold, italic) in self.color_scheme.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            
            if bold:
                fmt.setFontWeight(QFont.Bold)
            if italic:
                fmt.setFontItalic(True)
            
            self.formats[name] = fmt
    
    def highlightBlock(self, text):
        """
        Основной метод подсветки блока текста.
        Вызывается автоматически QSyntaxHighlighter для каждой строки.
        """
        if not text:
            return
        
        # Устанавливаем базовый формат
        self.setFormat(0, len(text), self.formats['normal'])
        
        if self.lexer and PYGMENTS_AVAILABLE:
            # Использование Pygments для точной подсветки
            self._highlight_with_pygments(text)
    
    def _highlight_with_pygments(self, text):
        """
        Подсветка с использованием Pygments (более точная и полная).
        """
        try:
            # Получаем токены от Pygments
            tokens = list(lex(text, self.lexer))
            
            # Применяем форматирование для каждого токена
            offset = 0
            for token_type, token_value in tokens:
                length = len(token_value)
                
                # Определяем формат для токена
                fmt = self._get_format_for_token(token_type)
                if fmt:
                    self.setFormat(offset, length, fmt)
                
                offset += length
        except Exception as e:
            # В случае ошибки просто не подсвечиваем
            pass
    
    def _get_format_for_token(self, token_type):
        """
        Сопоставление типов токенов Pygments с нашими форматами.
        """
        # Комментарии (БЕЗ курсива для единообразия)
        if token_type in Comment:
            return self.formats['comment']
        
        # Ключевые слова
        if token_type in Keyword:
            return self.formats['keyword']
        
        # Строки (включая многострочные)
        if token_type in String or token_type in Literal.String:
            return self.formats['string']
        
        # Числа
        if token_type in Number or token_type in Literal.Number:
            return self.formats['number']
        
        # Функции и имена
        if token_type in Name.Function:
            return self.formats['function']
        
        if token_type in Name.Builtin:
            return self.formats['builtin']
        
        # Операторы
        if token_type in Operator or token_type in Punctuation:
            return self.formats['operator']
        
        # Ошибки
        if token_type in Error:
            return self.formats['error']
        
        return None
    
    def set_color_scheme(self, color_scheme):
        """
        Изменение цветовой схемы.
        
        Args:
            color_scheme (dict): Словарь формата
                {'keyword': (color, bold, italic), ...}
        """
        self.color_scheme = color_scheme
        self._setup_formats()
        self.rehighlight()  # Перерисовка всего документа
    
    def get_color_scheme(self):
        """Получение текущей цветовой схемы"""
        return self.color_scheme


# Предустановленные цветовые схемы
COLOR_SCHEMES = {
    'dark': {
        'keyword': ('#569CD6', True, False),
        'builtin': ('#4EC9B0', False, False),
        'function': ('#DCDCAA', False, False),
        'comment': ('#6A9955', False, False),  # БЕЗ курсива
        'string': ('#CE9178', False, False),
        'number': ('#B5CEA8', False, False),
        'directive': ('#C586C0', False, False),
        'operator': ('#D4D4D4', False, False),
        'error': ('#F44747', False, False),
        'normal': ('#D4D4D4', False, False),
    },
    'light': {
        'keyword': ('#0000FF', True, False),
        'builtin': ('#267F99', False, False),
        'function': ('#795E26', False, False),
        'comment': ('#008000', False, False),  # БЕЗ курсива
        'string': ('#A31515', False, False),
        'number': ('#098658', False, False),
        'directive': ('#AF00DB', False, False),
        'operator': ('#000000', False, False),
        'error': ('#FF0000', False, False),
        'normal': ('#000000', False, False),
    },
}
