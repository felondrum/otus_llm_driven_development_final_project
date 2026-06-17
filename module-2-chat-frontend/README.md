# README Модуля 2 - Chat Frontend

## Обзор

Модуль 2 - это чат-интерфейс для системы Chameleon Chat. Он реализует WebSocket протокол для обмена сообщениями и HTTP API для администраторов.

### Архитектура

```
module-2-chat-frontend/
├── src/
│   ├── backend/        # Node.js сервер (Express + WebSocket)
│   └── frontend/       # React UI
│       ├── src/
│       │   ├── components/
│       │   ├── hooks/
│       │   ├── services/  # gRPC клиенты
│       │   └── styles/
├── protos/             # gRPC протобуферы (копия из модуля 1)
├── docs/               # Документация
│   └── PROTOCOL.md     # gRPC протокол
└── config/             # Конфигурация
```

## Установка

```bash
cd module-2-chat-frontend

# Установить зависимости
npm install

# Или через poetry для backend
poetry install
```

## Конфигурация

Конфигурация находится в `config/`:

- `config.js` - настройки сервера
- `.env` - переменные окружения

### Переменные окружения

```bash
# Сервер
PORT=8080
WS_PORT=8081

# Оркестратор (модуль 1)
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_GRPC_PORT=8001

# Другие настройки
LOG_LEVEL=INFO
```

## Запуск

### Локально

```bash
# Запуск backend сервера
npm run start:backend

# Запуск frontend
npm run start:frontend

# Запуск в dev режиме
npm run dev
```

### Через Docker

```bash
# Запуск через docker-compose
docker-compose -f docker-compose.module.yml up -d
```

## gRPC протокол

Модуль 2 использует gRPC для взаимодействия с Модулем 1 (Core Engine).

### Генерация gRPC stubs

После изменения протобуферов (из модуля 1) необходимо сгенерировать новые stubs:

#### Python

```bash
# Установить зависимости
poetry add grpcio grpcio-tools

# Сгенерировать stubs
python -m grpc_tools.protoc -Iprotos --python_out=src --grpc_python_out=src protos/common.proto protos/orchestrator.proto protos/retriever.proto protos/llm_gateway.proto

# Или через Makefile (если добавлен)
make generate-grpc
```

#### JavaScript/Node.js

```bash
# Установить прото компилятор
npm install -g protoc

# Генерировать JS stubs
protoc --js_out=import_style=commonjs,binary:src/frontend/grpc protos/common.proto protos/orchestrator.proto protos/retriever.proto
```

### Использование gRPC клиента

```python
# src/backend/grpc_client/orchestrator_client.py
import grpc
import chameleon.core.v1.orchestrator_pb2 as orchestrator_pb2
import chameleon.core.v1.orchestrator_pb2_grpc as orchestrator_pb2_grpc

class OrchestratorClient:
    def __init__(self, host='localhost', port=8001):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = orchestrator_pb2_grpc.OrchestratorServiceStub(self.channel)
    
    async def process_message(self, request):
        return await self.stub.ProcessMessage(request, timeout=5.0)
```

## API Endpoints

### WebSocket (Real-time)

**Endpoint**: `ws://localhost:8081/ws`

**Сообщения**:
- `auth` - аутентификация
- `message` - отправка сообщения
- `message_ack` - подтверждение получения
- `message` - получение сообщения

### HTTP REST (Admin)

**Base URL**: `http://localhost:8080/api/v1`

- `GET /users/{user_id}` - получить пользователя
- `GET /rooms/{room_id}/messages` - история чата
- `POST /messages` - отправить сообщение

## Структура проекта

```
module-2-chat-frontend/
├── src/
│   ├── backend/
│   │   ├── server.js          # Express сервер
│   │   ├── websocket/         # WebSocket обработчики
│   │   ├── api/               # REST endpoints
│   │   ├── grpc_client/       # gRPC клиенты
│   │   ├── config.js          # Конфигурация
│   │   └── package.json
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx        # Главный компонент
│       │   ├── components/    # React компоненты
│       │   ├── hooks/         # React хуки
│       │   ├── services/      # Служебные модули
│       │   └── styles/        # CSS стили
│       ├── index.html
│       └── package.json
├── protos/                    # gRPC протобуферы
│   ├── common.proto
│   ├── orchestrator.proto
│   ├── retriever.proto
│   └── llm_gateway.proto
└── docs/
    └── PROTOCOL.md           # Документация gRPC
```

## Тестирование

```bash
# Юнит-тесты
npm run test

# Интеграционные тесты
npm run test:integration

# Покрытие
npm run test:coverage
```

## Разработка

### Добавление новогоgRPC метода

1. Обновить `protos/orchestrator.proto` (из модуля 1)
2. Сгенерировать stubs: `make generate-grpc`
3. Создать клиент в `src/backend/grpc_client/`
4. Использовать клиент в `src/backend/api/`

### Добавление нового WebSocket сообщения

1. Обновить схему в `src/backend/websocket/schema.js`
2. Добавить обработчик в `src/backend/websocket/handlers.js`
3. Добавить TypeScript тип в `src/frontend/src/types/websocket.ts`

## Метрики

Метрики экспортируются в формате Prometheus на порту 9090.

## Проверка интеграции с модулем 1

```bash
# Запустить модуль 1
cd ../module-1-core-engine
make run

# Запустить модуль 2
cd ../module-2-chat-frontend
make run

# Проверить подключение
curl http://localhost:8081/api/v1/health
```

## Troubleshooting

### Проблема: gRPC connection refused

**Решение**: Проверить доступность оркестратора на порту 8001

```bash
# Проверить порт
lsof -i :8001

# Или через netstat
netstat -tuln | grep 8001
```

### Проблема: WebSocket handshake error

**Решение**: Проверить CORS на backend сервере

```bash
# В config.js убедиться, что CORS разрешен
cors: {
    origin: ['http://localhost:3000', 'http://localhost:8080']
}
```

## Лицензия

MIT
