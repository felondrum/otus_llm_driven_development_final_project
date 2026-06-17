# Документ интеграции модулей 1 и 2

**Дата**: 2026-06-15  
**Версия**: 1.0.0

---

## Обзор

Модуль 1 (Core Engine) и Модуль 2 (Chat Frontend) взаимодействуют через gRPC протокол.

```
┌─────────────────┐
│ Module 2        │
│ Chat Frontend   │
│ (WebSocket)     │
└────────┬────────┘
         │ gRPC (ports 8001-8004)
         ▼
┌─────────────────┐
│ Module 1        │
│ Core Engine     │
│ (gRPC Services) │
└─────────────────┘
```

---

## Архитектура взаимодействия

### Компоненты модуля 1

| Сервис | Порт | Протокол | Описание |
|--------|------|----------|----------|
| Orchestrator | 8001 | gRPC | Координация адаптации сообщений |
| Retriever | 8002 | gRPC | RAG данные (профили, правила, стили) |
| LLM Gateway | 8003 | HTTP | Маршрутизация LLM запросов |
| Embedder | 8004 | gRPC | Генерация эмбеддингов |

### Протоколы

1. **gRPC** - основной протокол для внутреннего взаимодействия
2. **HTTP** - для LLM Gateway API
3. **WebSocket** - для чат-интерфейса (модуль 2)

---

## gRPC Контракт

### Модель: chameleon.core.v1

**Location**: `protos/`

| Proto файл | Описание |
|------------|----------|
| `common.proto` | Общие сообщения (HealthStatus) |
| `orchestrator.proto` | Оркестратор сервис |
| `retriever.proto` | Ретривер сервис |
| `llm_gateway.proto` | LLM Gateway сервис |

---

## Основные потоки данных

### 1. Process Message Flow

```
User Input → WebSocket → Module 2
                        ↓
                   gRPC call
                        ↓
              Module 1: Orchestrator
                        ↓
              ┌─────────┴─────────┐
              ▼                   ▼
        GetProfile         GetRules
              ▼                   ▼
         Retriever         Retriever
              ▼                   ▼
           Qdrant          Qdrant
                        ↓
              Assemble Context
                        ↓
              LLM Gateway (HTTP)
                        ↓
                   Generate Text
                        ↓
              Cache Response
                        ↓
              Return Response
```

**Описание**:
1. Модуль 2 получает сообщение через WebSocket
2. Отправляет gRPC запрос Orchestrator (port 8001)
3. Orchestrator вызывает Retriever для получения:
   - Профиля пользователя (cache_ttl: 3600)
   - Корпоративных правил (cache_ttl: 300)
   - Примеров стилей (cache_ttl: 86400)
4. Собирает контекст
5. Вызывает LLM Gateway для генерации
6. Кэширует ответ
7. Возвращает адаптированное сообщение

### 2. Profile Retrieval Flow

```
Module 2
  ↓ (gRPC GetProfile)
Module 1: Retriever
  ↓
Qdrant (user_id)
  ↓
UserProfile
```

**Cache TTL**: 3600 секунд (1 час)

### 3. Rules Retrieval Flow

```
Module 2
  ↓ (gRPC GetRules)
Module 1: Retriever
  ↓
Qdrant (sender_role, recipient_role)
  ↓
[CorporateRule, ...]
```

**Cache TTL**: 300 секунд (5 минут)

### 4. Style Examples Flow

```
Module 2
  ↓ (gRPC GetStyleExamples)
Module 1: Retriever
  ↓
Qdrant (style_name)
  ↓
[StyleExample, ...]
```

**Cache TTL**: 86400 секунд (24 часа)

---

## Таймауты

### gRPC вызовы

Все gRPC вызовы имеют таймаут **5 секунд** (5000ms):

```python
await retriever_stub.GetProfile(
    request,
    timeout=5.0  # 5 seconds
)
```

### HTTP вызовы

LLM Gateway вызовы имеют таймаут **5 секунд**:

```python
async with session.post(url, timeout=aiohttp.ClientTimeout(total=5.0)):
```

---

## Кэширование

### Cache TTL по типу данных

| Тип данных | TTL (сек) | Описание |
|------------|-----------|----------|
| Profile | 3600 | Профиль пользователя |
| Rules | 300 | Корпоративные правила |
| Style Examples | 86400 | Примеры стилей |
| Adaptation | 3600 | Адаптированные сообщения |

### Где кэшируется

1. **Redis** - для кэша RAG данных (Retriever)
2. **LLM Cache** - для кэша генераций (LLM Gateway)

---

## Обработка ошибок

### Not Found

```protobuf
// Profile not found
context.set_code(grpc.StatusCode.NOT_FOUND)
context.set_details(f"Profile not found: {user_id}")
```

**Действие модуля 1**: Создать дефолтный профиль

### Deadline Exceeded (Timeout)

```protobuf
// gRPC timeout
context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
```

**Действие модуля 1**: Fallback на оригинальный текст

