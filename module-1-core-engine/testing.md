# Testing Guide — Module 1: Core Engine

## Тестирование

### Юнит-тесты

```bash
cd module-1-core-engine

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

### Что тестируется в e2e

1. **Полный поток адаптации**: отправитель → оркестратор → ретривер → LLM → ответ
2. **Формальное обращение**: "Иван, ты должен" → "Иван Петрович, вы должны"
3. **Обработка обвинений**: "ты сломал" → "система не работает корректно"
4. **RAG поиск**: поиск профилей, правил и стилей в Qdrant
5. **Кэширование**: повторные запросы возвращаются из кэша
6. **Fallback**: обработка отсутствующих профилей и ошибок

### Покрытие тестами

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

### Локальный запуск для разработки

```bash
cd module-1-core-engine

# Запуск через poetry
poetry run python -m src.orchestrator.main
poetry run python -m src.retriever.main
poetry run python -m src.llm_gateway.main
```
