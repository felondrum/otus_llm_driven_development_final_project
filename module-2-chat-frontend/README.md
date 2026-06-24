# README Модуля 2 - Chat Frontend

## Обзор

Модуль 2 - это веб-интерфейс чата для системы Chameleon Chat. Он реализует WebSocket протокол для обмена сообщениями в реальном времени и REST API для управления.

**Особенности:**
- Один контейнер чата (с возможностью масштабирования через Redis Pub/Sub)
- Профили пользователей хранятся в SQLite БД
- Управление профилями через REST API
- Синхронизация с Core Engine через gRPC
- Автоматическое случайное изменение фона
- Минималистичный UI с базовыми функциями
- Поддержка литературных стилей
- Межконтейнерная коммуникация через Redis Pub/Sub

## Технологический стек

- **Backend**: Python 3.11 + FastAPI + WebSocket
- **Frontend**: React 18 + Vite
- **Коммуникация**: gRPC (с Core Engine), Redis Pub/Sub
- **База данных**: SQLite для профилей пользователей
- **Контейнеризация**: Docker + Docker Compose

## Структура проекта

```
module-2-chat-frontend/
├── docker-compose.yml          # Один контейнер чата (Redis для масштабирования)
├── Dockerfile                  # Общий образ
├── requirements.txt            # Python зависимости
├── package.json                # Node.js зависимости
├── .env.example                # Пример переменных окружения
├── src/
│   ├── backend/                # Python FastAPI backend
│   │   ├── main.py            # FastAPI server
│   │   ├── websocket.py       # WebSocket обработчики
│   │   ├── api.py             # REST endpoints
│   │   ├── database.py        # SQLite database for profiles
│   │   ├── config.py          # Конфигурация
│   │   └── __init__.py
│   └── frontend/               # React frontend
│       ├── src/
│       │   ├── App.jsx        # Главный компонент
│       │   ├── components/    # React компоненты
│       │   │   ├── Login.jsx
│       │   │   └── ChatRoom.jsx
│       │   ├── services/      # API сервисы
│       │   │   ├── api.js
│       │   │   └── websocket.js
│       │   ├── styles/        # CSS стили
│       │   └── hooks/         # React хуки
│       ├── public/            # Статические файлы
│       │   └── index.html
│       └── vite.config.js     # Конфигурация Vite
└── protos/                    # gRPC протобуферы (копия из module-1)
```

## Установка и запуск

### Локальный запуск (разработка)

#### 1. Запуск Backend

```bash
cd module-2-chat-frontend

# Установить зависимости Python
pip install -r requirements.txt

# Запустить backend
cd src/backend
python -m main
```

#### 2. Запуск Frontend

```bash
cd module-2-chat-frontend/src/frontend

# Установить зависимости
npm install

# Запустить dev-сервер
npm run dev
```

Frontend будет доступен на `http://localhost:5173`

### Docker запуск (рекомендуется для демонстрации)

#### 1. Запуск контейнера

```bash
cd module-2-chat-frontend
docker-compose up -d
```

#### 2. Доступ к чату

- **Чат**: `http://localhost:8080`

#### 3. Остановка

```bash
docker-compose down
```

## API Endpoints

### REST API (`/api/v1`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users` | GET | Список тестовых пользователей |
| `/profiles` | GET | Список всех профилей (из БД) |
| `/profiles/{user_id}` | GET | Получить профиль по ID |
| `/profiles` | POST | Создать профиль |
| `/profiles/{user_id}` | PUT | Обновить профиль |
| `/profiles/{user_id}` | DELETE | Удалить профиль |
| `/profiles/sync` | POST | Синхронизировать с Core Engine |
| `/styles` | GET | Список доступных стилей |
| `/health` | GET | Проверка состояния |

### WebSocket API (`/ws`)

| Type | Direction | Description |
|------|-----------|-------------|
| `welcome` | Server → Client | Приветственное сообщение |
| `auth` | Client → Server | Аутентификация |
| `auth_ok` | Server → Client | Подтверждение авторизации |
| `message` | Client → Server | Отправка сообщения |
| `message` | Server → Client | Получение сообщения |
| `recipient_selected` | Server → Client | Выбор получателя |
| `error` | Server → Client | Ошибка |

## Тестовые пользователи

При первом запуске профили загружаются из Core Engine через gRPC. Если Core Engine недоступен, используются тестовые профили по умолчанию.

Доступные пользователи:

- `alex_i` - Иванов Алексей (engineer, informal)
- `petr_s` - Смирнов Петр (team_lead, formal)
- `anna_k` - Ковалева Анна (director, formal)
- `maria_s` - Смирнова Мария (hr_manager, formal)
- `dmitry_k` - Кузнецов Дмитрий (senior_engineer, technical)
- `elena_v` - Воронова Елена (team_lead, collaborative)
- `sergey_m` - Михайлов Сергей (intern, informal)
- `olga_a` - Алексеева Ольга (director, formal)

## Управление профилями

### Через REST API (Module 2)

```bash
# Список всех профилей
curl http://localhost:8080/api/v1/profiles

# Создать профиль
curl -X POST http://localhost:8080/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{"user_id": "new_user", "full_name": "Новый Пользователь", "role": "employee"}'

# Обновить профиль
curl -X PUT http://localhost:8080/api/v1/profiles/new_user \
  -H "Content-Type: application/json" \
  -d '{"user_id": "new_user", "full_name": "Обновленный Пользователь", "role": "manager"}'

# Удалить профиль
curl -X DELETE http://localhost:8080/api/v1/profiles/new_user

# Синхронизировать с Core Engine
curl -X POST http://localhost:8080/api/v1/profiles/sync
```

