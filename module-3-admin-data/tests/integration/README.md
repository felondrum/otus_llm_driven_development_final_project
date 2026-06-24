# Тесты Module 3: Admin & Data Management

## Структура тестов

```
tests/
├── api_tests/          # API endpoint tests
│   └── test_admin_endpoints.py
├── integration/        # Integration tests with PostgreSQL
│   ├── test_crud_operations.py
│   └── README.md
└── unit/              # Unit tests
```

## Запуск тестов

### Предварительные требования

- Python 3.11+
- Poetry
- Docker и Docker Compose (для запуска PostgreSQL)

### Локальный запуск

1. Запустите Docker Compose для поднятия PostgreSQL:

```bash
cd module-3-admin-data
docker-compose -f docker-compose.module.yml up -d
```

2. Подождите 10-15 секунд пока PostgreSQL запустится.

3. Запустите тесты:

```bash
# Установите зависимости
poetry install

# Запустите тесты
poetry run pytest tests/integration/ -v

# Или используйте скрипт
./scripts/test.sh
```

4. Остановите Docker Compose:

```bash
docker-compose -f docker-compose.module.yml down
```

### CI/CD запуск

В CI/CD pipeline используйте следующие команды:

```bash
# Запустить все тесты
poetry run pytest tests/ -v

# Запустить только интеграционные тесты
poetry run pytest tests/integration/ -v

# Запустить только API тесты
poetry run pytest tests/api_tests/ -v

# С покрытием кода
poetry run pytest tests/ --cov=src/admin_api --cov-report=html -v
```

## Типы тестов

### Integration Tests (tests/integration/)

Интеграционные тесты работают с реальной базой данных PostgreSQL.

**Покрытие:**
- profiles CRUD (create, read, update, delete)
- rules CRUD (create, read, update, delete)
- styles CRUD (create, read, update, delete)
- documents CRUD (create, read, delete)
- database pool management
- sync functions

**Тесты:**
- `test_profiles_crud` - полный цикл CRUD для профилей
- `test_rules_crud` - полный цикл CRUD для правил
- `test_styles_crud` - полный цикл CRUD для стилей
- `test_documents_crud` - полный цикл CRUD для документов
- `test_database_pool_management` - управление соединениями
- `test_sync_functions` - функции синхронизации

### API Tests (tests/api_tests/)

Тесты API endpoints с использованием TestClient.

### Unit Tests (tests/unit/)

Модульные тесты с моками и патчами.

## Конфигурация

Переменные окружения для тестов:

- `TEST_DATABASE_URL` - URL для подключения к PostgreSQL (по умолчанию: `postgresql://chameleon:chameleon123@localhost:5433/chameleon_admin`)

## Написание новых тестов

### Правила написания тестов

1. Используйте `@pytest.mark.asyncio` для асинхронных тестов
2. Используйте `pg_pool` fixture для доступа к базе данных
3. Используйте `test_` префикс для имен файлов и функций
4. Добавьте cleanup логику в fixture `setup_database`
5. Используйте уникальные ID для тестовых данных (uuid)

### Пример нового теста

```python
import pytest
import uuid
import asyncio

@pytest.mark.asyncio
async def test_your_feature_crud(pg_pool):
    """Test CRUD for your feature"""
    from database import your_crud_functions
    
    test_id = f"test_{uuid.uuid4().hex[:8]}"
    
    # CREATE
    created = await your_crud_functions.create({...})
    assert created["id"] == test_id
    
    # READ
    item = await your_crud_functions.get(test_id)
    assert item is not None
    
    # UPDATE
    updated = await your_crud_functions.update(test_id, {...})
    assert updated["field"] == "new_value"
    
    # DELETE
    deleted = await your_crud_functions.delete(test_id)
    assert deleted is True
```

## Устранение проблем

### Проблема: Connection refused

**Решение:** Убедитесь что PostgreSQL запущен и доступен на порту 5433.

```bash
docker-compose -f docker-compose.module.yml ps
docker-compose -f docker-compose.module.yml logs postgres
```

### Проблема: Test data not cleaned up

**Решение:** Вручную очистите тестовые данные:

```sql
DELETE FROM profiles WHERE user_id LIKE 'test_%';
DELETE FROM rules WHERE rule_id LIKE 'test_%';
DELETE FROM styles WHERE style_id LIKE 'test_%';
DELETE FROM documents WHERE document_id LIKE 'test_%';
```

### Проблема: Timeout на соединение

**Решение:** Увеличьте таймаут в Docker Compose или проверьте сетевые настройки.

## Лицензия

Copyright (c) 2024 Chameleon Team. All rights reserved.
