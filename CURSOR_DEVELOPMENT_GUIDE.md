# WoodWOP Post Processor - Cursor IDE Development Guide

## 🎯 Обзор проекта

**WoodWOP Post Processor** - модульный пост-процессор для FreeCAD, конвертирующий Path операции в формат WoodWOP MPR 4.0 для станков HOMAG CNC.

### Основные возможности

- ✅ Генерация MPR файлов (формат WoodWOP 4.0)
- ✅ Опциональная генерация G-code
- ✅ Поддержка G54 coordinate systems
- ✅ Интеллектуальная маршрутизация инструментов
- ✅ Обработка контуров (линии, дуги)
- ✅ Операции сверления
- ✅ Автоматические отчеты

---

## 📁 Структура проекта

```
woodwop/
├── __init__.py              # Инициализация модуля + dev mode
├── woodwop_post.py          # Entry point для FreeCAD
├── woodwop_post_impl.py     # Главная реализация export()
│
├── config.py                # Глобальные переменные и константы
├── utils.py                 # Вспомогательные функции
│
├── argument_parser.py       # Парсинг аргументов командной строки
├── path_parser.py           # Извлечение контуров из Path команд
├── geometry.py              # Геометрические расчеты
├── job_processor.py         # Обработка FreeCAD Job объектов
│
├── mpr_generator.py         # Генерация MPR контента
├── gcode_generator.py       # Генерация G-code
├── report_generator.py      # Генерация отчетов
├── export_handler.py        # Экспорт Path команд
├── file_writer.py           # Запись файлов с CRLF
│
├── command_patch.py         # Monkey patch для Command.py
├── dialog_patch.py          # Patch для file dialog (disabled)
├── woodwop_file_dialog.py   # Кастомный file dialog
│
├── .dev_mode                # Маркер dev mode (опционально)
├── .gitignore               # Git ignore rules
└── README.md                # Документация
```

---

## 🚀 Быстрый старт в Cursor

### 1. Настройка окружения

```bash
# Клонируй репозиторий
git clone https://github.com/cebdan/woodwop-post-processor.git
cd woodwop-post-processor/woodwop

# Активируй dev mode для автоочистки кэша
touch .dev_mode

# Убедись что FreeCAD установлен
which freecad  # Linux/macOS
where freecad  # Windows
```

### 2. Открой проект в Cursor

```bash
cursor .
```

### 3. Установи Python extension для Cursor

- Открой Extensions (Ctrl+Shift+X)
- Найди "Python" от Microsoft
- Установи

### 4. Настрой Python interpreter

Cursor нужно указать путь к Python из FreeCAD:

**Linux:**
```bash
/usr/lib/freecad/bin/python3
# или
/usr/bin/python3
```

**macOS:**
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/python3
```

**Windows:**
```bash
C:\Program Files\FreeCAD\bin\python.exe
```

В Cursor: `Ctrl+Shift+P` → "Python: Select Interpreter" → добавь путь

---

## 💻 Рабочий процесс разработки

### Workflow с автоочисткой кэша

1. **Редактируй код** в Cursor
2. **Сохрани файл** (Ctrl+S)
3. **Переключись в FreeCAD** (не нужна перезагрузка!)
4. **Post Process** → модуль автоматически очистит кэш и загрузит новую версию
5. **Проверь результат**

### Без .dev_mode (требуется перезагрузка)

1. Редактируй код в Cursor
2. Сохрани файл
3. **Перезагрузи FreeCAD** полностью
4. Post Process
5. Проверь результат

---

## 🔍 Понимание потока данных

### Основной поток (export function)

```
FreeCAD Job
    ↓
woodwop_post.py (entry point)
    ↓
woodwop_post_impl.py: export()
    ↓
1. argument_parser.py     → Парсинг флагов (--log, --nc, etc)
2. job_processor.py       → Обработка всех Path объектов
3. path_parser.py         → Извлечение контуров и операций
4. geometry.py            → Расчет границ, offsets, compensation
5. mpr_generator.py       → Генерация MPR контента
6. gcode_generator.py     → Генерация G-code (если --nc)
7. report_generator.py    → Генерация отчетов (если --report)
8. command_patch.py       → Запись файлов через patched Command
    ↓
