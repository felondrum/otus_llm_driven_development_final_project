# Module 2: Chat Frontend

## Бизнес-смысл

Модуль 2 - это веб-интерфейс чата для системы Chameleon Chat. Он реализует WebSocket протокол для обмена сообщениями в реальном времени и REST API для управления.

### Особенности

- Один контейнер чата (с возможностью масштабирования через Redis Pub/Sub)
- Профили пользователей хранятся в Postgres БД
- Управление профилями через REST API
- Синхронизация с Core Engine через http
- Автоматическое случайное изменение фона
- Минималистичный UI с базовыми функциями
- Поддержка литературных стилей
- Межконтейнерная коммуникация через Redis Pub/Sub

---

## Технологии

- **Backend**: Python 3.11 + FastAPI + WebSocket
- **Frontend**: React 18 + Vite
- **Коммуникация**: http (с Core Engine), Redis Pub/Sub
- **База данных**: Postgres для профилей пользователей
- **Контейнеризация**: Docker + Docker Compose

> 💡 **Примечание:** Для корректной работы модуль 2 должен быть запущен в той же Docker сети (chameleon-network), что и модуль 1 (core-engine).

---

## Архитектура

### Компоненты

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Chat Frontend (Module 2)                         │
│  ┌─────────────────┐  ┌─────────────────┐                         │
│  │ Backend         │  │ Frontend        │                         │
│  │ (FastAPI)       │  │ (React + Vite)  │                         │
│  │ - WebSocket     │  │ - Chat UI       │                         │
│  │ - REST API      │  │ - Profile List  │                         │
│  │ - Profile Sync  │  │ - Message Send  │                         │
│  └─────────────────┘  └─────────────────┘                         │
│  ┌─────────────────┐                                              │
│  │ PostgreSQL      │                                              │
│  │ (профили)       │                                              │
│  └─────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Поток обработки

```
User → Chat UI → Backend → Profile Sync → Core Engine
          ↓
    WebSocket
          ↓
    Real-time messages
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
```

---

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

---

## Быстрый старт

```bash
cd module-2-chat-frontend
docker-compose up -d
```

- **Чат**: http://localhost:8080
