# Testing Guide — Chameleon Chat

## Тестирование

### Модуль 1: Core Engine

#### Юнит-тесты

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

#### Запуск e2e тестов

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

#### Что тестируется в e2e

1. **Полный поток адаптации**: отправитель → оркестратор → ретривер → LLM → ответ
2. **Формальное обращение**: "Иван, ты должен" → "Иван Петрович, вы должны"
3. **Обработка обвинений**: "ты сломал" → "система не работает корректно"
4. **RAG поиск**: поиск профилей, правил и стилей в Qdrant
5. **Кэширование**: повторные запросы возвращаются из кэша
6. **Fallback**: обработка отсутствующих профилей и ошибок

### Модуль 2: Chat Frontend

#### Интеграционные тесты

```bash
cd module-2-chat-frontend

# Установить зависимости
pip install -r requirements.txt

# Запустить тесты
pytest tests/integration/ -v
```

### Модуль 3: Admin Data

#### Интеграционные тесты с PostgreSQL

```bash
cd module-3-admin-data

# Запустить PostgreSQL через Docker Compose
docker-compose -f docker-compose.module.yml up -d postgres

# Подождать 10-15 секунд пока БД запустится
sleep 15

# Установить зависимости
poetry install

# Запустить тесты
poetry run pytest tests/integration/ -v

# Или использовать скрипт
./scripts/test.sh

# Остановить PostgreSQL
docker-compose -f docker-compose.module.yml down
```

### Покрытие тестами

#### Модуль 1: Core Engine
- **Всего тестов**: 203
- **Прошли успешно**: 183 (90.1%)
- **Пропущено**: 2 (0.99%)
- **Ошибки**: 0 (0%)

**Распределение по категориям:**
| Категория | Всего | Статус |
|-----------|-------|--------|
| E2E тесты | 32 | ✅ 100% passed |
| Unit тесты | 137 | ✅ 100% passed |
| Integration тесты | 14 | ✅ 14/14 passed |

#### Модуль 3: Admin Data
- ✅ Profiles CRUD (create, read, update, delete)
- ✅ Rules CRUD (create, read, update, delete)
- ✅ Styles CRUD (create, read, update, delete)
- ✅ Documents CRUD (create, read, delete)
- ✅ Database pool management
- ✅ Sync functions (mocked)

### Локальный запуск для разработки

#### Модуль 1: Core Engine

```bash
cd module-1-core-engine

# Запуск через poetry
poetry run python -m src.orchestrator.main
poetry run python -m src.retriever.main
poetry run python -m src.llm_gateway.main
```

#### Модуль 2: Chat Frontend

```bash
cd module-2-chat-frontend

# Запуск backend
cd src/backend
python -m main

# Запуск frontend (в другом терминале)
cd src/frontend
npm install
npm run dev
```

#### Модуль 3: Admin Data

```bash
cd module-3-admin-data

# Запуск API
poetry run python -m admin_api.main

# Запуск UI (в другом терминале)
cd src/frontend_admin
npm install
npm run dev
```

### Решение проблем

#### Проблема: WebSocket connection failed

**Решение**: Убедитесь, что backend запущен и слушает на правильном порту

```bash
# Проверить порты
lsof -i :8080
```

#### Проблема: Core Engine недоступен

**Решение**: Убедитесь, что Core Engine запущен

```bash
# Проверить порт Core Engine
curl http://localhost:8001/health

# Или запустить core-engine из module-1
cd ../module-1-core-engine
docker-compose up -d
```
