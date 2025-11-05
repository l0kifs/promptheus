# План исправления Issue 3.2: Webhook Configuration

> **ID задачи:** PRMT-DOC-3.2  
> **Дата создания:** 2025-11-05  
> **Приоритет:** Средний  
> **Оценка сложности:** 6/10  
> **Предполагаемое время:** 4-6 часов

---

## МЕТАИНФОРМАЦИЯ

**Название:** Добавить поддержку Webhook режима для Telegram бота  
**Категория:** Конфигурация и развертывание  
**Связанные документы:**
- Technical Requirements Document (TRD) §7.1
- Documentation Mismatches §3.2
- System Architecture Document (SAD) §10.2

**Текущее состояние:**
- ❌ Отсутствует поле `webhook_url` в Settings
- ❌ Отсутствует поле `webhook_secret` для валидации
- ❌ Бот работает только в режиме polling
- ❌ Нет возможности переключения между polling и webhook режимами

---

## БИЗНЕС-КОНТЕКСТ

### Описание проблемы

В текущей реализации Telegram бот работает **только в режиме polling** (постоянное опрашивание API), хотя согласно документации (TRD §7.1) должна быть поддержка **webhook режима** для production развертывания.

**Что не так:**
1. В `settings.py` отсутствуют поля `webhook_url` и `webhook_secret`
2. В `main.py` всегда используется polling: `await application.updater.start_polling()`
3. Нет логики выбора между polling и webhook режимами
4. Нет обработчика HTTP endpoint для входящих webhook запросов

### Бизнес-цели

- **Подготовка к production**: Webhook режим обязателен для масштабируемого развертывания
- **Снижение нагрузки**: Webhook эффективнее polling (push vs pull модель)
- **Соответствие best practices**: Telegram рекомендует webhook для production
- **Гибкость развертывания**: Возможность выбора режима в зависимости от окружения

### Целевая аудитория

- **Основная:** DevOps-инженеры, администраторы системы
- **Вторичная:** Разработчики проекта

### Ценность для бизнеса

- **Production-ready решение**: Бот готов к масштабированию
- **Снижение затрат**: Меньше запросов к Telegram API (webhook vs polling)
- **Надежность**: Webhook режим более стабилен при высокой нагрузке
- **Соответствие документации**: Устранение расхождения между docs и кодом

---

## ТЕХНИЧЕСКОЕ ЗАДАНИЕ

### Функциональные требования

#### Основная функциональность

Как **администратор системы**, я хочу развернуть бота в webhook режиме, чтобы получить production-ready решение с оптимальной производительностью.

Как **разработчик**, я хочу иметь возможность выбирать между polling и webhook режимами через конфигурацию, чтобы гибко управлять развертыванием в разных окружениях.

#### Детальные требования

1. **Добавление конфигурационных полей**
   - Описание: Расширить `Settings` для поддержки webhook конфигурации
   - Входные данные:
     - `bot_mode`: enum (`polling` | `webhook`)
     - `webhook_url`: optional string (URL для webhook endpoint)
     - `webhook_secret`: optional string (токен для проверки подлинности)
     - `webhook_port`: optional int (порт для HTTP сервера, default: 8443)
     - `webhook_path`: optional string (путь endpoint, default: `/webhook`)
   - Выходные данные: Валидированный объект Settings
   - Ограничения:
     - Если `bot_mode=webhook`, то `webhook_url` обязателен
     - `webhook_secret` рекомендован для безопасности
     - `webhook_url` должен быть валидным HTTPS URL

2. **Логика выбора режима работы**
   - Описание: Добавить conditional logic в `main.py` для выбора режима
   - Входные данные: `settings.bot_mode`
   - Выходные данные: Запуск бота в соответствующем режиме
   - Ограничения:
     - Polling для `development` по умолчанию
     - Webhook для `production` (если настроен)
     - Graceful fallback при ошибках webhook

