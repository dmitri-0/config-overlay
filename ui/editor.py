# ui/editor.py
"""
Пример интеграции подсветки синтаксиса 1С в редактор.
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QShortcut, QKeySequence, QTextCursor, QKeyEvent

import re

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

        # Автоматическое сворачивание
        self._method_ranges = []
        self._folding_timer = QTimer()
        self._folding_timer.setSingleShot(True)
        self._folding_timer.setInterval(200) # Задержка для оптимизации
        self._folding_timer.timeout.connect(self._perform_scan_and_fold)

        self.editor.textChanged.connect(self._schedule_folding_update)
        self.editor.cursorPositionChanged.connect(self._on_cursor_position_changed)
        
        # Регулярки для поиска методов
        self._re_proc_start = re.compile(r'^\s*(Процедура|Функция|Procedure|Function)\s+', re.IGNORECASE)
        self._re_proc_end = re.compile(r'^\s*(КонецПроцедуры|КонецФункции|EndProcedure|EndFunction)', re.IGNORECASE)
        self._re_comment = re.compile(r'^\s*//')

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
            color_scheme (str): 'dark' или 'light'
        """
        scheme = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES['dark'])
        self.highlighter = OneCHighlighter(
            parent=self.editor.document(),
            color_scheme=scheme
        )
    
    def _setup_shortcuts(self):
        """Настройка горячих клавиш"""
        # F12 - Сохранить
        QShortcut(QKeySequence("F12"), self).activated.connect(self._save)
        # Esc - Отмена
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._cancel)
        # Shift + Esc - Полный выход
        QShortcut(QKeySequence("Shift+Esc"), self).activated.connect(self._exit_full)
        # Alt + Up - Предыдущий метод
        QShortcut(QKeySequence("Alt+Up"), self).activated.connect(self._navigate_to_previous_method)
        # Alt + Down - Следующий метод
        QShortcut(QKeySequence("Alt+Down"), self).activated.connect(self._navigate_to_next_method)

    def open_with_text(self, text):
        """Открыть редактор с текстом"""
        self.editor.setPlainText(text)
        self.showFullScreen()
        self.activateWindow()
        self.editor.setFocus()
        
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)
        
        # Принудительное обновление сворачивания при открытии
        if self.settings.auto_fold_methods:
             self._perform_scan_and_fold()

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
            
        if 'auto_fold_methods' in kwargs:
            if self.settings.auto_fold_methods:
                self._perform_scan_and_fold()
            else:
                self._unfold_all()
        
        # Сохраняем настройки
        save_settings()

    # --- Method Navigation ---
    
    def _navigate_to_previous_method(self):
        """Переход к началу предыдущего метода (Alt+Up)."""
        # Обновляем список методов, если нужно
        if not self._method_ranges:
            self._scan_methods()
        
        if not self._method_ranges:
            return  # Нет методов
        
        current_line = self.editor.textCursor().blockNumber()
        
        # Ищем предыдущий метод
        target_line = None
        for m_range in reversed(self._method_ranges):
            # Ищем метод, чья сигнатура находится строго выше текущей позиции
            if m_range['sig'] < current_line:
                target_line = m_range['sig']
                break
        
        if target_line is not None:
            self._move_cursor_to_line_start(target_line)
            self._scroll_to_top(target_line)
    
    def _navigate_to_next_method(self):
        """Переход к началу следующего метода (Alt+Down)."""
        # Обновляем список методов, если нужно
        if not self._method_ranges:
            self._scan_methods()
        
        if not self._method_ranges:
            return  # Нет методов
        
        current_line = self.editor.textCursor().blockNumber()
        
        # Ищем следующий метод
        target_line = None
        for m_range in self._method_ranges:
            # Ищем метод, чья сигнатура находится строго ниже текущей позиции
            if m_range['sig'] > current_line:
                target_line = m_range['sig']
                break
        
        if target_line is not None:
            self._move_cursor_to_line_start(target_line)
            self._scroll_to_top(target_line)
    
    def _move_cursor_to_line_start(self, line_number):
        """Установить курсор в начало указанной строки."""
        cursor = self.editor.textCursor()
        
        # Переходим к началу указанной строки
        block = self.editor.document().findBlockByNumber(line_number)
        if block.isValid():
            cursor.setPosition(block.position())
            cursor.movePosition(QTextCursor.StartOfLine)
            self.editor.setTextCursor(cursor)
    
    def _scroll_to_top(self, line_number):
        """Прокрутить редактор так, чтобы указанная строка стала первой видимой строкой."""
        doc = self.editor.document()
        block = doc.findBlockByNumber(line_number)
        if not block.isValid():
            return

        # Для QPlainTextEdit самый надежный способ: вычислить, где блок находится сейчас
        # относительно верхнего края viewport, и сдвинуть scrollbar на эту величину.
        def _do_scroll():
            y = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            sb = self.editor.verticalScrollBar()
            sb.setValue(sb.value() + int(y))

        _do_scroll()
        # Повторяем на следующем цикле событий, чтобы учесть пересчет layout/visibility после смены курсора (auto_fold_methods).
        QTimer.singleShot(0, _do_scroll)

    # --- Logic for Auto Folding ---

    def _schedule_folding_update(self):
        """Запланировать обновление структуры методов при изменении текста."""
        if self.settings.auto_fold_methods:
            self._folding_timer.start()

    def _on_cursor_position_changed(self):
        """Обработка перемещения курсора."""
        if self.settings.auto_fold_methods:
            self._apply_visibility()

    def _perform_scan_and_fold(self):
        """Сканирование методов и применение фолдинга."""
        self._scan_methods()
        self._apply_visibility()

    def _scan_methods(self):
        """Проход по документу и поиск границ методов."""
        self._method_ranges = []
        
        doc = self.editor.document()
        block = doc.begin()
        
        current_comments_start = -1
        
        while block.isValid():
            text = block.text()
            block_num = block.blockNumber()
            
            # Проверка на комментарий
            if self._re_comment.match(text):
                if current_comments_start == -1:
                    current_comments_start = block_num
            elif not text.strip():
                # Пустая строка - не сбрасываем начало комментариев, если они есть?
                # Или считаем разделителем? Обычно пустая строка разрывает блок комментов метода.
                current_comments_start = -1
            else:
                # Проверка на начало метода
                if self._re_proc_start.match(text):
                    # Нашли начало метода
                    start_fold = current_comments_start if current_comments_start != -1 else block_num
                    sig_line = block_num
                    
                    # Ищем конец метода
                    # (Упрощенно: ищем следующий EndProcedure без учета вложенности, 
                    # т.к. в 1С методы не вкладываются, кроме как в ОпределитьТип/etc в выражениях, но они не начинаются с начала строки обычно)
                    
                    # Запоминаем начало и ищем конец
                    search_block = block.next()
                    while search_block.isValid():
                        s_text = search_block.text()
                        if self._re_proc_end.match(s_text):
                            end_line = search_block.blockNumber()
                            
                            self._method_ranges.append({
                                'start': start_fold,   # Начало (включая комменты)
                                'sig': sig_line,       # Строка сигнатуры (всегда видна, если метод не текущий)
                                'end': end_line        # Конец метода
                            })
                            
                            block = search_block # Перемещаем основной итератор
                            break
                        
                        # Защита от вложенных начал (если вдруг парсинг сбился)
                        if self._re_proc_start.match(s_text):
                            # Наткнулись на начало следующего? 
                            # Значит предыдущий не закрыт или ошибка. 
                            # Считаем текущий search_block началом нового.
                            # Откатываемся
                            block = search_block.previous() 
                            break
                            
                        search_block = search_block.next()
                    
                    # Сброс комментов после обработки метода
                    current_comments_start = -1
                    
                else:
                    # Какой-то другой код, сбрасываем комменты
                    current_comments_start = -1
            
            block = block.next()

    def _apply_visibility(self):
        """Применение видимости блоков на основе положения курсора."""
        cursor_block_num = self.editor.textCursor().blockNumber()
        doc = self.editor.document()
        
        # Определяем, в каком мы методе
        current_method_index = -1
        for i, m_range in enumerate(self._method_ranges):
            # Курсор внутри диапазона [start, end]?
            if m_range['start'] <= cursor_block_num <= m_range['end']:
                current_method_index = i
                break
        
        # Применяем видимость
        for i, m_range in enumerate(self._method_ranges):
            is_current = (i == current_method_index)
            
            # Блоки комментариев (до сигнатуры)
            for b_num in range(m_range['start'], m_range['sig']):
                block = doc.findBlockByNumber(b_num)
                if block.isVisible() != is_current:
                    block.setVisible(is_current)
            
            # Сигнатура - всегда видна
            sig_block = doc.findBlockByNumber(m_range['sig'])
            if not sig_block.isVisible():
                 sig_block.setVisible(True)
            
            # Тело метода (после сигнатуры до конца включительно? или EndProcedure виден?)
            # Обычно EndProcedure скрывают, чтобы было "ProcName..."
            # Но если скрываем, то сворачивается в одну строку.
            for b_num in range(m_range['sig'] + 1, m_range['end'] + 1):
                block = doc.findBlockByNumber(b_num)
                if block.isVisible() != is_current:
                    block.setVisible(is_current)
                    
        # Вызываем пересчет геометрии редактора (иногда нужно для line numbers)
        self.editor.viewport().update()
        self.editor.update_line_number_area_width(0)

    def _unfold_all(self):
        """Развернуть всё."""
        doc = self.editor.document()
        block = doc.begin()
        while block.isValid():
            if not block.isVisible():
                block.setVisible(True)
            block = block.next()
        self.editor.update_line_number_area_width(0)