MPR file (и опционально NC file)
```

### Патчинг FreeCAD

```
command_patch.py (auto-loads)
    ↓
Monkey patches Command._write_file()
    ↓
Fixes: gcode type checking (list → string)
       .mpr extension enforcement
       CRLF line endings (via file_writer.py)
```

---

## 🛠️ Частые задачи разработки

### Добавление нового флага

**1. Определи флаг в `config.py`:**

```python
# config.py
ENABLE_MY_FEATURE = False
```

**2. Добавь парсинг в `argument_parser.py`:**

```python
# argument_parser.py
def parse_arguments(argstring):
    # ...
    elif arg == '--my-feature' or normalized_arg == 'my-feature':
        config.ENABLE_MY_FEATURE = True
        print(f"[WoodWOP] My feature enabled")
    # ...
```

**3. Добавь в TOOLTIP_ARGS в `config.py`:**

```python
# config.py
TOOLTIP_ARGS = '''
...
--my-feature: Enable my awesome feature
  Description of what it does
...
'''
```

**4. Используй флаг где нужно:**

```python
# В любом модуле
from . import config

if config.ENABLE_MY_FEATURE:
    # Do something
    pass
```

### Добавление нового типа операции

**1. Определи в `job_processor.py`:**

```python
def process_path_object(obj):
    op_type = get_operation_type(obj)
    
    if op_type == 'my_operation':
        # Создай операцию
        config.operations.append(create_my_operation(obj))
```

**2. Создай функцию создания операции:**

```python
def create_my_operation(obj, tool_number):
    return {
        'type': 'MyOperation',
        'id': 104,
        'tool': tool_number,
        'param1': value1,
        # ...
    }
```

**3. Добавь генерацию в MPR в `mpr_generator.py`:**

```python
# В generate_mpr_content()
for op in config.operations:
    if op['type'] == 'MyOperation':
        output.append(f'<{op["id"]} \\MyOperation\\')
        output.append(f'TNO="{op["tool"]}"')
        # ... другие параметры
        output.append('')
```

### Модификация формата MPR

Все изменения MPR формата делаются в `mpr_generator.py`:

```python
def generate_mpr_content(z_safe=20.0):
    output = []
    
    # Header section [H
    output.append('[H')
    output.append('VERSION="4.0 Alpha"')
    # ... добавь новые параметры
    
    # Contours section
    for contour in config.contours:
        # ... модифицируй контуры
    
    # Operations section
    for op in config.operations:
        # ... модифицируй операции
    
    return '\r\n'.join(output)
```

### Добавление нового геометрического расчета

В `geometry.py`:

```python
def calculate_my_geometry():
    """
    Calculate something geometric.
    
    Returns:
        tuple: (result1, result2, ...)
    """
    # Используй данные из config.contours
    for contour in config.contours:
        for elem in contour['elements']:
            # Обработай элементы
            pass
    
    return result
```

---

## 🐛 Отладка в Cursor

### Логирование

Используй встроенную систему логирования:

```python
from . import utils

# Debug log (только если --log включен)
utils.debug_log("Debug message")

# Всегда печатать
print(f"[WoodWOP] Important message")

# FreeCAD console (если доступен)
try:
    import FreeCAD
    FreeCAD.Console.PrintMessage("Message\n")
    FreeCAD.Console.PrintWarning("Warning\n")
    FreeCAD.Console.PrintError("Error\n")
except:
    pass
```

### Включение verbose logging

```bash
# В FreeCAD Path → Post Process → Arguments:
--log

# Или в коде:
config.ENABLE_VERBOSE_LOGGING = True
```

### Генерация отчетов для анализа

```bash
# В Arguments:
--report

# Создаст файл: output_job_report.txt
```

### Export Path Commands

```bash
# В Arguments:
--p_c

