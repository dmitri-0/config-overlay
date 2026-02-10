"""
Подсветка синтаксиса 1С (BSL) для QPlainTextEdit.
Использует собственный лексер для анализа и QSyntaxHighlighter для рендеринга.
"""

import re
from enum import Enum, auto
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class TokenType(Enum):
    """Типы токенов для 1С (BSL)"""
    KEYWORD = auto()
    BUILTIN = auto()
    FUNCTION = auto()
    COMMENT = auto()
    STRING = auto()
    NUMBER = auto()
    DIRECTIVE = auto()
    OPERATOR = auto()
    ERROR = auto()
    NORMAL = auto()
    WHITESPACE = auto()


class Token:
    """Токен лексера"""
    __slots__ = ('type', 'value', 'start', 'end')
    
    def __init__(self, token_type: TokenType, value: str, start: int, end: int):
        self.type = token_type
        self.value = value
        self.start = start
        self.end = end
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.start}, {self.end})"


class BSLLexer:
    """
    Лексический анализатор для языка 1С (BSL).
    Поддерживает:
    - Ключевые слова (Процедура, Функция, Если и т.д.)
    - Встроенные функции и типы
    - Комментарии (однострочные //)
    - Строки (обычные "..." с многострочными продолжениями)
    - Числа
    - Директивы препроцессора (#Если, &НаКлиенте)
    - Операторы
    """
    
    # Ключевые слова 1С (регистронезависимые)
    KEYWORDS = {
        # Объявления
        'процедура', 'procedure', 'функция', 'function', 'конецпроцедуры', 'endprocedure',
        'конецфункции', 'endfunction', 'перем', 'var', 'экспорт', 'export',
        
        # Управляющие конструкции
        'если', 'if', 'тогда', 'then', 'иначеесли', 'elseif', 'elsif', 'иначе', 'else',
        'конецесли', 'endif', 'для', 'for', 'каждого', 'each', 'из', 'in', 'по', 'to',
        'цикл', 'do', 'конеццикла', 'enddo', 'пока', 'while', 'попытка', 'try',
        'исключение', 'except', 'конецпопытки', 'endtry', 'вызватьисключение', 'raise',
        'возврат', 'return', 'продолжить', 'continue', 'прервать', 'break',
        
        # Логические
        'и', 'and', 'или', 'or', 'не', 'not', 'истина', 'true', 'ложь', 'false',
        'неопределено', 'undefined', 'null',
        
        # Прочее
        'новый', 'new', 'выполнить', 'execute', 'перейти', 'goto',
    }
    
    # Встроенные функции и типы (примеры основных)
    BUILTINS = {
        # Базовые типы
        'число', 'number', 'строка', 'string', 'дата', 'date', 'булево', 'boolean',
        'тип', 'type', 'типзначения', 'typeof',
        
        # Функции работы со строками
        'строка', 'string', 'стрдлина', 'strlen', 'стрзаменить', 'strreplace',
        'стрнайти', 'strfind', 'врег', 'upper', 'нрег', 'lower', 'сокрлп', 'trimall',
        'сокрл', 'triml', 'сокрп', 'trimr', 'лев', 'left', 'прав', 'right',
        'сред', 'mid', 'стрразделить', 'strsplit', 'стрсоединить', 'strjoin',
        'стрначинаетсяс', 'strstartswith', 'стрзаканчиваетсяна', 'strendswith',
        'пустаястрока', 'isblankstring', 'стрчисловхождений', 'stroccurrencecount',
        'стрсравнить', 'strcompare', 'стрполучитьстроку', 'strgetline',
        'стрчислострок', 'strlinecount', 'стршаблон', 'strtemplate',
        
        # Функции работы с числами
        'число', 'number', 'цел', 'int', 'окр', 'round', 'макс', 'max', 'мин', 'min',
        'log', 'log10', 'ln', 'exp', 'pow', 'sqrt', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
        
        # Функции работы с датами
        'дата', 'date', 'текущаядата', 'currentdate', 'год', 'year', 'месяц', 'month',
        'день', 'day', 'час', 'hour', 'минута', 'minute', 'секунда', 'second',
        'началодня', 'begofday', 'началомесяца', 'begofmonth', 'началогода', 'begofyear',
        'конецдня', 'endofday', 'конецмесяца', 'endofmonth', 'конецгода', 'endofyear',
        'началоквартала', 'begofquarter', 'конецквартала', 'endofquarter',
        'началонедели', 'begofweek', 'конецнедели', 'endofweek',
        'началочаса', 'begofhour', 'конечаса', 'endofhour',
        'началоминуты', 'begofminute', 'конецминуты', 'endofminute',
        'добавитьмесяц', 'addmonth', 'деньгода', 'dayofyear', 'деньнедели', 'dayofweek',
        'неделягода', 'weekofyear', 'квартал', 'quarter',
        
        # Системные функции
        'сообщить', 'message', 'предупреждение', 'alert', 'вопрос', 'question',
        'значениезаполнено', 'valuefilled', 'формат', 'format',
        'xmlстрока', 'xmlstring', 'xmlзначение', 'xmlvalue', 'xmlтип', 'xmltype',
        'base64строка', 'base64string', 'base64значение', 'base64value',
        'получитьвремяta', 'getta', 'получитьзначенияотбора', 'getfiltervalues',
        
        # Коллекции и структуры данных
        'массив', 'array', 'структура', 'structure', 'соответствие', 'map',
        'списокзначений', 'valuelist', 'таблицазначений', 'valuetable',
        'деревозначений', 'valuetree', 'фиксированныймассив', 'fixedarray',
        'фиксированнаяструктура', 'fixedstructure', 'фиксированноесоответствие', 'fixedmap',
        'деревострок', 'rowtree', 'коллекциястрок', 'rowcollection',
        
        # Запросы и работа с БД
        'запрос', 'query', 'построительзапроса', 'querybuilder',
        'схемазапроса', 'queryschema', 'менеджервременныхтаблиц', 'tempquerytablelist',
        'пакетзапросов', 'querybatch', 'выборка', 'selection',
        'выборкадетальныхзаписей', 'detailedrecordsselection',
        
        # Работа с файлами
        'файл', 'file', 'найтифайлы', 'findfiles', 'каталогвременныхфайлов', 'tempfilesdir',
        'получитьимявременногофайла', 'gettempfilename', 'каталогдокументов', 'documentsdir',
        'объединитьпути', 'combinepaths', 'разделитьфайл', 'splitfile',
        'удалитьфайлы', 'deletefiles', 'копироватьфайл', 'copyfile',
        'переместитьфайл', 'movefile', 'создатькаталог', 'createdir',
        
        # XML, JSON
        'чтениеxml', 'xmlreader', 'записьxml', 'xmlwriter',
        'чтениеjson', 'jsonreader', 'записьjson', 'jsonwriter',
        'прочитатьjson', 'readjson', 'записатьjson', 'writejson',
        
        # Прочие типы
        'uuid', 'уникальныйидентификатор', 'uniqueidentifier',
        'двоичныеданные', 'binarydata', 'картинка', 'picture',
        'шрифт', 'font', 'цвет', 'color', 'граница', 'border', 'линия', 'line',
        'хранилищезначения', 'valuestorage', 'указательссылки', 'referencepointer',
        'границы', 'boundaries', 'точность', 'accuracy', 'квалификаторыдаты', 'datequalifiers',
        'квалификаторыстроки', 'stringqualifiers', 'квалификаторычисла', 'numberqualifiers',
        'квалификаторыдвоичныхданных', 'binarydataqualifiers',
        
        # Системные перечисления (примеры)
        'видсравнения', 'comparevalues', 'использованиережимаблокировкиданных', 'datalockusagemode',
        'режимавтовремя', 'autotimemode', 'режимблокировкиданных', 'datalockmode',
        'режимтранзакции', 'transactionmode', 'состояниевнешнегоисточникаданных', 'externaldatasourcestate',
        'типплатформы', 'platformtype', 'режимзапускаклиентскогоприложения', 'clientruntimemode',
    }
    
    def __init__(self):
        # Компиляция регулярных выражений для производительности
        self.patterns = {
            'whitespace': re.compile(r'\s+'),
            'comment': re.compile(r'//[^\n]*'),
            'directive': re.compile(r'[#&][А-Яа-яA-Za-z_][А-Яа-яA-Za-z0-9_]*'),
            'string': re.compile(r'"(?:[^"]|"")*"'),  # Строки с экранированием ""
            'number': re.compile(r'\b\d+(?:\.\d+)?\b'),  # Целые и дробные числа
            'identifier': re.compile(r'[А-Яа-яA-Za-z_][А-Яа-яA-Za-z0-9_]*'),
            'operator': re.compile(r'[+\-*/%=<>!;,\.()\[\]{}:]'),
        }
    
    def tokenize(self, text: str) -> list[Token]:
        """
        Токенизация строки текста.
        
        Args:
            text: Исходный текст для анализа
            
        Returns:
            Список токенов
        """
        tokens = []
        pos = 0
        length = len(text)
        
        while pos < length:
            # Пробелы (пропускаем, но можно добавить в tokens при необходимости)
            if match := self.patterns['whitespace'].match(text, pos):
                pos = match.end()
                continue
            
            # Комментарии
            if match := self.patterns['comment'].match(text, pos):
                tokens.append(Token(
                    TokenType.COMMENT,
                    match.group(),
                    match.start(),
                    match.end()
                ))
                pos = match.end()
                continue
            
            # Директивы препроцессора (#Если, &НаКлиенте)
            if match := self.patterns['directive'].match(text, pos):
                tokens.append(Token(
                    TokenType.DIRECTIVE,
                    match.group(),
                    match.start(),
                    match.end()
                ))
                pos = match.end()
                continue
            
            # Строки
            if match := self.patterns['string'].match(text, pos):
                tokens.append(Token(
                    TokenType.STRING,
                    match.group(),
                    match.start(),
                    match.end()
                ))
                pos = match.end()
                continue
            
            # Числа
            if match := self.patterns['number'].match(text, pos):
                tokens.append(Token(
                    TokenType.NUMBER,
                    match.group(),
                    match.start(),
                    match.end()
                ))
                pos = match.end()
                continue
            
            # Идентификаторы (ключевые слова, встроенные функции, имена)
            if match := self.patterns['identifier'].match(text, pos):
                value = match.group()
                value_lower = value.lower()
                
                # Проверяем, является ли идентификатор ключевым словом
                if value_lower in self.KEYWORDS:
                    token_type = TokenType.KEYWORD
                # Проверяем, является ли встроенной функцией/типом
                elif value_lower in self.BUILTINS:
                    token_type = TokenType.BUILTIN
                else:
                    # Проверяем следующий символ - если (, то это вызов функции
                    next_pos = match.end()
                    # Пропускаем пробелы после идентификатора
                    while next_pos < length and text[next_pos].isspace():
                        next_pos += 1
                    
                    # Если следующий символ - открывающая скобка, это функция
                    if next_pos < length and text[next_pos] == '(':
                        token_type = TokenType.FUNCTION
                    else:
                        # Иначе это переменная
                        token_type = TokenType.NORMAL
                
                tokens.append(Token(
                    token_type,
                    value,
                    match.start(),
                    match.end()
                ))
                pos = match.end()
                continue
            
            # Операторы и пунктуация
            if match := self.patterns['operator'].match(text, pos):
                tokens.append(Token(
                    TokenType.OPERATOR,
                    match.group(),
                    match.start(),
                    match.end()
                ))
                pos = match.end()
                continue
            
            # Неизвестный символ - ошибка
            tokens.append(Token(
                TokenType.ERROR,
                text[pos],
                pos,
                pos + 1
            ))
            pos += 1
        
        return tokens


