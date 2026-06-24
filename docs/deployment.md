# Deployment Guide — Chameleon Chat

## Запуск системы

### Требования

- Docker (версия 20+)
- Docker Compose (версия 2+)
- Python 3.11+ (для локальной разработки)
- Poetry (для управления зависимостями модулей)

> 💡 **Примечание:** Для корректной работы убедитесь, что все три модуля (core-engine, chat-frontend, admin-data) запущены в единой сети Docker. Сеть `chameleon-network` создаётся автоматически при первом запуске модуля 1 (core-engine).

### Шаг 1: Настройка .env файла

Скопируйте `.env.example` в `.env` и обновите ключи:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите свои ключи:

- `LANGFUSE_PUBLIC_KEY` - ваш публичный ключ Langfuse
- `LANGFUSE_SECRET_KEY` - ваш секретный ключ Langfuse
- `YA_LLM_KEY` - API ключ Yandex Cloud
- `YA_HOST_KEY` - ID папки в Yandex Cloud

> 💡 Ключи Langfuse можно получить на http://localhost:3000 после первого запуска

### Шаг 2: Запуск

Запуск производится отдельно для каждого модуля. Все модули используют общую сеть Docker `chameleon-network`, которая создаётся автоматически при первом запуске модуля 1.

#### Модуль 1: Core Engine

```bash
cd module-1-core-engine

# Создайте .env файл
cp .env.example .env

# Запустите инфраструктуру и сервисы
docker-compose -f docker-compose.module.yml up -d

# Остановить
docker-compose -f docker-compose.module.yml down

# Логи
docker-compose -f docker-compose.module.yml logs -f
```

#### Модуль 2: Chat Frontend

```bash
cd module-2-chat-frontend

# Запустите чат-интерфейс
docker-compose -f docker-compose.module.yml up -d

# Остановить
docker-compose -f docker-compose.module.yml down
```

#### Модуль 3: Admin Data

```bash
cd module-3-admin-data

# Запустите админ-интерфейс
docker-compose -f docker-compose.module.yml up -d

# Остановить
docker-compose -f docker-compose.module.yml down
```

> 💡 **Порядок запуска:** Сначала запустите модуль 1 (core-engine), дождитесь инициализации всех сервисов, затем запустите модуль 2 и модуль 3.

### Шаг 3: Проверка

После запуска всех модулей проверьте доступность сервисов:

```bash
# Проверка модуля 1 (core-engine)
cd module-1-core-engine
docker ps

# Проверка модуля 2 (chat-frontend)
cd module-2-chat-frontend
docker ps

# Проверка модуля 3 (admin-data)
cd module-3-admin-data
docker ps
```

### Доступные сервисы

| Сервис | URL | Порт | Описание |
|--------|-----|------|----------|
| Langfuse UI | http://localhost:3000 | 3000 | Веб-интерфейс трейсинга |
| Orchestrator | localhost:8001 | 8001 | HTTP оркестратор |
| Retriever | localhost:8002 | 8002 | HTTP RAG поиск |
| LLM Gateway | localhost:8003 | 8003 | HTTP LLM прокси |
| ClickHouse | http://localhost:8123 | 8123 | База метрик |
| MinIO Console | http://localhost:9011 | 9011 | Хранилище файлов |
| Chat Frontend | http://localhost:8080 | 8080 | React чат-интерфейс |
| Admin API | http://localhost:8200 | 8200 | Admin REST API |
| Admin UI | http://localhost:5174 | 5174 | Admin React UI |

### Остановка и очистка

```bash
# Остановить сервисы каждого модуля отдельно
cd module-1-core-engine
docker-compose -f docker-compose.module.yml down

cd ../module-2-chat-frontend
docker-compose -f docker-compose.module.yml down

cd ../module-3-admin-data
docker-compose -f docker-compose.module.yml down

# Остановить и удалить volume (данные будут потеряны!)
docker-compose -f docker-compose.module.yml down -v
```

---

## Архитектура развертывания

### Локальный деплой (Docker Compose)

**Профили запуска:**
- `dev` — горячая перезагрузка, volume mounts, debug ports
- `test` — фиксированные версии, без GPU, ограниченные ресурсы
- `prod-demo` — production-like для демо (replicas, healthchecks)

**Ресурсы:**
| Сервис | CPU | RAM | GPU | Storage |
|--------|-----|-----|-----|---------|
| Ollama | 4 cores | 16 GB | 1x NVIDIA (16GB) | 20 GB |
| Qdrant | 2 cores | 4 GB | - | 10 GB |
| Orchestrator | 2 cores | 2 GB | - | - |
| LLM Gateway | 1 core | 1 GB | - | - |
| Chat Frontend | 1 core | 512 MB | - | - |
| PostgreSQL | 1 core | 1 GB | - | 10 GB |
| Total | ~12 cores | ~25 GB | ~16 GB | ~50 GB |

### Масштабирование (перспектива)

Кластеризация для production:
- **Frontend**: 2+ реплики
- **Orchestrator**: 2+ реплики
- **LLM Gateway**: 2+ реплики
- **Qdrant**: кластеризация
- **Redis**: кластеризация

### Сетевые порты и протоколы

| От (сервис) | До (сервис) | Порт | Протокол | Назначение |
|-------------|-------------|------|----------|------------|
| Browser | API Gateway | 8000 | HTTP | REST API |
| Browser | WebSocket | 8081 | WS | Real-time messages |
| API Gateway | Orchestrator | 8001 | HTTP | Process message |
| Orchestrator | Retriever | 8002 | HTTP | RAG queries |
| Orchestrator | LLM Gateway | 8003 | HTTP | Text generation |
| Orchestrator | Redis | 6379 | RESP | Cache & Queue |
| Retriever | Qdrant | 6334 | HTTP | Vector search |
| Retriever | Ollama | 11434 | HTTP | Embeddings |
| LLM Gateway | Ollama | 11434 | HTTP | LLM inference |
| Black Box | PostgreSQL | 5432 | PGWire | Write analytics |
| Dashboard | PostgreSQL | 5432 | PGWire | Read metrics |
