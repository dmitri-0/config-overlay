from PySide6.QtWidgets import QMainWindow, QPlainTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QTextCursor

class OverlayWindow(QMainWindow):
    on_save = Signal(str)   # Сохранить и вставить
    on_cancel = Signal()    # Просто скрыть окно
    on_exit_app = Signal()  # ПОЛНЫЙ ВЫХОД из приложения

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.apply_style()
        
        self.editor = QPlainTextEdit()
        font = QFont("JetBrains Mono", 14)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.setCentralWidget(self.editor)

        # --- Хоткеи ---
        # 1. F12 - Сохранить
        QShortcut(QKeySequence("F12"), self).activated.connect(self._save)
        # 2. Esc - Отмена (скрыть)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._cancel)
        # 3. Shift + Esc - Полный выход
        QShortcut(QKeySequence("Shift+Esc"), self).activated.connect(self._exit_full)

    def open_with_text(self, text):
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
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: none;
                padding: 20px;
            }
        """)
