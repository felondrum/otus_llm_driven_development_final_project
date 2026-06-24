# README Модуля 1 - Core Engine

## Обзор

Модуль Core Engine - это сердце системы Chameleon Chat. Он отвечает за адаптацию сообщений с использованием LLM, ретривер RAG данных и маршрутизацию запросов к различным моделям.

### Основные компоненты

- **Orchestrator** - координирует процесс адаптации, вызывает Retriever и LLM Gateway
- **Retriever** - предоставляет RAG данные (профили, правила, стили, корпоративная культура) из Qdrant
- **LLM Gateway** - маршрутизирует запросы к различным LLM провайдерам (Ollama, Yandex LLM)
- **Langfuse** - трейсинг и мониторинг LLM приложений (опционально)

### Новая функциональность: RAG для корпоративной культуры

Система поддерживает загрузку и поиск векторных данных корпоративной культуры:

- **Документация**: `demo_data/corporate_culture.md` - Markdown документ с ценностями, принципами и примерами
- **CLI утилита**: `scripts/ingest_corporate_culture.py` - загрузка документа в Qdrant
- **Поиск**: `SearchCulture` gRPC метод и `get_culture_chunks()` - векторный поиск релевантных фрагментов
- **Промпт**: Корпоративная культура автоматически добавляется в промпт для адаптации сообщений

**Использование в адаптации:**
1. Генерирует эмбеддинг запроса (исходный текст + style + role + department)
2. Ищет релевантные фрагменты корпоративной культуры в Qdrant
3. Добавляет их в промпт для LLM
4. LLM учитывает культуру при переделывании сообщения

**Тесты:**
```bash
# Юнит тесты chunking и embeddings
poetry run pytest tests/unit/retriever/test_chunking.py -v

# E2E тесты RAG культуры
poetry run pytest tests/e2e/test_culture_rag.py -v

# Интеграция в контекст
poetry run pytest tests/e2e/test_culture_in_prompts.py -v
```

### Работа с профилями пользователей

Система адаптирует сообщения с учетом профиля получателя. Профили загружаются из `demo_data/profiles.json` и хранятся в Qdrant.

#### Важно: Используйте правильный `user_id`

Профили в системе хранятся с `user_id` в формате:
- `alex_i` (для Иванова Алексея)
- `petr_s` (для Смирнова Петра)
- `anna_k` (для Ковалевой Анны)

При отправке сообщения используйте **`user_id`**, а не имя пользователя:
```python
recipient_id = "alex_i"  # ПРАВИЛЬНО
# recipient_id = "Иван"  # НЕПРАВИЛЬНО - профиль не будет найден
```

#### Найти правильный `user_id`

Используйте скрипт поиска профиля по имени:
```bash
python scripts/find_profile_by_name.py Иван
```

Результат:
```
user_id: alex_i
full_name: Иванов Алексей Петрович
role: engineer
department: backend
```

#### Загрузка профилей

При первом запуске Docker Compose профили загружаются автоматически через `e2e_load_demo_data.py`. Для ручной загрузки:
```bash
python scripts/e2e_load_demo_data.py
```

#### Проверка загрузки профилей

```bash
# Проверка количества профилей в Qdrant
docker exec chameleon-qdrant curl http://localhost:6333/collections/user_profiles/points/count

# Диагностика поиска профилей
docker exec -it chameleon-retriever python scripts/test_profile_lookup.py
```

#### Тест полного потока

```bash
# Тест с реальными профилями
docker exec -it chameleon-orchestrator python scripts/test_profile_full_flow.py
```

**Документация**: Полное руководство по работе с профилями см. в `docs/PROFILE_FIX.md` и `docs/PROFILE_FIX_QUICK.md`.

### Стек технологий

- Python 3.11+
- FastAPI (HTTP API)
- gRPC (внутреннее взаимодействие)
- Qdrant (векторная БД)
- Redis (кэш)
- Ollama (локальные LLM: qwen2.5:1.5b)
- Yandex LLM API (Fallback провайдер)

## Установка

```bash
cd module-1-core-engine

# Установка зависимостей
poetry install
```

## Конфигурация

Конфигурация находится в `config/`:
- `development.yaml` - настройки разработки
- `production.yaml` - настройки продакшна
- `models.yaml` - конфигурация моделей

### Переменные окружения

Создайте файл `.env` в корне модуля:

```bash
cp .env.example .env
# Обновите переменные в .env (YA_LLM_KEY, YA_HOST_KEY и др.)
```

Полный список переменных см. в `.env.example`.

## Запуск

### Подготовка

Создайте файл `.env` в корне модуля:

