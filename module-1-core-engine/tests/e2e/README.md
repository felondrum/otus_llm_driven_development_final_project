# E2E Тесты Core Engine

Этот каталог содержит end-to-end тесты для модуля Core Engine.

## Структура тестов

- `test_full_flow.py` - Полные потоки обработки сообщений
- `test_basic_adaptation.py` - Базовая адаптация текста
- `test_fallbacks.py` - Тесты сценариев отказоустойчивости

## Запуск тестов

### Способ 1: Через Makefile (рекомендуется)

```bash
# Подготовить среду и запустить тесты
make e2e-setup
make test-e2e

# Или отдельно
make e2e-setup  # Только подготовка
make test-e2e   # Только тесты
```

### Способ 2: Вручную

```bash
# 1. Запустить инфраструктуру
docker-compose -f docker-compose.module.yml up -d

# 2. Подождать инициализации (30-60 секунд)
sleep 30

# 3. Загрузить демо данные
poetry run python scripts/e2e_load_demo_data.py

# 4. Запустить тесты
poetry run pytest tests/e2e/ -v
```

## Требования

- Docker и Docker Compose
- Python 3.11+
- poetry
- Оперативная память: минимум 8GB

## Что тестируется

### test_full_flow.py
- Проверка здоровья всех сервисов через gRPC
- Обработка сообщений от отправителя к получателю
- Формальное обращение (к менеджерам, директорам)
- Сценарии с обвинениями (правило "не обвиняй")
- Генерация текста с литературными стилями
- RAG поиск профилей, правил и стилей

### test_basic_adaptation.py
- Базовая адаптация текста
- Применение корпоративных правил
- Проверка кэширования
- Обработка несуществующих профилей

## Настройка окружения

### Переменные окружения

```bash
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_PORT=8001
RETRIEVER_HOST=localhost
RETRIEVER_PORT=8002
LLM_GATEWAY_URL=http://localhost:8003
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_PASSWORD=redis123
```

### Загрузка демо данных

Скрипт `e2e_load_demo_data.py` загружает данные из `demo_data/` в Qdrant:

- `profiles.json` - Профили пользователей
- `rules.json` - Корпоративные правила
- `styles.json` - Литературные стили

## Примеры тестовых сценариев

### Формальное обращение к менеджеру

**Исходное сообщение:**
```
Иван, ты должен проверить код
```

**Адаптированное сообщение:**
```
Иван Петрович, вы должны проверить код
```

### Обработка обвинения

**Исходное сообщение:**
```
Петр, ты сломал сборку!
```

**Адаптированное сообщение:**
```
Сборка не работает корректно
```

## Примечания

- Все тесты используют реальные сервисы (Ollama, Qdrant, Redis)
- Тесты могут занимать 2-3 минуты на запуск
- Для отладки используйте флаг `-s` для вывода логов
- Включите подробный вывод с флагом `-v`

## Отладка

```bash
# Запуск конкретного теста
poetry run pytest tests/e2e/test_full_flow.py::TestOrchestratorService::test_process_message_formal_to_manager -v -s

# Запуск с логами
poetry run pytest tests/e2e/ -v -s --log-cli-level=INFO

# Запуск с покрытием
poetry run pytest tests/e2e/ --cov=src --cov-report=term-missing
```

## CI/CD

В CI/CD e2e тесты запускаются после:
1. Сборки контейнеров
2. Запуска инфраструктуры
3. Загрузки демо данных

```yaml
# Пример GitHub Actions шага
- name: Setup and run e2e tests
  run: |
    make e2e-setup
    make test-e2e
```
