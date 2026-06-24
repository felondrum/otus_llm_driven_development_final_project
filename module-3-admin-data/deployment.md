# Deployment Guide — Module 3: Admin & Data Management

## Запуск системы

### Требования

- Docker (версия 20+)
- Docker Compose (версия 2+)
- Python 3.11+ (для локальной разработки)
- Poetry (для управления зависимостями модулей)

> 💡 **Примечание:** Для корректной работы модуль 3 должен быть запущен в той же Docker сети (chameleon-network), что и модули 1 и 2.

### Шаг 1: Запуск

```bash
cd module-3-admin-data

# Собрать и запустить
docker-compose -f docker-compose.module.yml up -d

# Посмотреть логи
docker-compose -f docker-compose.module.yml logs -f

# Остановить
docker-compose -f docker-compose.module.yml down
```

### Шаг 2: Проверка

После запуска проверьте доступность сервиса:

```bash
# Проверка модуля 3 (admin-data)
cd module-3-admin-data
docker ps
```

### Доступные сервисы

| Сервис | URL | Порт | Описание |
|--------|-----|------|----------|
| Admin API | http://localhost:8200 | 8200 | Admin REST API |
| Admin UI | http://localhost:5174 | 5174 | Admin React UI |

### Остановка и очистка

```bash
# Остановить сервисы модуля
cd module-3-admin-data
docker-compose -f docker-compose.module.yml down

# Остановить и удалить volume (данные будут потеряны!)
docker-compose -f docker-compose.module.yml down -v
```

---

## Локальный запуск для разработки

```bash
cd module-3-admin-data

# Установка зависимостей
poetry install

# Запуск API
poetry run python -m admin_api.main

# Запуск UI (в другом терминале)
cd src/frontend_admin
npm install
npm run dev
```