```bash
cd module-1-core-engine
cp .env.example .env
# Обновите переменные в .env (YA_LLM_KEY, YA_HOST_KEY и др.)
```

### Локально

```bash
# Запуск через poetry
poetry run python -m src.orchestrator.main
poetry run python -m src.retriever.main
poetry run python -m src.llm_gateway.main
```

### Через Docker

```bash
# Создайте .env файл перед запуском
cp .env.example .env
# Обновите переменные в .env

# Запуск всей инфраструктуры
docker-compose -f docker-compose.module.yml up -d

# Запуск только оркестратора
docker-compose -f docker-compose.module.yml up orchestrator

# Запуск всех сервисов
make run
```

## API Endpoints

### gRPC HealthCheck Endpoints

Все gRPC сервисы поддерживают HealthCheck через `grpcurl`:

```bash
# Установка grpcurl (macOS)
brew install grpcurl

# Or via docker
alias grpcurl='docker run --rm -it --network=host fullstory/grpcurl'

# Проверка всех сервисов
docker exec -it container_name grpcurl -plaintext localhost:8001 list
docker exec -it container_name grpcurl -plaintext localhost:8002 list
docker exec -it container_name grpcurl -plaintext localhost:8004 list

# Проверка HealthCheck
docker exec -it container_name grpcurl -plaintext localhost:8001 chameleon.core.v1.OrchestratorService/HealthCheck
docker exec -it container_name grpcurl -plaintext localhost:8002 chameleon.core.v1.RetrieverService/HealthCheck
docker exec -it container_name grpcurl -plaintext localhost:8004 chameleon.core.v1.LLMGatewayService/HealthCheck
```

### LLM Gateway (HTTP)

- `GET /health` - проверка состояния
- `POST /generate` - генерация текста
- `GET /models` - список доступных моделей

### Retriever (gRPC)

- `GetProfile` - получить профиль пользователя
- `GetRules` - получить корпоративные правила
- `GetStyleExamples` - получить примеры стилей
- `SearchRules` - поиск правил
- `SearchCulture` - поиск в корпоративной культуре (RAG)

### Orchestrator (gRPC)

- `ProcessMessage` - обработать сообщение
- `HealthCheck` - проверка состояния

## Структура проекта

```
module-1-core-engine/
├── src/
│   ├── common/         # Общие компоненты
│   │   ├── schemas.py  # Схемы данных
│   │   ├── logging.py  # Логирование
│   │   ├── metrics.py  # Prometheus метрики
│   │   └── langfuse_integration.py  # Локальный Langfuse client
│   ├── orchestrator/   # Оркестратор
│   ├── retriever/      # Ретривер RAG
│   └── llm_gateway/    # Шлюз LLM
├── protos/             # gRPC протобуферы
│   ├── common.proto    # Общие сообщения (HealthStatus)
│   ├── orchestrator.proto
│   ├── retriever.proto
│   └── llm_gateway.proto
├── config/             # Конфигурация
├── demo_data/          # Демо данные для RAG
│   ├── profiles.json   # Профили пользователей
│   ├── rules.json      # Корпоративные правила
│   ├── styles.json     # Литературные стили
│   └── corporate_culture.md
└── scripts/            # Скрипты
    ├── generate_proto.sh
    └── ingest_corporate_culture.py
```

## Генерация gRPC stubs

При изменении `.proto` файлов запустите генерацию stubs:

```bash
# Сгенерировать все stubs
poetry run bash scripts/generate_proto.sh

# Или вручную
poetry run python -m grpc_tools.protoc -Iprotos --python_out=src --grpc_python_out=src protos/common.proto protos/orchestrator.proto protos/retriever.proto protos/llm_gateway.proto
mv src/*_pb2*.py src/chameleon/core/v1/
```

### Текущие протобуферы версии v1:

**Orchestrator:**
- `ProcessMessage` - обработка сообщения
- `HealthCheck` - проверка состояния

**Retriever:**
- `GetProfile` - получение профиля
- `GetRules` - получение правил
- `GetStyleExamples` - получение стилей
- `SearchRules` - поиск правил
- `SearchCulture` - поиск в культуре (НОВЫЙ)
- `HealthCheck` - проверка состояния

**LLM Gateway:**
- `Generate` - генерация текста
- `StreamGenerate` - стриминг генерации
- `GetModelStatus` - статус моделей
- `HealthCheck` - проверка состояния

**HTTP Endpoints (LLM Gateway):**
- `POST /generate` - генерация текста
- `GET /health` - проверка состояния
- `GET /models` - список моделей

## Тестирование

