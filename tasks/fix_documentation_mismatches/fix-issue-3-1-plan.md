# Task Plan: Fix Issue 3.1 - Missing Lightweight AI Model Configuration

> **Based on template:** `docs/ai-agent-task-template.md`  
> **Issue Reference:** `tasks/fix_documentation_mismatches/documentation-mismatches.md` §3.1  
> **Date created:** 2025-11-05  
> **Priority:** Medium  
> **Estimated Complexity:** 3/10  
> **Estimated Time:** 1-2 hours

---

## МЕТАИНФОРМАЦИЯ

**ID задачи:** PRMT-DOC-3.1  
**Название:** Добавить конфигурацию для lightweight AI модели  
**Дата создания:** 2025-11-05  
**Приоритет:** Средний  
**Оценка сложности:** 3/10  
**Предполагаемое время:** 1-2 часа

---

## БИЗНЕС-КОНТЕКСТ

### Описание проблемы
В технической документации (TRD §5.2, §7.1) описаны **4 AI модели** для использования в системе:
1. Primary: `meta-llama/llama-4-scout:free`
2. Fallback: `google/gemini-2.5-pro-exp:free`
3. Alternative: `mistralai/mistral-small-3.1-24b-instruct:free`
4. **Lightweight: `qwen/qwen2.5-vl-3b-instruct:free`** (3B, multimodal)

Однако в текущей реализации (`src/promptheus/config/settings.py`) присутствуют только 3 модели. Четвертая модель (lightweight) отсутствует полностью, что создает **несоответствие между документацией и кодом**.

### Бизнес-цели
- Обеспечить соответствие кода и документации для прозрачности архитектуры
- Предоставить возможность использования легковесной модели для простых задач (экономия токенов, скорость)
- Подготовить систему к масштабированию с оптимизацией по стоимости
- Улучшить документированность конфигурации системы

### Целевая аудитория
- **Основная:** Разработчики команды Promptheus (для понимания доступных моделей)
- **Вторичная:** Администраторы (для настройки конфигурации в разных окружениях)
- **Будущая:** DevOps инженеры (для оптимизации стоимости AI запросов)

### Ценность для бизнеса
- Возможность использования легковесной модели для простых операций (снижение нагрузки)
- Подготовка к будущей оптимизации стоимости AI запросов (при переходе на платные модели)
- Улучшение документированности для будущих разработчиков
- Согласованность архитектуры: код = документация

---

## ТЕХНИЧЕСКОЕ ЗАДАНИЕ

### Функциональные требования

#### Основная функциональность
Как разработчик, я хочу иметь доступ к настройке lightweight AI модели в конфигурации, чтобы использовать её для простых задач (например, генерация примеров, краткие комментарии) без избыточных затрат ресурсов.

#### Детальные требования

1. **Добавить поле `ai_model_lightweight` в Settings**
   - Описание: Создать новое поле в классе `Settings` для lightweight модели
   - Входные данные: Значение по умолчанию из TRD
   - Выходные данные: Валидированное Pydantic поле
   - Ограничения: Должен соответствовать паттерну других AI моделей

2. **Обновить документацию в коде**
   - Описание: Добавить docstring с описанием модели (3B, multimodal)
   - Формат: Pydantic `Field(description="...")`
   - Примечание: Следовать существующему стилю описаний

3. **Обновить .env.example (если существует)**
   - Описание: Добавить пример переменной окружения
   - Формат: `AI_MODEL_LIGHTWEIGHT=qwen/qwen2.5-vl-3b-instruct:free`
   - Примечание: Опционально, если файл существует

### Нефункциональные требования

#### Совместимость
- Не нарушать существующую функциональность
- Обратная совместимость: значение по умолчанию должно работать без изменения .env
- Pydantic валидация должна работать корректно

#### Документированность
- Docstring должен следовать Google style
- Описание должно быть информативным (характеристики модели)

