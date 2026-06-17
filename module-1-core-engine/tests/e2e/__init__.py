"""E2E тесты для Core Engine модуля.

Эти тесты проверяют полный поток обработки сообщений с реальными сервисами:
- Orchestrator через gRPC
- Retriever через gRPC  
- LLM Gateway через HTTP
- Qdrant для RAG поиска
- Ollama для LLM генерации
- Redis для кэширования

Запуск:
    poetry run pytest tests/e2e/ -v

Или через make:
    make e2e-setup  # Подготовить среду
    make test-e2e   # Запустить тесты
"""