```bash
# Юнит-тесты
poetry run pytest tests/unit/

# Интеграционные тесты
poetry run pytest tests/integration/

# E2E тесты (требует запуска всех сервисов)
poetry run pytest tests/e2e/

# Все тесты
poetry run pytest

# Покрытие кода
poetry run pytest --cov=src --cov-report=term-missing
```

### Запуск e2e тестов

Перед запуском e2e тестов необходимо запустить инфраструктуру:

```bash
# Создайте .env файл
cp .env.example .env
# Обновите переменные в .env

# Запустите инфраструктуру
docker-compose -f docker-compose.module.yml up -d

# Подождите инициализации (60 сек)
# Загрузите демо данные
poetry run python scripts/e2e_load_demo_data.py

# Запустите тесты
poetry run pytest tests/e2e/ -v

# Или через make
make e2e-setup  # Автоматически запустит инфраструктуру и загрузит данные
make test-e2e   # Запустит e2e тесты
```

## E2E Тесты

E2E тесты проверяют полный поток обработки сообщений с реальными сервисами:

- **Orchestrator** через gRPC
- **Retriever** через gRPC
- **LLM Gateway** через HTTP
- **Qdrant** для RAG поиска
- **Ollama** для LLM генерации
- **Redis** для кэширования

### Подготовка среды

Перед запуском e2e тестов:

```bash
# Создайте .env файл
cp .env.example .env
# Обновите переменные в .env

# Запустите инфраструктуру
docker-compose -f docker-compose.module.yml up -d

# Подождите инициализации (60 сек)
# Загрузите демо данные
poetry run python scripts/e2e_load_demo_data.py
```

### Запуск e2e тестов

```bash
# Через make (рекомендуется)
make e2e-setup  # Запустит инфраструктуру и загрузит демо данные
make test-e2e   # Запустит e2e тесты

# Или вручную (сначала создайте .env и запустите инфраструктуру)
docker-compose -f docker-compose.module.yml up -d
poetry run python scripts/e2e_load_demo_data.py
poetry run pytest tests/e2e/ -v
```

### Что тестируется в e2e

1. **Полный поток адаптации**: отправитель → оркестратор → ретривер → LLM → ответ
2. **Формальное обращение**: "Иван, ты должен" → "Иван Петрович, вы должны"
3. **Обработка обвинений**: "ты сломал" → "система не работает корректно"
4. **RAG поиск**: поиск профилей, правил и стилей в Qdrant
5. **Кэширование**: повторные запросы возвращаются из кэша
6. **Fallback**: обработка отсутствующих профилей и ошибок

### Демо данные для e2e

Демо данные загружаются в Qdrant из папки `demo_data/`:

- `profiles.json` - Профили пользователей (employees, managers, directors)
- `rules.json` - Корпоративные правила (формальное обращение, нет обвинений)
- `styles.json` - Литературные стили (чеховский, довлатовский)

Скрипт автоматически загружает данные при первом запуске, если коллекции пусты.

## Демо данные

```bash
# Загрузка демо данных в Qdrant
python scripts/load_demo_data.py

# Загрузка корпоративной культуры
python scripts/ingest_corporate_culture.py \
    --input demo_data/corporate_culture.md \
    --collection corporate_culture \
    --batch-size 50
```

## RAG для корпоративной культуры

Корпоративная культура загружается в Qdrant как векторная коллекция и используется при адаптации сообщений.

### Структура документа

Документ с корпоративной культурой находится в `demo_data/corporate_culture.md` и содержит:

- **Введение** - миссия и ценности компании
- **Основные принципы** - открытость, уважение, командная работа, инновации, качество
- **Примеры поведения** - допустимое и недопустимое поведение
- **Рекомендации** - стиль коммуникации в Chameleon

### Использование в адаптации

При обработке сообщения система автоматически:
1. Генерирует эмбеддинг запроса (исходный текст)
2. Ищет релевантные фрагменты корпоративной культуры
3. Добавляет их в промпт для LLM
4. LLM учитывает культуру при переделывании сообщения

### Тесты

Запустите тесты RAG для корпоративной культуры:

```bash
# Юнит тесты chunking и embeddings
poetry run pytest tests/unit/retriever/test_chunking.py -v

# E2E тесты RAG культуры
poetry run pytest tests/e2e/test_culture_rag.py -v

# Интеграция в контекст
poetry run pytest tests/e2e/test_culture_in_prompts.py -v

# Все тесты
poetry run pytest tests/ -v
```

## Разработка

### Добавление новой модели в LLM Gateway

1. Создайте провайдер в `src/llm_gateway/providers/`
2. Реализуйте интерфейс `LLMProvider`
3. Добавьте провайдер в `fallback_chain` в конфигурации

