# Module 1: Core Engine

## Бизнес-смысл

Модуль Core Engine - это сердце системы Chameleon Chat. Он отвечает за адаптацию сообщений с использованием LLM, ретривер RAG данных и маршрутизацию запросов к различным моделям.

### Основные компоненты

- **Orchestrator** - координирует процесс адаптации, вызывает Retriever и LLM Gateway
- **Retriever** - предоставляет RAG данные (профили, правила, стили, корпоративная культура) из Qdrant
- **LLM Gateway** - маршрутизирует запросы к различным LLM провайдерам (Ollama, Yandex LLM)
- **Langfuse** - трейсинг и мониторинг LLM приложений (опционально)

### RAG для корпоративной культуры

Система поддерживает загрузку и поиск векторных данных корпоративной культуры:

- **Документация**: `demo_data/corporate_culture.md` - Markdown документ с ценностями, принципами и примерами
- **CLI утилита**: `scripts/ingest_corporate_culture.py` - загрузка документа в Qdrant
- **Поиск**: `SearchCulture` HTTP метод и `get_culture_chunks()` - векторный поиск релевантных фрагментов
- **Промпт**: Корпоративная культура автоматически добавляется в промпт для адаптации сообщений

### Работа с профилями пользователей

Система адаптирует сообщения с учетом профиля получателя. Профили загружаются из `demo_data/profiles.json` и хранятся в Qdrant.

**Важно**: Используйте `user_id` (например, `alex_i`), а не имя пользователя.

---

## Технологии

- Python 3.11+
- FastAPI (HTTP API)
- HTTP (внутреннее взаимодействие)
- Qdrant (векторная БД)
- Redis (кэш)
- Ollama (локальные LLM: qwen2.5:1.5b)
- Yandex LLM API (Fallback провайдер)

---

## Архитектура

### Компоненты

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Core Engine (Module 1)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │ Orchestrator    │  │ Retriever       │  │ LLM Gateway      │   │
│  │ (HTTP 8001)     │  │ (HTTP 8002)     │  │ (HTTP 8003)      │   │
│  │ - координирует   │  │ - RAG поиск     │  │ - кэширование    │   │
│  │ - обрабатывает  │  │ - профили       │  │ - fallback chain │   │
│  │   сообщения     │  │ - правила       │  │ - генерация      │   │
│  │                 │  │ - стили         │  │                  │   │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘   │
│  ┌─────────────────┐  ┌─────────────────┐                         │
│  │ Redis (кэш)     │  │ Qdrant (векторы)│                         │
│  └─────────────────┘  └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Поток обработки

```
User Message → Chat UI → Orchestrator → Retriever → LLM Gateway → Response
                                    ↓              ↓              ↓
                               Redis         Qdrant        Ollama/API
```

---

## Документация

| Тип документации | Файл | Описание |
|------------------|------|----------|
| **Deployment** | [deployment.md](deployment.md) | Инструкции по развертыванию |
| **Testing** | [testing.md](testing.md) | Руководство по тестированию |

---

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
├── config/             # Конфигурация
├── demo_data/          # Демо данные для RAG
│   ├── profiles.json   # Профили пользователей
│   ├── rules.json      # Корпоративные правила
│   ├── styles.json     # Литературные стили
│   └── corporate_culture.md
└── scripts/            # Скрипты
    └── ingest_corporate_culture.py
```

---

## API Endpoints

### LLM Gateway (HTTP)

- `GET /health` - проверка состояния
- `POST /generate` - генерация текста
- `GET /models` - список доступных моделей

### Retriever (HTTP)

- `GET /profile/{user_id}` - получить профиль пользователя
- `GET /rules` - получить корпоративные правила
- `GET /styles` - получить примеры стилей
- `POST /rules/search` - поиск правил
- `POST /culture/search` - поиск в корпоративной культуре (RAG)

### Orchestrator (HTTP)

- `POST /process-message` - обработать сообщение
- `GET /health` - проверка состояния

---

## Быстрый старт

```bash
cd module-1-core-engine

# Установка зависимостей
poetry install

# Локальный запуск
poetry run python -m src.orchestrator.main
poetry run python -m src.retriever.main
poetry run python -m src.llm_gateway.main

# Docker запуск
docker-compose -f docker-compose.module.yml up -d
```