3. **HTTP сервер для webhook** (опционально для MVP)
   - Описание: Базовая реализация webhook handler
   - Входные данные: POST запросы от Telegram API
   - Выходные данные: Обработка Update объектов
   - Ограничения:
     - Используем встроенные возможности `python-telegram-bot`
     - Простая реализация без дополнительных зависимостей
     - Валидация `webhook_secret` если настроен

4. **Документация и примеры**
   - Описание: Обновить документацию и примеры конфигурации
   - Входные данные: N/A
   - Выходные данные:
     - Обновленный `.env.example` с webhook параметрами
     - Документация по настройке webhook режима
     - Примеры для development и production

### Нефункциональные требования

#### Производительность

- Переключение режима без изменения кода (только через env variables)
- Webhook режим должен обрабатывать updates < 100ms
- Поддержка graceful shutdown в обоих режимах

#### Безопасность

- HTTPS-only для webhook URL (валидация в settings)
- Опциональная проверка `webhook_secret` для защиты от поддельных запросов
- Логирование попыток доступа к webhook endpoint
- Нет хардкода чувствительных данных

#### Надежность

- Graceful fallback: если webhook не удается настроить, warning в логи
- Автоматическое удаление старого webhook при смене режима
- Корректная обработка ошибок при регистрации webhook
- Retry logic при временных сбоях Telegram API

#### Совместимость

- Обратная совместимость: если webhook параметры не заданы, используется polling
- Совместимость с `python-telegram-bot >= 20.0`
- Работа с существующим dependency container
- Без breaking changes для текущих пользователей

---

## ТЕХНИЧЕСКИЙ КОНТЕКСТ

### Архитектура системы

Текущая архитектура (из SAD):
```
Telegram Bot API
       │
       ▼ (Polling only - текущая реализация)
Bot Interface Layer
       │
       ▼
Application Core
```

Целевая архитектура:
```
Telegram Bot API
       │
       ├─── Polling (для development)
       │
       └─── Webhook (для production)
              │
              ▼ HTTPS POST /webhook
         HTTP Server (встроенный в python-telegram-bot)
              │
              ▼
       Bot Interface Layer
              │
              ▼
       Application Core
```

### Технологический стек

- **Backend:** Python 3.12
- **Bot Framework:** python-telegram-bot 20+
- **HTTP Server:** встроенный в python-telegram-bot (Tornado-based)
- **Configuration:** Pydantic Settings, python-dotenv
- **Logging:** loguru

### Структура проекта

```
src/promptheus/
├── config/
│   ├── __init__.py
│   └── settings.py                    ← ИЗМЕНИТЬ: добавить webhook поля
├── main.py                             ← ИЗМЕНИТЬ: добавить webhook logic
└── ...

.env.example                            ← ОБНОВИТЬ: примеры webhook config
README.md                               ← ОБНОВИТЬ: инструкции по webhook
docs/
└── deployment-plan.md                  ← ПРОВЕРИТЬ: обновить при необходимости
```

### Файлы для изменения

1. **`src/promptheus/config/settings.py`**
   - Назначение: Конфигурация приложения с Pydantic
   - Где вносить изменения:
     - Добавить новые поля после существующих (после `telegram_bot_token`)
     - Добавить custom validator для webhook_url (HTTPS проверка)
     - Добавить computed property для определения режима
   - Примечания:
     - Использовать `Field()` с `description` для каждого поля
     - Добавить Literal type для `bot_mode`
     - Сделать webhook поля Optional

2. **`src/promptheus/main.py`**
   - Назначение: Точка входа приложения, инициализация бота
   - Где вносить изменения:
     - В функции `main()` после создания `application`
     - Добавить conditional logic перед строкой `await application.updater.start_polling()`
     - Создать helper функцию `start_bot_in_mode(application, settings)`
   - Примечания:
     - Сохранить существующий polling код как default
     - Добавить логирование режима запуска
     - Обработать ошибки webhook setup

3. **`.env.example`** (СОЗДАТЬ или ОБНОВИТЬ)
   - Назначение: Пример конфигурации для разработчиков
   - Где вносить изменения:
     - Добавить секцию `# Bot Mode Configuration`
     - Добавить примеры для polling и webhook
   - Примечания:
     - Использовать placeholder значения (не реальные URL)
     - Добавить комментарии с пояснениями