**Пример Yandex LLM провайдера:**

```python
from .base import LLMProvider

class YandexProvider(LLMProvider):
    async def generate(self, prompt: str, config: GenerationConfig) -> GenerateResponse:
        # Implementation
    
    async def health_check(self) -> bool:
        # Implementation
```

4. Добавьте переменные окружения в `.env.example`

### Добавление нового правила RAG

1. Создайте JSON файл в `demo_data/rules.json`
2. Загрузите данные через скрипт или API админки

## Метрики

Метрики экспортируются в формате Prometheus на порту 9090.

## Langfuse (трейсинг и мониторинг)

Langfuse используется для отслеживания вызовов LLM, метрик и аналитики:

- **Хост**: `http://localhost:5000` (по умолчанию)
- **Веб интерфейс**: `http://localhost:3000`

### Настройка Langfuse

1. Запустите Docker Compose: `docker-compose -f docker-compose.module.yml up -d`
2. Проверьте доступность: `curl http://localhost:3000/api/health`
3. Веб интерфейс доступен по адресу `http://localhost:3000`

### Использование в коде

```python
from common.langfuse_integration import init_langfuse_from_config, start_trace, log_generation
from orchestrator.config import get_config

# Инициализация из конфигурации
config = get_config()
if config.langfuse_enabled:
    init_langfuse_from_config(config)

# Использование трейсов
trace = start_trace("orchestrator-process-message", user_id="user123")
log_generation(
    name="llm-call",
    model="qwen2.5:1.5b",
    prompt=prompt,
    completion=response.text,
)
```

### Конфигурация

```yaml
# config/development.yaml
services:
  langfuse:
    host: http://langfuse:5000
    enabled: true
```

## API Документация

### OpenAPI Спецификация

Документация HTTP API находится в `docs/api/`:
- `openapi.json` - OpenAPI спецификация (JSON)
- `openapi.md` - OpenAPI спецификация (Markdown)

**Доступные endpoints**:
- `GET /health` - проверка состояния сервиса
- `POST /generate` - генерация текста
- `GET /models` - список доступных моделей

**Примеры запросов**:

```bash
# Проверка статуса
curl http://localhost:8003/health

# Генерация текста
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Привет, как дела?", "complexity": 2}'

# Получить модели
curl http://localhost:8003/models
```

### gRPC Документация

Документация gRPC контракта находится в:
- `docs/PROTOCOL.md` - gRPC контракт между модулями

## Решение проблем

### Профили не попадают в промпт

**Проблема**: Отображается "Unknown User" вместо реальных данных профиля.

**Решение**:
1. Проверьте, какой `user_id` используется при отправке сообщения
2. Используйте `find_profile_by_name.py` для поиска правильного `user_id`:
```bash
python scripts/find_profile_by_name.py Иван
```
3. Используйте правильный `user_id` при отправке сообщения

**Документация**: Полное руководство см. в `docs/PROFILE_FIX.md` и `docs/PROFILE_FIX_QUICK.md`.

### Профили не загружаются в Qdrant

**Проверьте**:
```bash
# Проверка количества профилей
docker exec chameleon-qdrant curl http://localhost:6333/collections/user_profiles/points/count

# Загрузка демо данных
docker exec -it chameleon-orchestrator python scripts/e2e_load_demo_data.py
```

### Диагностические скрипты

- `scripts/find_profile_by_name.py` - поиск профиля по имени
- `scripts/test_profile_lookup.py` - диагностика поиска профилей
- `scripts/test_profile_full_flow.py` - полный тест потока с профилями

## Покрытие тестами

**Текущее состояние тестов (финальное ревью):**
- **Всего тестов**: 203
- **Прошли успешно**: 183 (90.1%)
- **Пропущено**: 2 (0.99%)
- **Ошибки**: 0 (0%)

**Распределение по категориям:**
| Категория | Всего | Статус |
|-----------|-------|--------|
| E2E тесты | 32 | ✅ 100% passed |
| Unit тесты | 137 | ✅ 100% passed |
| Integration тесты | 14 | ✅ 14/14 passed (после cleanup) |

**Конкретно для main.py сервисов:**
- `src/orchestrator/main.py` - tested via pytest-docker
- `src/retriever/main.py` - tested via pytest-docker
- `src/llm_gateway/main.py` - tested via pytest-docker

**Запуск тестов:**
```bash
# Все тесты
poetry run pytest tests/ -v

# E2E тесты
poetry run pytest tests/e2e/ -v

# Unit тесты
poetry run pytest tests/unit/ -v

# Покрытие кода
poetry run pytest tests/ --cov=src --cov-report=term-missing
```