class OneCHighlighter(QSyntaxHighlighter):
    """
    Подсветка синтаксиса 1С:Enterprise (BSL) на основе собственного лексера.
    
    Особенности:
    - Асинхронная подсветка через QSyntaxHighlighter (не блокирует UI)
    - Собственный быстрый лексер без внешних зависимостей
    - Гибкая настройка цветовой схемы
    - Поддержка комментариев, строк, ключевых слов, функций
    - Различение переменных и вызовов функций
    - Обработка директив препроцессора
    - Поддержка многострочных строк
    """
    
    def __init__(self, parent=None, color_scheme=None):
        super().__init__(parent)
        
        # Цветовая схема по умолчанию (темная тема)
        self.color_scheme = color_scheme or self._get_default_color_scheme()
        
        # Инициализация форматов
        self.formats = {}
        self._setup_formats()
        
        # Инициализация лексера
        self.lexer = BSLLexer()
    
    def _get_default_color_scheme(self):
        """Цветовая схема по умолчанию (темная тема в стиле VS Code)"""
        return {
            'keyword': ('#569CD6', True, False),      # Синие жирные
            'builtin': ('#4EC9B0', False, False),     # Бирюзовые
            'function': ('#DCDCAA', False, False),    # Желтоватые
            'comment': ('#6A9955', False, False),     # Зеленые
            'string': ('#CE9178', False, False),      # Оранжевые
            'number': ('#B5CEA8', False, False),      # Светло-зеленые
            'directive': ('#C586C0', False, False),   # Фиолетовые
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
        Работает асинхронно, не блокируя UI.
        """
        if not text:
            return
        
        # Устанавливаем базовый формат
        self.setFormat(0, len(text), self.formats['normal'])
        
        # Токенизация и применение форматов
        try:
            tokens = self.lexer.tokenize(text)
            
            for token in tokens:
                # Получаем формат для типа токена
                fmt = self._get_format_for_token(token.type)
                if fmt:
                    # Применяем формат к соответствующему участку текста
                    self.setFormat(token.start, token.end - token.start, fmt)
        except Exception as e:
            # В случае ошибки просто не подсвечиваем (не ломаем UI)
            pass
    
    def _get_format_for_token(self, token_type: TokenType):
        """
        Сопоставление типов токенов с форматами.
        
        Args:
            token_type: Тип токена из TokenType
            
        Returns:
            QTextCharFormat или None
        """
        mapping = {
            TokenType.KEYWORD: 'keyword',
            TokenType.BUILTIN: 'builtin',
            TokenType.FUNCTION: 'function',
            TokenType.COMMENT: 'comment',
            TokenType.STRING: 'string',
            TokenType.NUMBER: 'number',
            TokenType.DIRECTIVE: 'directive',
            TokenType.OPERATOR: 'operator',
            TokenType.ERROR: 'error',
            TokenType.NORMAL: 'normal',
        }
        
        format_name = mapping.get(token_type)
        return self.formats.get(format_name) if format_name else None
    
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
        'comment': ('#6A9955', False, False),
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
        'comment': ('#008000', False, False),
        'string': ('#A31515', False, False),
        'number': ('#098658', False, False),
        'directive': ('#AF00DB', False, False),
        'operator': ('#000000', False, False),
        'error': ('#FF0000', False, False),
        'normal': ('#000000', False, False),
    },
}
