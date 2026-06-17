# Chameleon LLM Gateway - OpenAPI Спецификация

**Версия**: 1.0.0  
**Описание**: HTTP API для маршрутизации запросов к LLM моделям

---

## Общая информация

- **Title**: Chameleon LLM Gateway
- **Version**: 1.0.0
- **Description**: LLM model router and cache
- **Host**: localhost:8003
- **Base Path**: /
- **Schemes**: http

---

## Endpoints

### 1. Health Check

```yaml
GET /health
```

**Описание**: Проверка состояния сервиса

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "ollama:qwen2.5:1.5b": "ok",
    "yandex:ya-llm": "ok",
    "cache": "ok"
  }
}
```

**Статусы**:
- `healthy` - все компоненты работают
- `degraded` - часть компонентов недоступна
- `unhealthy` - критические ошибки

---

### 2. Generate Text

```yaml
POST /generate
```

**Описание**: Генерация текста с использованием адекватной модели

**Request Body**:
```json
{
  "prompt": "Привет, как дела?",
  "complexity": 2,
  "config": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "style": "chekhov"
  }
}
```

**Request Parameters**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `prompt` | string | Yes | Текст для генерации |
| `complexity` | integer | No | Сложность запроса (1=fast, 2=balanced, 3=powerful) |
| `config` | object | No | Дополнительная конфигурация |

**Complexity Values**:
- `1` - Fast (быстрая генерация)
- `2` - Balanced (сбалансированная)
- `3` - Powerful (качественная генерация)

**Response**:
```json
{
  "text": "Привет! У меня всё отлично, спасибо за интерес!",
  "model_used": "qwen2.5:1.5b",
  "complexity_used": 2,
  "token_usage": {
    "prompt_tokens": 15,
    "completion_tokens": 25,
    "total_tokens": 40
  },
  "latency_ms": 120,
  "from_cache": false
}
```

**Response Parameters**:

| Поле | Тип | Описание |
|------|-----|----------|
| `text` | string | Сгенерированный текст |
| `model_used` | string | Использованная модель |
| `complexity_used` | integer | Использованная сложность |
| `token_usage` | object | Использование токенов |
| `latency_ms` | integer | Время генерации (мс) |
| `from_cache` | boolean | Взят ли из кэша |

**Errors**:
- `400 Bad Request` - Неверный запрос
- `500 Internal Server Error` - Ошибка генерации

---

### 3. Get Models

```yaml
GET /models
```

**Описание**: Получение списка доступных моделей

**Response**:
```json
{
  "fast": "qwen2.5:1.5b",
  "balanced": "qwen2.5:1.5b",
  "powerful": "llama3.2:3b"
}
```

---

## Схемы данных

### GenerateRequest

```yaml
prompt: string (required)
complexity: integer (default: 2)
config: GenerationConfig
```

### GenerationConfig

```yaml
temperature: float (default: 0.7)
max_tokens: integer (default: 2048)
stream: boolean (default: false)
style: string (optional)
```

### GenerateResponse

```yaml
text: string
model_used: string
complexity_used: integer
token_usage: TokenUsage
latency_ms: integer
from_cache: boolean
```

### TokenUsage

```yaml
prompt_tokens: integer
completion_tokens: integer
total_tokens: integer
```

### HealthResponse

```yaml
status: string (healthy, degraded, unhealthy)
version: string
checks: object
```

---

## Примеры запросов

### Простая генерация

```bash
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Привет, как дела?",
    "complexity": 2
  }'
```

### Генерация со стилем

```bash
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Напиши письмо",
    "complexity": 2,
    "config": {
      "temperature": 0.8,
      "style": "chekhov"
    }
  }'
```

### Проверка статуса

```bash
curl http://localhost:8003/health
```

---

## Метрики

Все endpoints поддерживают Prometheus метрики:

- `chameleon_llm_calls_total` - вызовы LLM
- `chameleon_request_latency_seconds` - задержка запросов
- `chameleon_cache_hits_total` - попадания в кэш
- `chameleon_token_usage` - использование токенов

---

### Модели по умолчанию

| Сложность | Модель | Провайдер | Описание |
|-----------|--------|-----------|----------|
| Fast | qwen2.5:1.5b | Ollama | Быстрая генерация (primary) |
| Balanced | qwen2.5:1.5b | Ollama | Сбалансированная |
| Powerful | llama3.2:3b | Ollama | Качественная генерация (fallback) |

**Fallback цепочка:** ollama:qwen2.5:1.5b → yandex:ya-llm

**Порог circuit breaker:** 5 ошибок → 30 сек recovery timeout

---

## Ошибки

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate response"
}
```

### 503 Service Unavailable
```json
{
  "detail": "All fallback providers failed"
}
```

---

## Документация в формате OpenAPI

Скачать JSON/SWAGGER версию:
- `GET /openapi.json` - OpenAPI JSON
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc
