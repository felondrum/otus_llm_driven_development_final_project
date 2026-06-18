# README Модуля 2 - Chat Frontend

## Обзор

Модуль 2 - это веб-интерфейс чата для системы Chameleon Chat. Он реализует WebSocket протокол для обмена сообщениями в реальном времени и REST API для управления.

**Особенности:**
- Один контейнер чата (с возможностью масштабирования через Redis Pub/Sub)
- Выбор тестового пользователя из списка (из Core Engine)
- Автоматическое случайное изменение фона
- Минималистичный UI с базовыми функциями
- Поддержка литературных стилей
- Межконтейнерная коммуникация через Redis Pub/Sub

## Технологический стек

- **Backend**: Python 3.11 + FastAPI + WebSocket
- **Frontend**: React 18 + Vite
- **Коммуникация**: gRPC (с Core Engine), Redis Pub/Sub
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

При запуске загружаются пользователи из Core Engine:

- `alex_i` - Иванов Алексей (engineer, informal)
- `petr_s` - Смирнов Петр (team_lead, formal)
- `anna_k` - Ковалева Анна (director, formal)
- `maria_s` - Смирнова Мария (hr_manager, formal)
- `dmitry_k` - Кузнецов Дмитрий (senior_engineer, technical)
- `elena_v` - Воронова Елена (team_lead, collaborative)
- `sergey_m` - Михайлов Сергей (intern, informal)
- `olga_a` - Алексеева Ольга (director, formal)

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
| `LOG_LEVEL` | `INFO` | Уровень логирования |

## Верификация

### Проверка endpoints

```bash
# Проверка REST API
curl http://localhost:8080/api/v1/users

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
