# Module 3: Admin & Data Management

## Бизнес-смысл

Админ-интерфейс для управления данными системы Chameleon Chat.

### Функциональность

- **Профили (profiles)** - CRUD операции для модификации сообщений (Module 3 → Core Engine)
- **Профили чата (chat_profiles)** - CRUD операции для использования в чате (Module 2 ↔ Module 3)
- **Правила** - Управление корпоративными правилами
- **Стили** - Управление литературными стилями
- **Документы** - Загрузка и управление документами в RAG
- **Система** - Статус сервисов и управление кэшем

### Admin UI (React)

- Дашборд с метриками
- Таблицы с сортировкой и пагинацией
- Формы для создания/редактирования данных
- Загрузка файлов через HTML form

> 💡 **Примечание:** Для корректной работы модуль 3 должен быть запущен в той же Docker сети (chameleon-network), что и модули 1 и 2.

---

## Технологии

- **Backend**: Python 3.11 + FastAPI
- **Frontend**: React 18 + Vite
- **База данных**: PostgreSQL для профилей
- **Контейнеризация**: Docker + Docker Compose

---

## Архитектура

### Компоненты

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Admin Data (Module 3)                            │
│  ┌─────────────────┐  ┌─────────────────┐                         │
│  │ Admin API       │  │ Admin UI        │                         │
│  │ (FastAPI)       │  │ (React + Vite)  │                         │
│  │ - CRUD profiles │  │ - Dashboard     │                         │
│  │ - CRUD rules    │  │ - Tables        │                         │
│  │ - CRUD styles   │  │ - Forms         │                         │
│  │ - CRUD docs     │  │ - Upload        │                         │
│  └─────────────────┘  └─────────────────┘                         │
│  ┌─────────────────┐                                              │
│  │ PostgreSQL      │                                              │
│  │ (профили чата)  │                                              │
│  └─────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Поток обработки

```
Admin → Admin UI → Admin API → PostgreSQL
                          ↓
                     Core Engine
                          ↓
                    Profile Sync
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
module-3-admin-data/
├── src/
│   ├── admin_api/          # FastAPI сервер
│   │   ├── main.py         # Основной сервер
│   │   ├── routes/         # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── profiles.py
│   │   │   ├── rules.py
│   │   │   ├── styles.py
│   │   │   ├── documents.py
│   │   │   ├── system.py
│   │   │   └── users.py
│   │   └── services/       # Бизнес-логика
│   │       ├── document_processor.py
│   │       ├── bulk_importer.py
│   │       └── profile_generator.py
│   ├── data_loader/        # CLI инструменты
│   └── frontend_admin/     # React UI
│       ├── src/
│       │   ├── components/
│       │   │   ├── DataTable.jsx
│       │   │   ├── FileUploader.jsx
│       │   │   └── EditorForm.jsx
│       │   ├── pages/
│       │   │   ├── Dashboard.jsx
│       │   │   ├── Profiles.jsx
│       │   │   ├── Rules.jsx
│       │   │   ├── Styles.jsx
│       │   │   ├── Documents.jsx
│       │   │   └── System.jsx
│       │   └── App.jsx
│       └── package.json
├── scripts/               # Скрипты
├── tests/                 # Тесты
├── docker-compose.module.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/v1/admin/profiles` | GET | Список профилей (для модификации сообщений) |
| `/api/v1/admin/profiles` | POST | Создание профиля |
| `/api/v1/admin/profiles/{user_id}` | PUT | Обновление профиля |
| `/api/v1/admin/profiles/{user_id}` | DELETE | Удаление профиля |
| `/api/v1/admin/profiles/sync` | POST | Синхронизация всех профилей |
| `/api/v1/admin/chat_profiles` | GET | Список профилей чата |
| `/api/v1/admin/chat_profiles` | POST | Создание профиля чата |
| `/api/v1/admin/chat_profiles/{user_id}` | PUT | Обновление профиля чата |
| `/api/v1/admin/chat_profiles/{user_id}` | DELETE | Удаление профиля чата |
| `/api/v1/admin/chat_profiles/sync` | POST | Синхронизация всех профилей чата |
| `/api/v1/admin/rules` | GET | Список правил |
| `/api/v1/admin/rules` | POST | Создание правила |
| `/api/v1/admin/rules/{rule_id}` | PUT | Обновление правила |
| `/api/v1/admin/rules/{rule_id}` | DELETE | Удаление правила |
| `/api/v1/admin/rules/reload` | POST | Перезагрузка правил |
| `/api/v1/admin/styles` | GET | Список стилей |
| `/api/v1/admin/styles` | POST | Создание стиля |
| `/api/v1/admin/styles/{style_id}` | PUT | Обновление стиля |
| `/api/v1/admin/styles/{style_id}` | DELETE | Удаление стиля |
| `/api/v1/admin/documents/upload` | POST | Загрузка документа |
| `/api/v1/admin/documents` | GET | Список документов |
| `/api/v1/admin/documents/{id}` | DELETE | Удаление документа |
| `/api/v1/admin/system/status` | GET | Статус сервисов |
| `/api/v1/admin/system/cache/clear` | POST | Очистка кэша |
| `/api/v1/admin/system/rules/reload` | POST | Перезагрузка правил |

---

## Конфигурация

- **API Port**: 8100
- **Frontend Port**: 5174
- **Core Engine HTTP**: localhost:8001
- **Qdrant**: localhost:6333
- **Chat Frontend**: localhost:8080

---

## Быстрый старт

```bash
cd module-3-admin-data

# Собрать и запустить
docker-compose -f docker-compose.module.yml up -d

# Посмотреть логи
docker-compose -f docker-compose.module.yml logs -f

# Остановить
docker-compose -f docker-compose.module.yml down
```

---

## Интеграция с Module 2

Module 3 предоставляет API для получения профилей чата:

**Endpoint:** `GET /api/v1/admin/chat_profiles`

**Module 2 подключается как:**
- Хост: `host.docker.internal`
- Порт: `8200`

**Module 3 переменные окружения в docker-compose.yml:**

```yaml
- DATABASE_URL=postgresql://chameleon:chameleon123@host.docker.internal:5433/chameleon_admin
```
