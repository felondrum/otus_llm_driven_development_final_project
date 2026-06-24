# Testing Guide — Module 3: Admin & Data Management

## Тестирование

### Интеграционные тесты с PostgreSQL

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

- ✅ Profiles CRUD (create, read, update, delete)
- ✅ Rules CRUD (create, read, update, delete)
- ✅ Styles CRUD (create, read, update, delete)
- ✅ Documents CRUD (create, read, delete)
- ✅ Database pool management
- ✅ Sync functions (mocked)

### Локальный запуск для разработки

```bash
cd module-3-admin-data

# Установка зависимостей
poetry install

# Запуск API
poetry run python -m admin_api.main
```

### Верификация endpoints

```bash
# Проверка REST API
curl http://localhost:8200/api/v1/admin/profiles

# Проверка состояния
curl http://localhost:8200/api/v1/admin/system/status
```