#### Стандарты кода
- Соответствие PEP 8
- Type hints везде
- Соответствие существующему стилю конфигурации

---

## ТЕХНИЧЕСКИЙ КОНТЕКСТ

### Архитектура системы
```
┌─────────────────────────────────────────────────────┐
│              Settings (Pydantic)                    │
│  ┌───────────────────────────────────────────────┐  │
│  │ AI Model Configuration                        │  │
│  │  • ai_model_primary (109B MoE)               │  │
│  │  • ai_model_fallback (1M context)            │  │
│  │  • ai_model_alternative (96K context)        │  │
│  │  • [ДОБАВИТЬ] ai_model_lightweight (3B)      │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│         OpenRouterClient (AI Integration)           │
│  Использует модели из Settings для запросов         │
└─────────────────────────────────────────────────────┘
```

### Технологический стек
- **Configuration:** Pydantic Settings 2.0+
- **Environment:** python-dotenv
- **Python Version:** 3.11+

### Структура проекта
```
src/promptheus/
├── config/
│   └── settings.py          ← ИЗМЕНИТЬ: добавить ai_model_lightweight
└── integration/
    └── openrouter_client.py  ← ПРОВЕРИТЬ: может понадобиться обновление
```

### Файлы для изменения

1. **`src/promptheus/config/settings.py`**
   - Назначение: Конфигурация приложения через Pydantic Settings
   - Где вносить изменения: Класс `Settings`, раздел "OpenRouter AI" (строки ~27-36)
   - Примечания: Следовать паттерну существующих полей `ai_model_*`

2. **`.env.example`** (если существует)
   - Назначение: Пример файла конфигурации для разработчиков
   - Где вносить изменения: Добавить строку с новой переменной
   - Примечания: Опциональное изменение, зависит от наличия файла

### Связанные компоненты
- **OpenRouterClient** (`src/promptheus/integration/openrouter_client.py`): Использует настройки моделей из Settings
- **Dependency Container** (если есть): Может инжектить Settings в компоненты
- **Documentation** (TRD, SAD): Уже содержат описание всех 4 моделей

---

## ПРИМЕРЫ И ДОКУМЕНТАЦИЯ

### Примеры кода

#### Пример 1: Существующее поле ai_model_primary (settings.py)
```python
ai_model_primary: str = Field(
    default="meta-llama/llama-4-scout:free",
    description="Primary AI model (109B MoE, 512K context)",
)
```

**Объяснение:** Используйте этот паттерн для нового поля - тип `str`, `Field` с default и description.

#### Пример 2: Текущая структура AI моделей (settings.py строки 27-36)
```python
# OpenRouter AI
openrouter_api_key: str = Field(..., description="OpenRouter API key")
ai_model_primary: str = Field(
    default="meta-llama/llama-4-scout:free",
    description="Primary AI model (109B MoE, 512K context)",
)
ai_model_fallback: str = Field(
    default="google/gemini-2.5-pro-exp:free",
    description="Fallback AI model (1M context, advanced reasoning)",
)
ai_model_alternative: str = Field(
    default="mistralai/mistral-small-3.1-24b-instruct:free",
    description="Alternative AI model (96K context, function calling)",
)
# ← ЗДЕСЬ добавить ai_model_lightweight
```

#### Пример 3: Документация из TRD §5.2
```markdown
**Model Selection**: Free models for MVP phase via OpenRouter
  - Primary: `meta-llama/llama-4-scout:free` (109B MoE, 512K context)
  - Fallback: `google/gemini-2.5-pro-exp:free` (1M context, advanced reasoning)
  - Alternative: `mistralai/mistral-small-3.1-24b-instruct:free` (96K context, function calling)
  - Lightweight: `qwen/qwen2.5-vl-3b-instruct:free` (3B, multimodal for examples)
```

**Объяснение:** Lightweight модель предназначена для простых задач - генерация примеров, небольшие комментарии.

