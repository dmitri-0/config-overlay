# ui/editor_with_highlighter.py
"""
Пример интеграции подсветки синтаксиса 1С в редактор.
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QTextCursor, QKeyEvent

from ui.styles import EditorStyles
from ui.syntax_highlighter import OneCHighlighter, COLOR_SCHEMES
from ui.line_numbers import CodeEditor
from core.settings import get_settings, save_settings


class OverlayWindow(QMainWindow):
    """
    Редактор с подсветкой синтаксиса 1С.
    """
    on_save = Signal(str)   # Сохранить и вставить
    on_cancel = Signal()    # Просто скрыть окно
    on_exit_app = Signal()  # ПОЛНЫЙ ВЫХОД из приложения

    def __init__(self, enable_highlighting=None, color_scheme=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.apply_style()
        
        # Загружаем настройки
        self.settings = get_settings()
        
        # Используем параметры или настройки
        if enable_highlighting is None:
            enable_highlighting = self.settings.enable_highlighting
        if color_scheme is None:
            color_scheme = self.settings.color_scheme
        
        # Создаем редактор с номерами строк
        self.editor = CodeEditor()
        self.editor.set_show_line_numbers(self.settings.show_line_numbers)
        
        # Настройка шрифта
        font = QFont(
            EditorStyles.get_font_family(),
            self.settings.font_size
        )
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        
        # Настройка табуляции
        self.editor.setTabStopDistance(
            self.editor.fontMetrics().horizontalAdvance(' ') * self.settings.tab_width
        )
        
        self.setCentralWidget(self.editor)

        # Подсветка синтаксиса
        self.highlighter = None
        if enable_highlighting:
            self._setup_syntax_highlighter(color_scheme)

        # Хоткеи
        self._setup_shortcuts()
        
        # Перехват нажатия клавиш для замены табов
        self.editor.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Перехват событий для замены табов на пробелы."""
        if obj == self.editor and event.type() == QKeyEvent.KeyPress:
            if event.key() == Qt.Key_Tab and self.settings.replace_tabs_with_spaces:
                # Заменяем таб на пробелы
                cursor = self.editor.textCursor()
                cursor.insertText(' ' * self.settings.tab_width)
                return True
        return super().eventFilter(obj, event)

    def _setup_syntax_highlighter(self, color_scheme='dark'):
        """
        Настройка подсветки синтаксиса.
        
        Args:
            color_scheme (str): 'даrk' или 'light'
        """
        scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['dark'])
        self.highlighter = OneCHighlighter(
            parent=self.editor.document(),
            color_scheme=scheme
        )
    
    def _setup_shortcuts(self):
        """uНастройка горячих клавиш"""
        # F12 - Сохранить
        QShortcut(QKeySequence("F12"), self).activated.connect(self._save)
        # Esc - Отмена
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._cancel)
        # Shift + Esc - Полный выход
        QShortcut(QKeySequence("Shift+Esc"), self).activated.connect(self._exit_full)

    def open_with_text(self, text):
        """Открыть редактор с текстом"""
        self.editor.setPlainText(text)
        self.showFullScreen()
        self.activateWindow()
        self.editor.setFocus()
        
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)

    def _save(self):
        self.hide()
        self.on_save.emit(self.editor.toPlainText())

    def _cancel(self):
        self.hide()
        self.on_cancel.emit()

    def _exit_full(self):
        self.hide()
        self.on_exit_app.emit()

    def apply_style(self):
        self.setStyleSheet(EditorStyles.get_editor_stylesheet())
    
    def toggle_highlighting(self, enabled=True):
        """
        Включить/выключить подсветку синтаксиса.
        
        Args:
            enabled (bool): True - включить, False - выключить
        """
        if enabled and not self.highlighter:
            self._setup_syntax_highlighter()
        elif not enabled and self.highlighter:
            self.highlighter.setDocument(None)
            self.highlighter = None
    
    def change_color_scheme(self, color_scheme='dark'):
        """
        Изменить цветовую схему подсветки.
        
        Args:
            color_scheme (str): 'dark' или 'light'
        """
        if self.highlighter:
            scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['dark'])
            self.highlighter.set_color_scheme(scheme)
    
    def update_settings(self, **kwargs):
        """
        Обновить настройки редактора.
        
        Примеры:
            update_settings(show_line_numbers=False)
            update_settings(tab_width=3, replace_tabs_with_spaces=True)
        """
        self.settings.update(**kwargs)
        
        # Применяем изменения
        if 'show_line_numbers' in kwargs:
            self.editor.set_show_line_numbers(self.settings.show_line_numbers)
        
        if 'tab_width' in kwargs:
            self.editor.setTabStopDistance(
                self.editor.fontMetrics().horizontalAdvance(' ') * self.settings.tab_width
            )
        
        if 'font_size' in kwargs:
            font = self.editor.font()
            font.setPointSize(self.settings.font_size)
            self.editor.setFont(font)
        
        if 'color_scheme' in kwargs and self.highlighter:
            self.change_color_scheme(self.settings.color_scheme)
        
        if 'enable_highlighting' in kwargs:
            self.toggle_highlighting(self.settings.enable_highlighting)
        
        # Сохраняем настройки
        save_settings()
