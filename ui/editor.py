# ui/editor_with_highlighter.py
"""
Пример интеграции подсветки синтаксиса 1С в редактор.
"""

from PySide6.QtWidgets import QMainWindow, QPlainTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QTextCursor

from ui.styles import EditorStyles
from ui.syntax_highlighter import OneCHighlighter, COLOR_SCHEMES


class OverlayWindow(QMainWindow):
    """
    Редактор с подсветкой синтаксиса 1С.
    """
    on_save = Signal(str)   # Сохранить и вставить
    on_cancel = Signal()    # Просто скрыть окно
    on_exit_app = Signal()  # ПОЛНЫЙ ВЫХОД из приложения

    def __init__(self, enable_highlighting=True, color_scheme='high_contrast_dark'):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.apply_style()
        
        # Создаем редактор
        self.editor = QPlainTextEdit()
        font = QFont(
            EditorStyles.get_font_family(),
            EditorStyles.get_font_size()
        )
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.setCentralWidget(self.editor)

        # Подсветка синтаксиса
        self.highlighter = None
        if enable_highlighting:
            self._setup_syntax_highlighter(color_scheme)

        # Хоткеи
        self._setup_shortcuts()

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