### Документация
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Pydantic Field](https://docs.pydantic.dev/latest/api/fields/)
- [TRD §5.2](../docs/technical-requirements-document.md#52-openrouter-api) - описание всех моделей
- [Development Standards §8](../docs/development-standards.md#8-configuration-management) - стандарты конфигурации

### Существующие паттерны
- **Pydantic Fields:** Все настройки используют `Field()` с `default` и `description`
- **Naming Convention:** `snake_case` для переменных окружения и полей
- **Documentation:** Description включает ключевые характеристики (размер модели, контекст)
- **Type Hints:** Всегда указываем тип (в данном случае `str`)

### Известные подводные камни
⚠️ **Важно:**
- **Не забыть description:** Все поля моделей имеют информативные описания - lightweight также должен
- **Консистентность имён:** Использовать паттерн `ai_model_*` (не `ai_lightweight_model`)
- **Значение по умолчанию:** Обязательно указать, чтобы работало без .env
- **Pydantic валидация:** Pydantic автоматически валидирует `str` - дополнительной валидации не нужно
- **Окружение:** Переменная будет автоматически читаться как `AI_MODEL_LIGHTWEIGHT` (case_sensitive=False)

---

## КРИТЕРИИ ПРИЕМКИ

### Сценарные критерии (Given-When-Then)

#### Сценарий 1: Загрузка конфигурации с lightweight моделью по умолчанию
```gherkin
Given конфигурационный файл .env не содержит AI_MODEL_LIGHTWEIGHT
When приложение загружает Settings
Then поле ai_model_lightweight имеет значение "qwen/qwen2.5-vl-3b-instruct:free"
And тип поля str
And description содержит информацию о модели (3B, multimodal)
```

#### Сценарий 2: Переопределение lightweight модели через .env
```gherkin
Given конфигурационный файл .env содержит AI_MODEL_LIGHTWEIGHT=custom/model:free
When приложение загружает Settings
Then поле ai_model_lightweight имеет значение "custom/model:free"
And валидация Pydantic проходит успешно
```

#### Сценарий 3: Доступ к настройке из кода
```gherkin
Given Settings успешно инициализированы
When код обращается к settings.ai_model_lightweight
Then значение возвращается корректно
And нет ошибок AttributeError
And значение можно использовать в OpenRouterClient
```

### Правила и ограничения
- [ ] Поле `ai_model_lightweight` существует в классе Settings
- [ ] Тип поля: `str`
- [ ] Значение по умолчанию: `"qwen/qwen2.5-vl-3b-instruct:free"`
- [ ] Description информативный и следует паттерну других моделей
- [ ] Переменная окружения `AI_MODEL_LIGHTWEIGHT` автоматически маппится
- [ ] Pydantic валидация работает корректно

### Тестирование
- [ ] Settings загружаются без ошибок (с и без .env)
- [ ] Значение по умолчанию корректно
- [ ] Переопределение через .env работает
- [ ] Type hints корректны (mypy проходит)
- [ ] Документация в description присутствует

### Код-ревью
- [ ] Код соответствует PEP 8
- [ ] Type hint добавлен
- [ ] Docstring в Google style (через Field description)
- [ ] Нет хардкода (используется Field default)
- [ ] Паттерн соответствует другим полям ai_model_*

### Совместимость
- [ ] Существующие тесты проходят без изменений
- [ ] Не требуется миграция данных
- [ ] Обратная совместимость сохранена
- [ ] Settings по-прежнему валидируются корректно

---

## ПЛАН РЕАЛИЗАЦИИ

### Этапы выполнения

#### Этап 1: Добавление поля в Settings
**Описание:** Внести изменения в `settings.py`
**Задачи:**
- [ ] Открыть файл `src/promptheus/config/settings.py`
- [ ] Найти раздел "OpenRouter AI" (после `ai_model_alternative`)
- [ ] Добавить новое поле `ai_model_lightweight` с корректным типом и описанием
- [ ] Проверить форматирование кода (соответствие PEP 8)

**Валидация:**
- Python импортирует модуль без ошибок
- mypy type checking проходит
- Код читается естественно, следует паттерну

#### Этап 2: Проверка существования .env.example
**Описание:** Определить, нужно ли обновлять пример конфигурации
**Задачи:**
- [ ] Проверить наличие файла `.env.example` в корне проекта
- [ ] Если существует: добавить строку `AI_MODEL_LIGHTWEIGHT=qwen/qwen2.5-vl-3b-instruct:free`
- [ ] Если не существует: пропустить этап

**Валидация:**
- Если файл есть: новая переменная присутствует в примере
- Формат соответствует другим переменным

#### Этап 3: Тестирование изменений
**Описание:** Убедиться, что изменения работают корректно
**Задачи:**
- [ ] Запустить Python REPL и импортировать Settings
- [ ] Проверить значение по умолчанию: `settings.ai_model_lightweight`
- [ ] Создать .env с переопределением и проверить
- [ ] Запустить существующие тесты (если есть)
- [ ] Проверить mypy: `mypy src/promptheus/config/settings.py`

**Валидация:**
- Значение по умолчанию `"qwen/qwen2.5-vl-3b-instruct:free"`
- Переопределение через .env работает
- Все существующие тесты проходят
- mypy не выдаёт ошибок

#### Этап 4: Документирование изменений
**Описание:** Зафиксировать выполнение задачи
**Задачи:**
- [ ] Обновить `documentation-mismatches.md`: отметить §3.1 как исправленный
- [ ] Создать changelog entry (если ведётся CHANGELOG.md)
- [ ] Подготовить commit message (следуя Conventional Commits)

**Валидация:**
- documentation-mismatches.md содержит статус "✅ Fixed"
- Commit message описательный: `fix(config): add ai_model_lightweight setting`

---

## ТЕСТИРОВАНИЕ И ВАЛИДАЦИЯ

### Ручное тестирование

#### Тест 1: Загрузка Settings с default значением
```python
# test_settings_default.py (ручной тест)
from promptheus.config.settings import get_settings

settings = get_settings()
print(f"Lightweight model: {settings.ai_model_lightweight}")
# Expected output: qwen/qwen2.5-vl-3b-instruct:free

assert settings.ai_model_lightweight == "qwen/qwen2.5-vl-3b-instruct:free"
print("✅ Default value correct")
```

#### Тест 2: Переопределение через .env
```bash
# Create .env file with override
echo "AI_MODEL_LIGHTWEIGHT=test/model:free" > .env

# Run Python
python -c "from promptheus.config.settings import get_settings; print(get_settings().ai_model_lightweight)"
# Expected output: test/model:free
```

#### Тест 3: Type checking
```bash
# Run mypy
mypy src/promptheus/config/settings.py
# Expected: Success: no issues found
```

### Команды для запуска
```bash
# Проверить импорт Settings
python -c "from promptheus.config.settings import Settings; print(Settings().ai_model_lightweight)"

# Запустить mypy
mypy src/promptheus/config/settings.py

# Запустить ruff linter
ruff check src/promptheus/config/settings.py

# Запустить существующие тесты (если есть)
pytest tests/test_config.py -v
```

### Сценарии валидации

1. **Сценарий: Чтение из кода**
   - Импортировать Settings
   - Получить значение `ai_model_lightweight`
   - Проверить тип (должен быть `str`)
   - Ожидаемый результат: `"qwen/qwen2.5-vl-3b-instruct:free"`

2. **Сценарий: Переопределение**
   - Создать .env с `AI_MODEL_LIGHTWEIGHT=custom-model`
   - Загрузить Settings
   - Проверить значение
   - Ожидаемый результат: `"custom-model"`

3. **Сценарий: Совместимость**
   - Запустить существующие unit-тесты
   - Убедиться, что ничего не сломалось
   - Ожидаемый результат: Все тесты проходят

---

## ДОПОЛНИТЕЛЬНЫЕ СООБРАЖЕНИЯ

### Риски
- **Риск: Изменение может сломать существующий код, если где-то хардкод на 3 модели**
  - Митигация: Провести grep поиск по кодовой базе на использование моделей
  - Команда: `grep -r "ai_model_" src/ --include="*.py"`

- **Риск: Непонятно, используется ли lightweight модель в коде**
  - Митигация: Проверить OpenRouterClient и другие места использования
  - Действие: Если не используется - это OK, подготовка к будущему использованию

### Предположения
- Settings загружаются через `get_settings()` с кэшированием (lru_cache)
- Приложение использует python-dotenv для загрузки .env
- Pydantic Settings автоматически маппит переменные окружения (case_sensitive=False)

### Ограничения
- Только изменение конфигурации, не добавление логики использования модели
- Не требуется миграция БД или изменение API
- Изменения только в файлах конфигурации

### Будущие улучшения
- [ ] Добавить использование lightweight модели в OpenRouterClient для простых задач
- [ ] Создать стратегию выбора модели на основе сложности задачи
- [ ] Добавить метрики использования каждой модели
- [ ] Документировать best practices для выбора модели в runtime

### Вопросы и нерешенные моменты
- [ ] Используется ли lightweight модель в текущей кодовой базе?
  - Действие: Проверить `grep -r "lightweight" src/`
- [ ] Существует ли .env.example в проекте?
  - Действие: Проверить `ls -la .env.example`
- [ ] Есть ли unit-тесты для Settings?
  - Действие: Проверить `tests/` директорию

---

## ЧЕКЛИСТ ВЫПОЛНЕНИЯ

### Разработка
- [ ] Поле `ai_model_lightweight` добавлено в `Settings` класс
- [ ] Тип поля: `str`
- [ ] Default значение: `"qwen/qwen2.5-vl-3b-instruct:free"`
- [ ] Description добавлен: `"Lightweight AI model (3B, multimodal for examples)"`
- [ ] Код соответствует паттерну других полей `ai_model_*`
- [ ] `.env.example` обновлён (если существует)

### Тестирование
- [ ] Settings загружаются без ошибок
- [ ] Значение по умолчанию корректно
- [ ] Переопределение через .env работает
- [ ] mypy type checking проходит
- [ ] ruff linter не выдаёт ошибок
- [ ] Существующие тесты проходят (если есть)

### Документация
- [ ] Description поля информативный
- [ ] Паттерн соответствует другим полям
- [ ] `documentation-mismatches.md` обновлён (статус §3.1 → Fixed)
- [ ] CHANGELOG обновлён (если ведётся)

### Качество кода
- [ ] Код соответствует PEP 8
- [ ] Type hints присутствуют
- [ ] Нет хардкода
- [ ] Форматирование правильное
- [ ] Нет TODO/FIXME

### Финализация
- [ ] Изменения закоммичены с понятным сообщением
- [ ] Commit message следует Conventional Commits
- [ ] Формат: `fix(config): add ai_model_lightweight setting to match TRD`
- [ ] Pull request создан (если workflow требует)
- [ ] Code review запрошен (если применимо)
- [ ] CI/CD pipeline проходит успешно (если настроен)

---

## РЕЗУЛЬТАТЫ И ЗАМЕТКИ

### Что было сделано
_(Заполняется после выполнения)_

### Проблемы и решения
_(Заполняется при возникновении проблем)_

### Время выполнения
_(Заполняется после завершения)_

---

**Версия плана:** 1.0  
**Создан:** 2025-11-05  
**Автор:** AI Assistant  
**Шаблон:** `docs/ai-agent-task-template.md`  
**Статус:** 📝 Plan Ready