4. **`README.md`**
   - Назначение: Документация проекта
   - Где вносить изменения:
     - Секция "Configuration" или "Deployment"
     - Добавить описание webhook режима
   - Примечания:
     - Краткая инструкция по настройке
     - Ссылка на deployment-plan.md для деталей

### Связанные компоненты

- **DependencyContainer**: Не требует изменений (уже async-ready)
- **BotHandlers**: Не требует изменений (работает с обоими режимами)
- **Logging**: Использовать существующий loguru для новых логов
- **Database**: Не затрагивается

---

## ПРИМЕРЫ И ДОКУМЕНТАЦИЯ

### Примеры кода

#### Пример 1: Текущая реализация polling (main.py)

```python
# main.py - текущая реализация
async def main() -> None:
    # ... инициализация ...
    
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # ... регистрация handlers ...
    
    # Всегда polling
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    await asyncio.Event().wait()
```

**Проблема**: Нет возможности использовать webhook.

#### Пример 2: Webhook реализация из python-telegram-bot docs

```python
# Пример из официальной документации python-telegram-bot
from telegram.ext import Application

application = Application.builder().token("TOKEN").build()

# Webhook mode
await application.bot.set_webhook(
    url="https://example.com/webhook",
    secret_token="my-secret"
)

await application.run_webhook(
    listen="0.0.0.0",
    port=8443,
    url_path="/webhook",
    webhook_url="https://example.com/webhook",
    secret_token="my-secret"
)
```

**Объяснение**: `run_webhook()` создает HTTP сервер и регистрирует webhook в Telegram.

#### Пример 3: Settings с enum и validation (паттерн из проекта)

```python
# settings.py - существующий паттерн
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: Literal["development", "production"] = Field(
        default="development",
        description="Application environment",
    )
```

**Объяснение**: Используем `Literal` для ограниченного набора значений.

### Документация

