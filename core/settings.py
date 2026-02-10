# core/settings.py
"""
Модуль настроек редактора.
"""

from dataclasses import dataclass
from typing import Optional
import json
import os


@dataclass
class EditorSettings:
    """Настройки редактора."""
    
    # Отображение номеров строк
    show_line_numbers: bool = True
    
    # Замена табов на пробелы
    replace_tabs_with_spaces: bool = True
    tab_width: int = 4  # Количество пробелов для замены таба (3 или 4)
    
    # Подсветка синтаксиса
    enable_highlighting: bool = True
    color_scheme: str = 'high_contrast_dark'
    
    # Шрифт
    font_size: int = 11
    
    # Автоматическое сворачивание методов
    auto_fold_methods: bool = True  # Сворачивать все методы кроме текущего (на котором курсор)
    
    @classmethod
    def load_from_file(cls, filepath: str = 'editor_settings.json') -> 'EditorSettings':
        """Загрузить настройки из файла."""
        if not os.path.exists(filepath):
            return cls()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls(**data)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            return cls()
    
    def save_to_file(self, filepath: str = 'editor_settings.json'):
        """Сохранить настройки в файл."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def update(self, **kwargs):
        """Обновить настройки."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# Глобальный экземпляр настроек
_settings: Optional[EditorSettings] = None


def get_settings() -> EditorSettings:
    """Получить глобальные настройки."""
    global _settings
    if _settings is None:
        _settings = EditorSettings.load_from_file()
    return _settings


def save_settings():
    """Сохранить глобальные настройки."""
    if _settings is not None:
        _settings.save_to_file()