### Через Admin API (Module 3)

```bash
# Список всех профилей
curl http://localhost:8100/api/admin/profiles

# Создать профиль
curl -X POST http://localhost:8100/api/admin/profiles \
  -H "Content-Type: application/json" \
  -d '{"user_id": "new_user", "full_name": "Новый Пользователь", "role": "employee"}'

# Обновить профиль
curl -X PUT http://localhost:8100/api/admin/profiles/new_user \
  -H "Content-Type: application/json" \
  -d '{"user_id": "new_user", "full_name": "Обновленный Пользователь", "role": "manager"}'

# Удалить профиль
curl -X DELETE http://localhost:8100/api/admin/profiles/new_user

# Синхронизировать все профили
curl -X POST http://localhost:8100/api/admin/profiles/sync
```
## Доступные стили

- `chekhov` - Антон Чехов (ироничный, меланхоличный)
- `dovlatov` - Сергей Довлатов (самоирония, короткие фразы)
- `pelevin` - Виктор Пелевин (постмодерн, сатира)
- `ilfpetrov` - Ильф и Петров (юмор, сатира, остроумие)

## Конфигурация

Создайте `.env` файл на основе `.env.example`:

```bash
cp .env.example .env
```

### Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `PORT` | `8080` | HTTP порт backend |
| `WS_PORT` | `8081` | WebSocket порт |
| `ORCHESTRATOR_HOST` | `localhost` | Хост Core Engine |
| `ORCHESTRATOR_PORT` | `8001` | Порт gRPC Core Engine |
| `MODULE3_HOST` | `localhost` | Хост Module 3 Admin API |
| `MODULE3_PORT` | `8200` | Порт Module 3 Admin API |
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `CHAT_DB_PATH` | `/app/backend/chat_profiles.db` | Путь к SQLite файлу профилей |

## Архитектура данных

### База данных профилей (SQLite)

Профили пользователей хранятся в локальной SQLite базе данных:

```sql
CREATE TABLE profiles (
    user_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    role TEXT,
    department TEXT,
    honorific_type TEXT,
    communication_mode TEXT,
    known_triggers TEXT,  -- JSON array
    core_user_id TEXT,    -- Ссылка на Core Engine
    last_updated TEXT
)
```

Синхронизация происходит при старте backend и через API endpoints:
- `/api/v1/profiles/sync` - синхронизация всех профилей
- `/api/v1/profiles` (POST) - создание профиля с автоматической синхронизацией

### Связь с Core Engine

Module 2 использует Core Engine для:
1. **Исходных данных** - загрузка профилей при первом запуске
2. **Адаптации сообщений** - вызов через gRPC для обработки сообщений
3. **Синхронизации** - поддержание актуальности профилей

Ключевое поле связи: `core_user_id` = `user_id` из Core Engine

## Синхронизация профилей с Module 3

Module 2 получает профили для чата из Module 3 через API:

**Module 3 endpoints:**
- **GET `/api/v1/admin/chat_profiles`** - получить все профили чата
- **POST `/api/v1/admin/chat_profiles/sync`** - синхронизировать профили

**Module 2 endpoints:**
- **POST `/api/v1/profiles/sync_module3`** - синхронизировать профили из Module 3

### Конфигурация

Добавьте переменные в `.env`:

```
MODULE3_HOST=host.docker.internal
MODULE3_PORT=8200
```

## Верификация

### Проверка endpoints

```bash
# Проверка REST API
curl http://localhost:8080/api/v1/users

# Проверка профилей
curl http://localhost:8080/api/v1/profiles

# Проверка состояния
curl http://localhost:8080/health
```

### Демонстрация работы

1. Откройте `http://localhost:8080` в браузере
2. Выберите пользователя (например, `alex_i`)
3. Выберите получателя (например, `petr_s`)
4. Отправьте сообщение
5. В том же окне или в другом окне браузера с другим пользователем получите и прочитайте сообщение

## Логирование

Backend логирует все события в stdout:

```
INFO - New connection: sess_1. Total: 1
INFO - User authenticated: alex_i (sess_1)
INFO - Recipient selected: petr_s (sess_1)
INFO - Message sent from alex_i to petr_s: Hello...
INFO - Client disconnected: sess_1
```

## Решение проблем

### Проблема: WebSocket connection failed

**Решение**: Убедитесь, что backend запущен и слушает на правильном порту

```bash
# Проверить порты
lsof -i :8080
```

### Проблема: Frontend не подключается к backend

**Решение**: Проверить CORS и порты

```bash
# Проверить backend
curl http://localhost:8080/health

# Проверить логи backend
docker logs chameleon-chat-1
```

### Проблема: Core Engine недоступен

**Решение**: Убедитесь, что Core Engine запущен

```bash
# Проверить порт Core Engine
curl http://localhost:8001/health

# Или запустить core-engine из module-1
cd ../module-1-core-engine
docker-compose up -d
```

## Разработка

### Добавление нового WebSocket сообщения

1. Обновить `src/backend/websocket.py` - обработчики событий
2. Обновить `src/frontend/src/services/websocket.js` - клиент
3. Обновить `src/frontend/src/components/ChatRoom.jsx` - UI

### Добавление нового REST endpoint

1. Обновить `src/backend/api.py` - добавить endpoint
2. Обновить `src/frontend/src/services/api.js` - вызов API

## Лицензия

MIT
