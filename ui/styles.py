# ui/styles.py
"""
Модуль стилей и цветовых схем для Config Overlay.
Содержит все CSS-стили и константы цветов.
"""

class ColorScheme:
    """Цветовая схема Dark Theme"""
    BACKGROUND = "#1e1e1e"
    TEXT = "#dcdcdc"
    BORDER = "none"
    PADDING = "20px"


class EditorStyles:
    """Стили для редактора"""
    
    @staticmethod
    def get_editor_stylesheet(scheme=ColorScheme):
        """Возвращает QSS-стиль для редактора"""
        return f"""
            QPlainTextEdit {{
                background-color: {scheme.BACKGROUND};
                color: {scheme.TEXT};
                border: {scheme.BORDER};
                padding: {scheme.PADDING};
            }}
        """
    
    @staticmethod
    def get_font_family():
        """Возвращает название шрифта"""
        return "JetBrains Mono"
    
    @staticmethod
    def get_font_size():
        """Возвращает размер шрифта"""
        return 14
