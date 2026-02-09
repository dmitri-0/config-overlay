import time
import ctypes
import pyautogui
from PySide6.QtWidgets import QApplication

class Automation:
    @staticmethod
    def get_active_window_hwnd():
        return ctypes.windll.user32.GetForegroundWindow()

    @staticmethod
    def set_active_window(hwnd):
        if not hwnd: return
        try:
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Не удалось активировать окно: {e}")

    @staticmethod
    def send_copy_command():
        clipboard = QApplication.clipboard()
        
        # 1. Отпускаем клавиши
        pyautogui.keyUp('shift')
        pyautogui.keyUp('ctrl')
        #time.sleep(0.1)
        
        # 2. Жмем Ctrl+A, Ctrl+C
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'c')
        
        # 3. ВАЖНО: Даем 1С время отпустить буфер
        time.sleep(0.1) 
        
        # 4. Цикл попыток чтения (Retry Logic)
        # Пытаемся прочитать буфер 5 раз с паузой
        for i in range(5):
            try:
                text = clipboard.text()
                # Если текст получен или буфер реально пуст - возвращаем
                return text
            except Exception:
                # Если Qt ругается, ждем немного и пробуем снова
                time.sleep(0.1)
        
        # Если за 5 попыток не вышло
        print("Не удалось получить доступ к буферу обмена.")
        return ""

    @staticmethod
    def send_paste_command(target_hwnd, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        Automation.set_active_window(target_hwnd)
        time.sleep(0.2) 
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'v')