# Создаст файл: output_path_commands.txt
# Содержит все G-code команды со всех операций
```

### Проверка MPR файла

```bash
# Hex dump (проверка CRLF)
od -A x -t x1z -v file.mpr | head -50

# Поиск двойных CR (должен вернуть 0)
grep -c $'\r\r' file.mpr

# Проверка кодировки
file file.mpr
```

---

## 🧪 Тестирование

### Тест-кейсы для проверки

**1. Базовая генерация:**
```bash
# Создай простой контур в FreeCAD
# Post Process без аргументов
# Проверь что .mpr файл создан и корректен
```

**2. G-code генерация:**
```bash
# Post Process → Arguments: --nc
# Проверь что созданы и .mpr и .nc файлы
```

**3. Coordinate system offset:**
```bash
# В Job → Fixtures → отметь G54
# Post Process
# Проверь offset в отчете (--report)
```

**4. Line endings:**
```bash
# Post Process
od -A x -t x1z -v output.mpr | head -20
# Должно быть 0d 0a (не 0d 0d 0a)
```

**5. Tool routing:**
```bash
# Создай операции с разными инструментами:
#   - D100 (WoodWOP macro)
#   - T65  (WoodWOP macro)
#   - T550 (FreeCAD G-code)
# Проверь что routing правильный
```

---

## 📝 Code Style Guidelines

### Python Style

```python
# Imports
import os
import sys
from . import config  # Relative imports для модулей

# Functions
def my_function(param1, param2):
    """
    Short description.
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        type: Description
    """
    # Code
    pass

# Comments - английский язык
# Good: "Calculate center point"
# Bad:  "Вычисляем центр"

# Constants
MY_CONSTANT = 42

# Variables
my_variable = "value"
```

### Naming Conventions

```python
# Modules: lowercase_with_underscores
# argument_parser.py

# Classes: PascalCase
class MyClass:
    pass

# Functions: lowercase_with_underscores
def calculate_bounds():
    pass

# Variables: lowercase_with_underscores
contour_counter = 1

# Constants: UPPERCASE_WITH_UNDERSCORES
WORKPIECE_LENGTH = 800.0
```

### Documentation

```python
# Каждая функция должна иметь docstring
def process_path_object(obj):
    """
    Process a single FreeCAD Path object.
    
    Determines operation type and creates appropriate operations
    in config.operations list.
    
    Args:
        obj: FreeCAD Path object to process
        
    Returns:
        None (modifies config.operations directly)
    """
    pass
```

---

## 🔧 Cursor-specific Tips

### 1. Use Cursor AI для понимания кода

```
# Выдели функцию → Ctrl+L → спроси:
"What does this function do?"
"How is this used in the codebase?"
"Are there any bugs in this code?"
```

### 2. Generate code с AI

```
# Ctrl+K в пустой функции:
"Generate a function that calculates arc center from I,J offsets"
```

### 3. Multi-file editing

```
# Ctrl+P → введи имя файла для быстрого открытия
# Ctrl+Shift+F → поиск по всему проекту
# F12 → Go to definition
# Shift+F12 → Find all references
```

### 4. Git integration

```
# Ctrl+Shift+G → открыть Git панель
# Stage changes
# Commit with message
# Push
```

### 5. Terminal в Cursor

```
# Ctrl+` → открыть terminal
# Можно запускать команды прямо в IDE:

od -A x -t x1z -v file.mpr | head -20
python test.py
```

---

## 🚨 Критические моменты

### 1. Line Endings (CRLF)

**КРИТИЧНО:** MPR файлы ДОЛЖНЫ использовать CRLF (`\r\n`), не LF (`\n`)!

```python
# ✅ Правильно (binary mode):
with open(filename, "wb") as f:
    f.write(content.encode("cp1252"))

# ❌ Неправильно (text mode с newline):
with open(filename, "w", newline="\r\n") as f:  # Создаст \r\r\n!
    f.write(content)
```

Используй `file_writer.py` для записи MPR файлов!

### 2. Coordinate Offsets

G54 offset применяется **ТОЛЬКО к MPR формату**, НЕ к G-code!

```python
# MPR coordinates
elem_x = elem['x'] + config.COORDINATE_OFFSET_X