### Invalid Argument

```protobuf
// Invalid message format
context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
context.set_details("Invalid message_id format")
```

**Действие модуля 1**: Вернуть ошибку модулю 2

---

## Метрики

### Prometheus метрики

| Метрика | Тип | Описание |
|---------|-----|----------|
| `chameleon_cache_hits_total` | Counter | Кэш попадания |
| `chameleon_cache_ttl_hits_total` | Counter | TTL кэш попадания |
| `chameleon_grpc_timeouts_total` | Counter | gRPC таймауты |
| `chameleon_llm_calls_total` | Counter | Вызовы LLM |
| `chameleon_token_usage` | Summary | Использование токенов |

### Metrics endpoint

Метрики экспортируются в формате Prometheus:
- **Host**: `localhost:9090`
- **Format**: Prometheus text format

---

## Langfuse трейсинг

### Конфигурация

```yaml
services:
  langfuse:
    host: http://langfuse:5000
    enabled: true
```

### Использование

```python
from common.langfuse_integration import start_trace, log_generation

trace = start_trace("orchestrator-process-message", user_id="user123")
log_generation(
    name="llm-call",
    model="qwen2.5:1.5b",
    prompt=prompt,
    completion=response.text,
)
```

**Веб интерфейс**: `http://localhost:3000`

---

## Конфигурация

### module-1-core-engine

**Location**: `config/development.yaml`

```yaml
services:
  redis:
    host: redis
    port: 6379
  
  qdrant:
    host: qdrant
    port: 6333
  
  ollama:
    host: ollama
    port: 11434
  
  langfuse:
    host: http://langfuse:5000
    enabled: true

cache_ttl:
  profile: 3600
  rules: 300
  style_examples: 86400
  adaptation: 3600

fallback:
  chain:
    - ollama:qwen2.5:1.5b
    - yandex:ya-llm
```

### module-2-chat-frontend

**Location**: `.env`

```bash
# Module 1 endpoints
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_PORT=8001
RETRIEVER_HOST=localhost
RETRIEVER_PORT=8002
LLM_GATEWAY_HOST=localhost
LLM_GATEWAY_PORT=8003

# Langfuse (optional)
LANGFUSE_HOST=http://localhost:5000
LANGFUSE_ENABLED=false
```

---

## Docker Compose

### module-1-core-engine

**Location**: `docker-compose.module.yml`

```yaml
services:
  # Redis - кэш для адаптаций
  redis:
    ports:
      - "6379:6379"
  
  # Qdrant - векторная БД
  qdrant:
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
  
  # Ollama - LLM модели
  ollama:
    ports:
      - "11434:11434"
  
  # Langfuse - трейсинг
  langfuse:
    ports:
      - "3000:3000"
      - "5000:5000"
```

### Запуск

```bash
cd module-1-core-engine
docker-compose -f docker-compose.module.yml up -d
```

---

## Тестирование

### Юнит тесты

```bash
poetry run pytest tests/unit/
```

### Интеграционные тесты

```bash
poetry run pytest tests/integration/
```

**Требования**:
- Redis
- Qdrant
- Ollama
- Langfuse (опционально)

---

## Миграции и обновления

### Версия протобуферов

Текущая версия: `chameleon.core.v1`

**Файлы**:
- `protos/common.proto`
- `protos/orchestrator.proto`
- `protos/retriever.proto`
- `protos/llm_gateway.proto`

### Обновление протобуферов

При изменении `.proto` файлов:

```bash
# Сгенерировать новые stubs
poetry run bash scripts/generate_proto.sh

# Исправить импорты
poetry run bash scripts/fix_stub_imports.sh
```

---

## Troubleshooting

### Проблема: gRPC timeout

**Логи**:
```
Retriever timeout: Deadline exceeded
```

**Решение**:
1. Проверить статус Redis: `docker exec -it redis redis-cli ping`
2. Проверить статус Qdrant: `docker exec -it qdrant curl -f http://localhost:6333/health`
3. Увеличить таймаут (не рекомендуется)

### Проблема: Profile not found

**Логи**:
```
Profile not found: user_123
```

**Решение**: Ожидаемое поведение - создается дефолтный профиль

### Проблема: Langfuse connection failed

**Логи**:
```
Failed to connect to Langfuse
```

**Решение**:
1. Проверить статус Langfuse: `curl http://localhost:5000/api/health`
2. Убедиться, что `LANGFUSE_ENABLED=false` в development
3. Проверить NETWORK_MODE в docker-compose

---

## Документация

### module-1-core-engine

- `README.md` - Общий README
- `docs/api/openapi.json` - OpenAPI спецификация
- `docs/api/openapi.md` - OpenAPI в Markdown
- `docs/PROTOCOL.md` - gRPC контракт

### module-2-chat-frontend

- `README.md` - README модуля 2
- `docs/PROTOCOL.md` - gRPC контракт

---

**Автор**: GigaCode AI Assistant  
**Дата создания**: 2026-06-15
