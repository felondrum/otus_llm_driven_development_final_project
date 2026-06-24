# Deployment Guide — Module 1: Core Engine

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

### Шаг 3: Проверка

После запуска всех модулей проверьте доступность сервисов:

```bash
# Проверка модуля 1 (core-engine)
cd module-1-core-engine
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

### Остановка и очистка

```bash
# Остановить сервисы модуля
cd module-1-core-engine
docker-compose -f docker-compose.module.yml down

# Остановить и удалить volume (данные будут потеряны!)
docker-compose -f docker-compose.module.yml down -v
```

---

## Ресурсы

| Сервис | CPU | RAM | GPU | Storage |
|--------|-----|-----|-----|---------|
| Ollama | 4 cores | 16 GB | 1x NVIDIA (16GB) | 20 GB |
| Qdrant | 2 cores | 4 GB | - | 10 GB |
| Orchestrator | 2 cores | 2 GB | - | - |
| LLM Gateway | 1 core | 1 GB | - | - |
| Total | ~8 cores | ~23 GB | ~16 GB | ~30 GB |

---

## Сетевые порты и протоколы

| От (сервис) | До (сервис) | Порт | Протокол | Назначение |
|-------------|-------------|------|----------|------------|
| Browser | Orchestrator | 8001 | HTTP | Process message |
| Orchestrator | Retriever | 8002 | HTTP | RAG queries |
| Orchestrator | LLM Gateway | 8003 | HTTP | Text generation |
| Orchestrator | Redis | 6379 | RESP | Cache & Queue |
| Retriever | Qdrant | 6334 | HTTP | Vector search |
| Retriever | Ollama | 11434 | HTTP | Embeddings |
| LLM Gateway | Ollama | 11434 | HTTP | LLM inference |