# G-code coordinates (NO offset!)
gcode_x = elem['x']  # Original coordinates
```

### 3. Arc Center Calculation

I, J - это **смещения от предыдущей точки**, не абсолютные координаты!

```python
# ✅ Правильно:
center_x = prev_x + elem['i']
center_y = prev_y + elem['j']

# ❌ Неправильно:
center_x = elem['i']  # Это offset, не координата!
```

### 4. Tool Routing Logic

```python
# WoodWOP macros (tools 1-400):
if (tool_name.startswith('D') or 
    60 <= tool_num <= 75 or 
    400 <= tool_num <= 500):
    # Use WoodWOP MPR format
    
# FreeCAD G-code (tools 500-600):
elif 500 <= tool_num <= 600:
    # Use FreeCAD G-code
```

---

## 📚 Полезные ресурсы

### Документация

- **FreeCAD Path Workbench:** https://wiki.freecad.org/Path_Workbench
- **WoodWOP Documentation:** HOMAG official docs
- **Python String Encoding:** https://docs.python.org/3/library/codecs.html

### Внутренние файлы проекта

- `README.md` - Основная документация
- `DEV_MODE_README.md` - Dev mode инструкции
- `CURSOR_DEVELOPMENT_GUIDE.md` - Это руководство
- `TOOLTIP_ARGS` в `config.py` - Список всех флагов

### Debugging files

При использовании флагов генерируются debug файлы:

```
--report     → output_job_report.txt
--p_c        → output_path_commands.txt
--p_a        → output_processing_analysis.txt
```

---

## 🎓 Практические примеры

### Пример 1: Добавить новый параметр в MPR header

```python
# config.py
MY_NEW_PARAM = "custom_value"

# mpr_generator.py - в generate_mpr_content()
def generate_mpr_content(z_safe=20.0):
    output = []
    output.append('[H')
    output.append('VERSION="4.0 Alpha"')
    # ... другие параметры
    output.append(f'CUSTOM_PARAM="{config.MY_NEW_PARAM}"')  # Новый параметр
    # ...
```

### Пример 2: Добавить проверку инструмента

```python
# job_processor.py
def get_tool_number(obj):
    tool_num = None  # ... получаем номер
    
    # Добавим проверку
    if tool_num is not None and tool_num > 1000:
        print(f"[WoodWOP WARNING] Tool {tool_num} is out of valid range!")
    
    return tool_num
```

### Пример 3: Кастомная фильтрация G0

```python
# path_parser.py - в extract_contour_from_path()

if cmd.Name in ['G0', 'G00']:
    # Пропустить G0 если config.SKIP_G0 = True
    if config.SKIP_G0:
        current_x = x
        current_y = y
        current_z = z
        continue  # Не добавляем в elements
```

---

## 🎯 Чеклист перед коммитом

- [ ] Код следует style guidelines
- [ ] Все функции имеют docstrings
- [ ] Добавлены комментарии к сложной логике
- [ ] Протестировано с `.dev_mode`
- [ ] Протестировано без `.dev_mode`
- [ ] Проверен hex dump MPR файла (нет `0d 0d 0a`)
- [ ] Обновлен `README.md` если нужно
- [ ] Обновлен `TOOLTIP_ARGS` если добавлен флаг
- [ ] Git commit message описывает изменения

---

## 💡 Советы для продуктивности в Cursor

1. **Используй AI Composer** (Ctrl+I) для сложных задач
2. **Quick Fix** (Ctrl+.) на ошибках
3. **Multi-cursor editing** (Ctrl+D для выделения)
4. **Fold/Unfold code** (Ctrl+Shift+[/])
5. **Breadcrumbs** для навигации в файлах
6. **Minimap** для быстрого обзора кода
7. **Split editor** для сравнения файлов
8. **Integrated terminal** (Ctrl+`) для команд

---

**Удачной разработки! 🚀**

Если возникнут вопросы - смотри код в других модулях, они следуют тем же паттернам.
