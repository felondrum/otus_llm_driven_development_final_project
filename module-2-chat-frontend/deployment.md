# Deployment Guide — Module 2: Chat Frontend

## Запуск системы

### Требования

- Docker (версия 20+)
- Docker Compose (версия 2+)
- Python 3.11+ (для локальной разработки)
- Poetry (для управления зависимостями модулей)

> 💡 **Примечание:** Для корректной работы модуль 2 должен быть запущен в той же Docker сети (chameleon-network), что и модуль 1 (core-engine).

### Шаг 1: Запуск

```bash
cd module-2-chat-frontend

# Запустите чат-интерфейс
docker-compose -f docker-compose.module.yml up -d

# Остановить
docker-compose -f docker-compose.module.yml down

# Логи
docker-compose -f docker-compose.module.yml logs -f
```

### Шаг 2: Проверка

После запуска проверьте доступность сервиса:

```bash
# Проверка модуля 2 (chat-frontend)
cd module-2-chat-frontend
docker ps
```

### Доступные сервисы

| Сервис | URL | Порт | Описание |
|--------|-----|------|----------|
| Chat Frontend | http://localhost:8080 | 8080 | React чат-интерфейс |

### Остановка и очистка

```bash
# Остановить сервисы модуля
cd module-2-chat-frontend
docker-compose -f docker-compose.module.yml down

# Остановить и удалить volume (данные будут потеряны!)
docker-compose -f docker-compose.module.yml down -v
```

---

## Локальный запуск для разработки

```bash
cd module-2-chat-frontend

# Установить зависимости Python
pip install -r requirements.txt

# Запустить backend
cd src/backend
python -m main

# Запустить frontend (в другом терминале)
cd src/frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:5173`
