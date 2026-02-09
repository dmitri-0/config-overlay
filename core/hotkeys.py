import keyboard
from PySide6.QtCore import QObject, Signal

class HotkeyListener(QObject):
    # Оставляем только сигнал активации
    triggered_edit = Signal()

    def __init__(self):
        super().__init__()
        self._is_listening = False

    def start(self):
        if self._is_listening: return
        
        # Только глобальный хук для вызова
        keyboard.add_hotkey('ctrl+shift+f12', self.triggered_edit.emit)
        self._is_listening = True

    def stop(self):
        if self._is_listening:
            keyboard.unhook_all()
            self._is_listening = False
