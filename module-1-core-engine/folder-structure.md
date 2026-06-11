# ========== МОДУЛЬ 1 ==========

## Папка module-1-core-engine/

### Файлы:

- README.md
- pyproject.toml - Python проект
- Dockerfile
- docker-compose.module.yml - Только для этого модуля
- .env

### Подпапки:

- **src/orchestrator/** - Оркестратор
  - __init__.py
  - main.py - FastAPI/gRPC сервер
  - handlers.py
  - context_assembler.py
  - cache_manager.py
  - config.py

- **src/retriever/** - Ретривер
  - __init__.py
  - main.py
  - qdrant_client.py
  - embeddings.py
  - chunking.py
  - hybrid_search.py
  - ingestion/
    - file_loader.py
    - api_loader.py

- **src/llm_gateway/** - Шлюз LLM
  - __init__.py
  - main.py
  - router.py
  - providers/
    - base.py
    - ollama_provider.py
    - openai_provider.py
  - cache.py
  - load_balancer.py

- **src/common/** - Общие компоненты
  - schemas.py
  - logging.py
  - metrics.py - Prometheus метрики
  - langfuse_integration.py

- **tests/** - Тесты
  - unit/ - Юнит-тесты
  - integration/ - Интеграционные тесты
  - conftest.py

- **scripts/** - Скрипты модуля
  - download_models.py
  - warmup_cache.py

- **config/** - Конфигурация
  - development.yaml
  - production.yaml
  - models.yaml - Какие модели доступны