- [python-telegram-bot Webhook Guide](https://docs.python-telegram-bot.org/en/stable/telegram.ext.application.html#telegram.ext.Application.run_webhook)
- [Telegram Bot API: setWebhook](https://core.telegram.org/bots/api#setwebhook)
- [Pydantic Settings Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- TRD §7.1: Environment Variables
- Deployment Plan (docs/deployment-plan.md)

### Существующие паттерны

- **Settings паттерн**: Все настройки через Pydantic BaseSettings с `.env` файлом
- **Conditional startup**: Уже есть пример в `init_database()` с try/except и критическими логами
- **Graceful shutdown**: Паттерн в `main()` с finally блоком для cleanup
- **Logging**: Использование loguru с context (kwargs): `logger.info("message", key=value)`

### Известные подводные камни

⚠️ **Важно:**

1. **HTTPS обязателен для webhook**: Telegram API принимает только HTTPS URL
   - Решение: Добавить validator в Pydantic для проверки схемы
   
2. **Порт для webhook**: Telegram поддерживает только порты 80, 88, 443, 8443
   - Решение: Добавить validator для проверки порта
   
3. **Polling и webhook взаимоисключающие**: Нельзя использовать оба одновременно
   - Решение: Явно удалять webhook при запуске в polling режиме
   
4. **Webhook требует публичный URL**: Для development нужен туннель (ngrok)
   - Решение: Документировать в README, polling по умолчанию для dev
   
5. **run_webhook() блокирует**: Метод асинхронный и блокирует как и polling
   - Решение: Использовать тот же паттерн с `asyncio.Event().wait()`

6. **Secret token опционален но рекомендован**: Защита от спуфинга
   - Решение: Сделать опциональным, но логировать warning если не установлен

---

## КРИТЕРИИ ПРИЕМКИ

### Сценарные критерии (Given-When-Then)

#### Сценарий 1: Запуск в polling режиме (default)

```gherkin
Given конфигурация не содержит BOT_MODE или BOT_MODE=polling
When запускается приложение через python main.py
Then бот стартует в polling режиме
And в логах появляется "Starting bot in polling mode"
And бот успешно получает updates через polling
```

#### Сценарий 2: Запуск в webhook режиме с валидной конфигурацией

```gherkin
Given в .env установлены:
  - BOT_MODE=webhook
  - WEBHOOK_URL=https://example.com/webhook
  - WEBHOOK_SECRET=mysecret123
  - WEBHOOK_PORT=8443
When запускается приложение
Then бот регистрирует webhook в Telegram API
And HTTP сервер запускается на порту 8443
And в логах появляется "Webhook registered successfully"
And бот получает updates через POST запросы на /webhook
```

#### Сценарий 3: Ошибка при неполной webhook конфигурации

```gherkin
Given в .env установлено BOT_MODE=webhook
And WEBHOOK_URL не задан
When приложение пытается запуститься
Then возникает ValidationError от Pydantic
And в ошибке указано "webhook_url is required when bot_mode is webhook"
And приложение не запускается
```

#### Сценарий 4: Переключение с webhook на polling

```gherkin
Given бот ранее работал в webhook режиме
And webhook был зарегистрирован в Telegram
When в .env меняется BOT_MODE на polling
And приложение перезапускается
Then бот удаляет старый webhook через deleteWebhook API
And в логах появляется "Webhook removed, switching to polling"
And бот запускается в polling режиме
```

#### Сценарий 5: Невалидный webhook URL (не HTTPS)

```gherkin
Given в .env установлено:
  - BOT_MODE=webhook
  - WEBHOOK_URL=http://example.com/webhook (HTTP, не HTTPS)
When приложение пытается запуститься
Then возникает ValidationError
And в ошибке указано "webhook_url must use HTTPS protocol"
```

### Правила и ограничения

- [ ] Если `bot_mode=webhook`, то `webhook_url` обязателен (ValidationError если отсутствует)
- [ ] `webhook_url` должен начинаться с `https://` (HTTP не допустим)
- [ ] `webhook_port` должен быть одним из: 80, 88, 443, 8443
- [ ] При старте в polling режиме, существующий webhook должен быть удален
- [ ] При старте в webhook режиме, бот должен вызвать `set_webhook()` перед `run_webhook()`
- [ ] Если `webhook_secret` не задан, вывести WARNING в логи

### Тестирование

- [ ] Unit-тесты для Settings валидации (webhook_url, bot_mode, port)
- [ ] Integration-тест: запуск в polling режиме
- [ ] Integration-тест: запуск в webhook режиме (с mock Telegram API)
- [ ] Тест проверки удаления webhook при переключении на polling
- [ ] Тест валидации: ошибка при webhook mode без URL
- [ ] Тест валидации: ошибка при HTTP URL
- [ ] Ручное тестирование с ngrok для webhook режима

### Код-ревью

- [ ] Код соответствует существующему стилю проекта
- [ ] Используется loguru для всех логов
- [ ] Нет хардкода: все параметры через settings
- [ ] Docstrings добавлены для новых функций
- [ ] Type hints для всех параметров и возвратов

### Документация

- [ ] `.env.example` обновлен с webhook параметрами
- [ ] README.md содержит секцию про webhook режим
- [ ] Комментарии в коде объясняют webhook логику
- [ ] Примеры для development (polling) и production (webhook)

---

## ПЛАН РЕАЛИЗАЦИИ

### Этапы выполнения

#### Этап 1: Обновление Settings

**Описание:** Добавить webhook конфигурационные поля в Pydantic Settings

**Задачи:**
- [ ] Добавить enum `BotMode` с вариантами `polling` и `webhook`
- [ ] Добавить поля: `bot_mode`, `webhook_url`, `webhook_secret`, `webhook_port`, `webhook_path`
- [ ] Создать custom validator `@field_validator` для `webhook_url` (HTTPS проверка)
- [ ] Создать custom validator для `webhook_port` (только 80, 88, 443, 8443)
- [ ] Добавить `@model_validator` для проверки: если webhook, то URL обязателен
- [ ] Обновить docstrings для всех новых полей

**Валидация:**
- Создать тестовый `.env` с webhook параметрами
- Запустить `python -c "from promptheus.config import get_settings; print(get_settings())"` 
- Убедиться что settings загружаются без ошибок
- Тест с невалидным URL (HTTP) → должна быть ValidationError
- Тест с webhook mode но без URL → должна быть ValidationError

#### Этап 2: Добавление webhook логики в main.py

**Описание:** Реализовать conditional startup logic для polling vs webhook

**Задачи:**
- [ ] Создать async функцию `start_bot_polling(application, settings)`
- [ ] Создать async функцию `start_bot_webhook(application, settings)`
- [ ] Обновить `main()`: добавить if/else на основе `settings.bot_mode`
- [ ] В `start_bot_webhook()`: вызвать `application.bot.set_webhook()`
- [ ] В `start_bot_webhook()`: вызвать `application.run_webhook()`
- [ ] В `start_bot_polling()`: вызвать `application.bot.delete_webhook()` (очистка)
- [ ] В `start_bot_polling()`: вызвать `application.updater.start_polling()`
- [ ] Добавить обработку ошибок с graceful fallback
- [ ] Добавить логирование для каждого режима

**Валидация:**
- Запустить бота с `BOT_MODE=polling` → должен работать как раньше
- Проверить логи: "Starting bot in polling mode"
- Запустить с `BOT_MODE=webhook` (с валидным URL) → не должно быть ошибок в startup
- Проверить логи: "Starting bot in webhook mode", "Webhook registered"

#### Этап 3: Обновление документации

**Описание:** Создать и обновить документацию для webhook режима

**Задачи:**
- [ ] Создать `.env.example` если не существует
- [ ] Добавить секцию `# Bot Mode Configuration` в `.env.example`
- [ ] Добавить примеры для polling и webhook режимов
- [ ] Обновить README.md: добавить секцию "Bot Modes"
- [ ] Описать как настроить webhook для production
- [ ] Описать как использовать ngrok для local testing
- [ ] Добавить troubleshooting секцию для webhook проблем

**Валидация:**
- Прочитать документацию как новый разработчик
- Убедиться что все шаги понятны и выполнимы
- Проверить что примеры `.env` корректны

#### Этап 4: Тестирование

**Описание:** Написать и запустить тесты для новой функциональности

**Задачи:**
- [ ] Создать `tests/test_config.py` (если не существует)
- [ ] Написать тест: `test_settings_polling_mode_default()`
- [ ] Написать тест: `test_settings_webhook_mode_requires_url()`
- [ ] Написать тест: `test_webhook_url_must_be_https()`
- [ ] Написать тест: `test_webhook_port_validation()`
- [ ] Создать `tests/test_main_startup.py` (опционально)
- [ ] Написать integration тест для polling startup
- [ ] Написать integration тест для webhook startup (с mock)
- [ ] Запустить все тесты: `pytest tests/ -v`

**Валидация:**
- Все новые тесты проходят (green)
- Coverage для новых функций >= 80%
- Существующие тесты не сломаны

#### Этап 5: Ручное тестирование (опционально)

**Описание:** Протестировать webhook режим с реальным Telegram API

**Задачи:**
- [ ] Установить ngrok: `brew install ngrok` (или с сайта)
- [ ] Запустить ngrok: `ngrok http 8443`
- [ ] Скопировать HTTPS URL из ngrok (например, https://abc123.ngrok.io)
- [ ] Обновить `.env`: `WEBHOOK_URL=https://abc123.ngrok.io/webhook`
- [ ] Установить `BOT_MODE=webhook`
- [ ] Запустить бота: `uv run python src/promptheus/main.py`
- [ ] Отправить `/start` в Telegram боту
- [ ] Проверить ngrok dashboard: должен быть POST запрос
- [ ] Проверить логи бота: update должен быть обработан

**Валидация:**
- Бот отвечает на команды в webhook режиме
- Логи показывают incoming webhook requests
- Нет ошибок в обработке updates

---

## ТЕСТИРОВАНИЕ И ВАЛИДАЦИЯ

### Unit-тесты

```python
# tests/test_config.py
import pytest
from pydantic import ValidationError
from promptheus.config.settings import Settings

def test_settings_default_bot_mode_is_polling():
    """Test that default bot mode is polling."""
    # Given: minimal env without BOT_MODE
    settings = Settings(
        telegram_bot_token="test_token",
        openrouter_api_key="test_key"
    )
    
    # Then: bot_mode defaults to polling
    assert settings.bot_mode == "polling"


def test_webhook_mode_requires_webhook_url():
    """Test that webhook mode requires webhook_url."""
    # Given: BOT_MODE=webhook but no webhook_url
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            bot_mode="webhook"
            # webhook_url not provided
        )
    
    # Then: ValidationError is raised
    assert "webhook_url is required" in str(exc_info.value)


def test_webhook_url_must_be_https():
    """Test that webhook URL must use HTTPS."""
    # Given: webhook_url with HTTP (not HTTPS)
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            bot_mode="webhook",
            webhook_url="http://example.com/webhook"  # HTTP!
        )
    
    # Then: ValidationError for non-HTTPS
    assert "must use HTTPS" in str(exc_info.value)


def test_webhook_port_must_be_valid():
    """Test that webhook port is one of allowed values."""
    # Given: invalid port
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            bot_mode="webhook",
            webhook_url="https://example.com/webhook",
            webhook_port=9999  # Invalid port!
        )
    
    # Then: ValidationError for invalid port
    assert "must be one of" in str(exc_info.value)


def test_valid_webhook_configuration():
    """Test that valid webhook config is accepted."""
    # Given: complete valid webhook config
    settings = Settings(
        telegram_bot_token="test_token",
        openrouter_api_key="test_key",
        bot_mode="webhook",
        webhook_url="https://example.com/webhook",
        webhook_secret="my_secret",
        webhook_port=8443
    )
    
    # Then: settings are valid
    assert settings.bot_mode == "webhook"
    assert settings.webhook_url == "https://example.com/webhook"
    assert settings.webhook_port == 8443
```

### Команды для запуска

```bash
# Установить зависимости (если еще не установлены)
uv sync

# Запустить все тесты
uv run pytest tests/ -v

# Запустить только тесты config
uv run pytest tests/test_config.py -v

# С покрытием
uv run pytest tests/test_config.py --cov=src/promptheus/config

# Линтер (проверить новый код)
uv run ruff check src/promptheus/config/settings.py
uv run ruff check src/promptheus/main.py

# Type checker
uv run mypy src/promptheus/config/settings.py
uv run mypy src/promptheus/main.py

# Запустить бота в polling режиме (для теста)
uv run python src/promptheus/main.py

# Запустить с webhook (требует ngrok и настройку .env)
# 1. Terminal 1: ngrok http 8443
# 2. Обновить .env: WEBHOOK_URL=<ngrok-url>/webhook, BOT_MODE=webhook
# 3. Terminal 2: uv run python src/promptheus/main.py
```

### Сценарии ручного тестирования

1. **Polling режим (baseline)**
   - Убедиться что в `.env` установлено `BOT_MODE=polling` или вообще не задано
   - Запустить: `uv run python src/promptheus/main.py`
   - Проверить логи: должно быть "Starting bot in polling mode"
   - Отправить `/start` боту в Telegram
   - Проверить: бот отвечает корректно

2. **Webhook режим с ngrok**
   - Установить ngrok если не установлен
   - Запустить: `ngrok http 8443`
   - Скопировать HTTPS URL из ngrok (например, `https://abc123.ngrok.io`)
   - Обновить `.env`:
     ```
     BOT_MODE=webhook
     WEBHOOK_URL=https://abc123.ngrok.io/webhook
     WEBHOOK_SECRET=test_secret_123
     WEBHOOK_PORT=8443
     ```
   - Запустить бота: `uv run python src/promptheus/main.py`
   - Проверить логи: "Starting bot in webhook mode", "Webhook registered"
   - Открыть ngrok web interface: http://127.0.0.1:4040
   - Отправить `/start` боту
   - Проверить ngrok: должен быть POST запрос на `/webhook`
   - Проверить логи бота: update обработан

3. **Переключение с polling на webhook**
   - Запустить бота в polling режиме
   - Остановить бота (Ctrl+C)
   - Изменить `.env`: `BOT_MODE=webhook` (с валидным WEBHOOK_URL)
   - Запустить бота снова
   - Проверить логи: "Removing old webhook" или "Webhook removed"
   - Проверить: webhook зарегистрирован и работает

4. **Валидация: webhook без URL**
   - Установить в `.env`: `BOT_MODE=webhook`
   - Удалить или закомментировать `WEBHOOK_URL`
   - Попытаться запустить бота
   - Ожидается: ValidationError с сообщением о необходимости webhook_url

5. **Валидация: HTTP URL**
   - Установить в `.env`:
     ```
     BOT_MODE=webhook
     WEBHOOK_URL=http://example.com/webhook
     ```
   - Попытаться запустить бота
   - Ожидается: ValidationError о необходимости HTTPS

---

## ДОПОЛНИТЕЛЬНЫЕ СООБРАЖЕНИЯ

### Риски

- **Риск: ngrok tunnel нестабилен для длительного тестирования**
  - Митигация: Документировать что ngrok только для dev тестов, для production использовать реальный домен с SSL

- **Риск: Webhook требует дополнительной инфраструктуры (reverse proxy, SSL)**
  - Митигация: Добавить в документацию примеры с nginx, указать на необходимость SSL сертификата

- **Риск: Сложности при отладке webhook (нет прямого доступа к HTTP запросам)**
  - Митигация: Добавить debug логирование входящих webhook requests, рекомендовать ngrok inspect

### Предположения

- Разработчики используют polling для local development
- Production развертывание будет на сервере с публичным IP и доменом
- SSL сертификат будет настроен администраторами (Let's Encrypt, Cloudflare, etc.)
- Для MVP достаточно базовой реализации webhook без advanced features

### Ограничения

- Не реализуем custom HTTP сервер (используем встроенный в python-telegram-bot)
- Не добавляем advanced webhook features (IP whitelist, custom headers, etc.)
- Webhook secret опционален (хотя рекомендован)
- Нет автоматической настройки SSL (требуется external setup)

### Будущие улучшения

- [ ] Health check endpoint для webhook сервера (`/health`)
- [ ] Metrics endpoint для мониторинга (`/metrics`)
- [ ] IP whitelist для webhook requests (только Telegram IP ranges)
- [ ] Rate limiting на webhook endpoint
- [ ] Автоматический fallback на polling при webhook failures
- [ ] Dashboard для управления webhook конфигурацией
- [ ] Integration с Cloudflare для автоматического SSL

### Вопросы и нерешенные моменты

- [ ] Нужен ли отдельный endpoint для manual webhook testing?
- [ ] Добавлять ли health check в MVP или отложить?
- [ ] Стоит ли валидировать webhook_url доступность при startup?
- [ ] Нужно ли логировать все webhook requests или только ошибки?

---

## ЧЕКЛИСТ ВЫПОЛНЕНИЯ

### Разработка

- [ ] Добавлены поля в `Settings`: `bot_mode`, `webhook_url`, `webhook_secret`, `webhook_port`, `webhook_path`
- [ ] Создан `BotMode` enum с вариантами `polling` и `webhook`
- [ ] Добавлен `@field_validator` для `webhook_url` (HTTPS проверка)
- [ ] Добавлен `@field_validator` для `webhook_port` (проверка допустимых портов)
- [ ] Добавлен `@model_validator` для проверки: webhook требует URL
- [ ] Создана функция `start_bot_polling(application, settings)` в `main.py`
- [ ] Создана функция `start_bot_webhook(application, settings)` в `main.py`
- [ ] Обновлена функция `main()`: добавлен if/else на основе `bot_mode`
- [ ] Добавлено логирование режима запуска
- [ ] Добавлена обработка ошибок при webhook setup
- [ ] Добавлено удаление старого webhook при polling режиме

### Тестирование

- [ ] Написан тест: `test_settings_default_bot_mode_is_polling()`
- [ ] Написан тест: `test_webhook_mode_requires_webhook_url()`
- [ ] Написан тест: `test_webhook_url_must_be_https()`
- [ ] Написан тест: `test_webhook_port_must_be_valid()`
- [ ] Написан тест: `test_valid_webhook_configuration()`
- [ ] Все unit-тесты проходят
- [ ] Coverage для `settings.py` >= 85%
- [ ] Ручное тестирование polling режима выполнено
- [ ] Ручное тестирование webhook режима с ngrok выполнено (опционально)

### Документация

- [ ] Создан или обновлен `.env.example` с webhook параметрами
- [ ] Добавлена секция "Bot Modes" в `README.md`
- [ ] Добавлены примеры конфигурации для polling
- [ ] Добавлены примеры конфигурации для webhook
- [ ] Добавлена инструкция по использованию ngrok для local testing
- [ ] Добавлена troubleshooting секция для webhook проблем
- [ ] Docstrings обновлены для новых функций
- [ ] Комментарии в коде для сложной webhook логики

### Качество кода

- [ ] `ruff check` не выдает ошибок для измененных файлов
- [ ] `mypy` проверка проходит без ошибок
- [ ] Type hints добавлены для всех новых функций и параметров
- [ ] Нет TODO/FIXME в коде
- [ ] Код соответствует существующему стилю проекта
- [ ] Логирование использует loguru с context binding

### Финализация

- [ ] Изменения закоммичены с понятным сообщением:
  - `feat: add webhook mode support for Telegram bot`
  - `docs: update configuration examples for webhook mode`
  - `test: add validation tests for webhook settings`
- [ ] Проверено что изменения не ломают существующий функционал (backward compatibility)
- [ ] Pull request создан с описанием изменений
- [ ] CI/CD pipeline проходит успешно (если настроен)
- [ ] Issue PRMT-DOC-3.2 переведена в статус "Ready for Review"

---

## ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

### Пример .env для разработки (polling)

```bash
# .env для development (polling mode)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database
DATABASE_URL=sqlite:///./data/promptheus.db

# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Bot Mode (polling for development)
BOT_MODE=polling
# Webhook parameters not needed in polling mode
```

### Пример .env для production (webhook)

```bash
# .env для production (webhook mode)
TELEGRAM_BOT_TOKEN=your_production_bot_token
OPENROUTER_API_KEY=your_production_api_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/promptheus

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# Bot Mode (webhook for production)
BOT_MODE=webhook
WEBHOOK_URL=https://yourdomain.com/webhook
WEBHOOK_SECRET=your_secure_random_secret_here
WEBHOOK_PORT=8443
WEBHOOK_PATH=/webhook
```

### Nginx конфигурация для webhook (пример для production)

```nginx
# /etc/nginx/sites-available/promptheus
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8443/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Telegram API webhook требования (справка)

Согласно [Telegram Bot API документации](https://core.telegram.org/bots/api#setwebhook):

- **URL**: Должен начинаться с `https://`
- **Порты**: Только 80, 88, 443, 8443
- **SSL**: Обязателен (Let's Encrypt, Cloudflare, или self-signed)
- **IP Ranges**: Webhook запросы приходят с Telegram IP (149.154.160.0/20, 91.108.4.0/22)
- **Secret Token**: До 256 символов, отправляется в заголовке `X-Telegram-Bot-Api-Secret-Token`

---

**Версия документа:** 1.0.0  
**Последнее обновление:** 2025-11-05  
**Автор плана:** AI Assistant  
**Связанные задачи:** PRMT-DOC-3.2  
**Статус:** Ready for Implementation
