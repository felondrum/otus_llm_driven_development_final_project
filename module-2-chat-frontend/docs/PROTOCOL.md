# gRPC Protocol Documentation - Module 2

**Версия**: 1.0.0  
**Дата**: 2026-06-15  
**Модуль**: Chat Frontend (module-2-chat-frontend)

---

## 📋 Содержание

1. [Введение](#введение)
2. [gRPC Сервисы](#grpc-сервисы)
3. [Протобуферы](#протобуферы)
4. [Генерация кода](#генерация-кода)
5. [Примеры использования](#примеры-использования)

---

## Введение

Модуль 2 (Chat Frontend) взаимодействует с Модулем 1 (Core Engine) через gRPC протокол. В этом документе описаны все gRPC контракты, необходимые для интеграции.

**Версия протокола**: `chameleon.core.v1`  
**Основной сервис**: `OrchestratorService`

---

## gRPC Сервисы

### OrchestratorService

Основной сервис для обработки сообщений в реальном времени.

| Метод | Описание | Timeout |
|-------|----------|---------|
| `ProcessMessage` | Обработка входящего сообщения | 5000ms |
| `HealthCheck` | Проверка состояния сервиса | 1000ms |

#### ProcessMessage

Обрабатывает входящее сообщение и возвращает адаптированную версию.

**Запрос**:
```protobuf
message ProcessMessageRequest {
    string message_id = 1;      // Unique message identifier
    string sender_id = 2;       // Sender user ID
    string recipient_id = 3;    // Recipient user ID
    string room_id = 4;         // Room ID (optional)
    string text = 5;            // Original message text (1-4000 chars)
    optional string style_name = 6;  // Selected style name
    map<string, string> metadata = 7;
}
```

**Ответ**:
```protobuf
message ProcessMessageResponse {
    string adapted_text = 1;              // Adapted message text
    bool was_adapted = 2;                 // Whether message was modified
    float confidence = 3;                 // Adaptation confidence (0.0-1.0)
    string model_used = 4;                // Model identifier used
    int64 processing_time_ms = 5;        // Processing time in milliseconds
    repeated string rules_applied = 6;    // Applied corporate rules
    AdaptationMetadata adaptation_metadata = 7;
}

message AdaptationMetadata {
    bool from_cache = 1;
    bool fallback_used = 2;
    string fallback_reason = 3;
    int32 tokens_prompt = 4;
    int32 tokens_completion = 5;
}
```

**gRPC Status Codes**:
- `OK (0)` - Успех
- `INVALID_ARGUMENT (3)` - Неверный формат сообщения
- `NOT_FOUND (5)` - Пользователь не найден
- `DEADLINE_EXCEEDED (4)` - Таймаут (>5 секунд)
- `INTERNAL (13)` - Внутренняя ошибка

#### HealthCheck

Проверка состояния оркестратора.

**Запрос**: `google.protobuf.Empty`

**Ответ**:
```protobuf
message HealthStatus {
    string status = 1;  // "healthy", "degraded", or "unhealthy"
    string version = 2; // Version string
    map<string, string> checks = 3;  // Service health checks
}
```

---

### RetrieverService

Сервис для получения RAG данных (профили, правила, стили).

| Метод | Описание | Timeout |
|-------|----------|---------|
| `GetProfile` | Получить профиль пользователя | 3600s (TTL) |
| `GetRules` | Получить корпоративные правила | 300s (TTL) |
| `GetStyleExamples` | Получить примеры стилей | 86400s (TTL) |
| `HealthCheck` | Проверка состояния сервиса | 1000ms |

#### GetProfile

Получает профиль пользователя из Qdrant.

**Запрос**:
```protobuf
message GetProfileRequest {
    string user_id = 1;        // User ID
    bool include_history = 2;  // Include embedding vector
    int32 cache_ttl = 3;       // Cache TTL in seconds (3600)
}
```

**Ответ**:
```protobuf
message UserProfile {
    string user_id = 1;
    string full_name = 2;
    string role = 3;
    string department = 4;
    HonorificType honorific_type = 5;
    CommunicationMode communication_mode = 6;
    repeated string known_triggers = 7;
    repeated float adaptive_history_vector = 8;  // 768 floats
    int64 last_updated = 9;
}

enum HonorificType {
    HONORIFIC_UNSPECIFIED = 0;
    FIRST_NAME = 1;
    FIRST_LAST = 2;
    PATRONYMIC = 3;
    TITLE_LAST = 4;
}

enum CommunicationMode {
    MODE_UNSPECIFIED = 0;
    FORMAL = 1;
    INFORMAL = 2;
    TECHNICAL = 3;
    DIPLOMATIC = 4;
}
```

#### GetRules

Получает корпоративные правила по ролям отправителя и получателя.

**Запрос**:
```protobuf
message GetRulesRequest {
    string sender_role = 1;
    string recipient_role = 2;
    string message_text = 3;
    int32 limit = 4;        // Default 5, max 20
    int32 cache_ttl = 5;    // Cache TTL in seconds (300)
}
```

**Ответ**:
```protobuf
message GetRulesResponse {
    repeated CorporateRule rules = 1;
}

message CorporateRule {
    string rule_id = 1;
    string category = 2;
    int32 priority = 3;
    string transformation_prompt = 4;
    string example_original = 5;
    string example_adapted = 6;
    float relevance_score = 7;
}
```

#### GetStyleExamples

Получает примеры литературных стилей.

**Запрос**:
```protobuf
message GetStyleExamplesRequest {
    string style_name = 1;
    int32 sample_count = 2;  // Default 3, max 10
    int32 cache_ttl = 3;     // Cache TTL in seconds (86400)
}
```

**Ответ**:
```protobuf
message GetStyleExamplesResponse {
    repeated StyleExample examples = 1;
}

message StyleExample {
    string style_name = 1;
    string author = 2;
    string sample_text = 3;
    map<string, string> metadata = 4;
}
```

---

## Протобуферы

Все протобуферы находятся в директории `protos/`:

| Файл | Описание |
|------|----------|
| `common.proto` | Общие сообщения (HealthStatus) |
| `orchestrator.proto` | OrchestratorService |
| `retriever.proto` | RetrieverService |
| `llm_gateway.proto` | LLMGatewayService |

---

## Генерация кода

### Установка зависимостей

```bash
# Установить зависимости через poetry
poetry install

# Установить gRPC инструменты
poetry add grpcio grpcio-tools
```

### Генерация Python stubs

```bash
# Сгенерировать все stubs
bash scripts/generate_proto.sh

# Или вручную
python -m grpc_tools.protoc -Iprotos --python_out=src --grpc_python_out=src protos/common.proto protos/orchestrator.proto protos/retriever.proto protos/llm_gateway.proto

# Исправить импорты
bash scripts/fix_stub_imports.sh
```

### Генерация JavaScript stubs (для frontend)

```bash
# Установить protoc-gen-js
npm install -g protoc-gen-js

# Генерировать
protoc --js_out=import_style=commonjs,binary:src/frontend/grpc protos/common.proto protos/orchestrator.proto protos/retriever.proto
```

---

## Примеры использования

### Python - Orchestrator Client

```python
import grpc
import chameleon.core.v1.orchestrator_pb2 as orchestrator_pb2
import chameleon.core.v1.orchestrator_pb2_grpc as orchestrator_pb2_grpc

# Подключение к оркестратору
channel = grpc.insecure_channel('localhost:8001')
stub = orchestrator_pb2_grpc.OrchestratorServiceStub(channel)

# Отправка сообщения
request = orchestrator_pb2.ProcessMessageRequest(
    message_id="msg_001",
    sender_id="user_alex",
    recipient_id="user_petr",
    room_id="room_engineering",
    text="Petr, привет! Как дела?",
    style_name="chekhov"
)

try:
    response = stub.ProcessMessage(request, timeout=5.0)
    print(f"Adapted: {response.adapted_text}")
    print(f"Was adapted: {response.was_adapted}")
    print(f"Model used: {response.model_used}")
except grpc.RpcError as e:
    print(f"Error: {e.code()} - {e.details()}")
```

### Python - Retriever Client

```python
import grpc
import chameleon.core.v1.retriever_pb2 as retriever_pb2
import chameleon.core.v1.retriever_pb2_grpc as retriever_pb2_grpc

channel = grpc.insecure_channel('localhost:8002')
stub = retriever_pb2_grpc.RetrieverServiceStub(channel)

# Получить профиль пользователя
profile_request = retriever_pb2.GetProfileRequest(
    user_id="user_petr",
    include_history=False,
    cache_ttl=3600
)

profile = stub.GetProfile(profile_request, timeout=5.0)
print(f"User: {profile.full_name}")
print(f"Role: {profile.role}")
```

### Node.js - Orchestrator Client (пример)

```javascript
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const packageDefinition = protoLoader.loadSync('protos/orchestrator.proto', {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});

const orchestrator = grpc.loadPackageDefinition(packageDefinition).chameleon.core.v1;

const client = new orchestrator.OrchestratorService(
    'localhost:8001',
    grpc.credentials.createInsecure()
);

// Отправка сообщения
const request = {
    messageId: 'msg_001',
    senderId: 'user_alex',
    recipientId: 'user_petr',
    roomId: 'room_engineering',
    text: 'Petr, привет! Как дела?',
    styleName: 'chekhov'
};

client.processMessage(request, { timeout: 5000 }, (err, response) => {
    if (err) {
        console.error('Error:', err);
    } else {
        console.log('Adapted:', response.adaptedText);
        console.log('Was adapted:', response.wasAdapted);
    }
});
```

---

## Ошибки и обработка исключений

### Типичные ошибки

| Код | Описание | Решение |
|-----|----------|---------|
| `UNAVAILABLE` | Сервис недоступен | Проверить доступность оркестратора |
| `DEADLINE_EXCEEDED` | Таймаут | Увеличить timeout или проверить нагрузку |
| `INVALID_ARGUMENT` | Неверный аргумент | Проверить формат запроса |
| `NOT_FOUND` | Ресурс не найден | Проверить user_id |

### Retry Policy

```yaml
retry_policy:
  max_attempts: 3
  initial_backoff_ms: 100
  max_backoff_ms: 10000
  backoff_multiplier: 2.0
  retryable_statuses:
    - UNAVAILABLE
    - DEADLINE_EXCEEDED
    - INTERNAL
```

---

## Метрики и мониторинг

### Key Metrics

- **QPS**: Запросы в секунду
- **p95 latency**: 95-й перцентиль задержки (<500ms)
- **Error rate**: Процент ошибок (<1%)
- **Cache hit rate**: Процент попаданий в кэш (>30%)

---

## Чеклист интеграции

- [ ] Скопированы протобуферы из модуля 1
- [ ] Установлены зависимости (grpcio, grpcio-tools)
- [ ] Сгенерированы Python stubs
- [ ] Создан gRPC клиент для оркестратора
- [ ] Тесты базового взаимодействия проходят
- [ ] Обработка ошибок реализована
- [ ] Retry policy настроен

---

**Статус**: ✅ Готово к интеграции  
**Дата**: 2026-06-15
