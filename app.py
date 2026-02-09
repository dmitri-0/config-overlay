import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Slot

from ui.editor import OverlayWindow
from core.automation import Automation
from core.hotkeys import HotkeyListener

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.window = OverlayWindow()
        self.hotkeys = HotkeyListener()
        self.last_hwnd = None

        self._connect_signals()
        self.hotkeys.start()

    def _connect_signals(self):
        # Глобальный хук -> Открыть редактор
        self.hotkeys.triggered_edit.connect(self.start_edit)
        
        # Сигналы от окна
        self.window.on_save.connect(self.finish_edit)
        self.window.on_cancel.connect(self.cancel_edit)
        # Подключаем новый сигнал полного выхода
        self.window.on_exit_app.connect(self.close_app)

    @Slot()
    def start_edit(self):
        self.last_hwnd = Automation.get_active_window_hwnd()
        text = Automation.send_copy_command()
        self.window.open_with_text(text)

    @Slot(str)
    def finish_edit(self, new_text):
        if self.last_hwnd:
            Automation.send_paste_command(self.last_hwnd, new_text)

    @Slot()
    def cancel_edit(self):
        if self.last_hwnd:
            Automation.set_active_window(self.last_hwnd)

    @Slot()
    def close_app(self):
        print("Завершение работы (по запросу из редактора)...")
        # Снимаем хук F12
        self.hotkeys.stop()
        self.window.close()
        self.app.quit()

    def run(self):
        print("--- Config Overlay v1.1 ---")
        print("Редактировать: Ctrl+Shift+F12")
        print("Полный выход: Shift+Esc (внутри окна редактора)")
        sys.exit(self.app.exec())

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    controller = AppController()
    controller.run()
