# WoodWOP Post Processor - Development Mode

## Автоматическая очистка кэша

При разработке и тестировании модуля FreeCAD кэширует скомпилированные `.pyc` файлы,
что может приводить к использованию старых версий кода после изменений.

Модуль поддерживает **автоматическую очистку кэша** при загрузке.

### Способ 1: Файл-маркер `.dev_mode` (рекомендуется)

Создайте пустой файл `.dev_mode` в директории модуля:

```bash
touch .dev_mode
```

Теперь при каждой загрузке модуля в FreeCAD кэш будет автоматически очищаться.

**Отключение:** Удалите файл `.dev_mode`

```bash
rm .dev_mode
```

### Способ 2: Переменная окружения

Установите переменную окружения перед запуском FreeCAD:

**Linux/macOS:**
```bash
export WOODWOP_DEV_MODE=1
freecad
```

**Windows (cmd):**
```cmd
set WOODWOP_DEV_MODE=1
freecad.exe
```

**Windows (PowerShell):**
```powershell
$env:WOODWOP_DEV_MODE = "1"
freecad.exe
```

### Проверка режима разработки

При загрузке модуля в dev mode вы увидите сообщение:

```
[WoodWOP DEV] Cache cleaned in /path/to/module
```

### Production mode

В production (когда `.dev_mode` отсутствует и `WOODWOP_DEV_MODE` не установлена):
- Кэш **НЕ** очищается автоматически
- Используется стандартное поведение Python/FreeCAD
- Максимальная производительность

### Ручная очистка кэша

Если по какой-то причине автоматическая очистка не работает:

```bash
# Удалить все .pyc файлы
find . -name "*.pyc" -delete

# Удалить все __pycache__ директории
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### Git

Файл `.dev_mode` включен в `.gitignore`, поэтому каждый разработчик может
самостоятельно решать, использовать ли dev mode или нет.
