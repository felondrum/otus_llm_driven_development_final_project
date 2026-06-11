# ========== МОДУЛЬ 3 ==========

## Папка module-3-admin-data/

### Файлы:

- README.md
- pyproject.toml - Python + FastAPI
- Dockerfile
- docker-compose.module.yml

### Подпапки:

- **src/admin_api/** - Admin API
  - main.py - FastAPI сервер (порт 8100)
  - routes/
    - documents.py - CRUD для RAG документов
    - profiles.py - Управление профилями
    - rules.py - Управление правилами
    - styles.py - Загрузка книг
    - users.py - Управление пользователями чата
    - system.py - Статус, перезагрузка
  - services/
    - document_processor.py
    - bulk_importer.py
    - profile_generator.py
  - auth.py - Простая админ-авторизация

- **src/data_loader/** - Загрузка данных
  - cli.py - Команды: load-rules, load-books
  - connectors/
    - local_fs.py
    - s3_connector.py
    - notion_connector.py - бонус
  - validators/
    - rule_validator.py
    - book_format_validator.py

- **src/frontend_admin/** - React админка
  - src/
    - App.jsx
    - pages/
      - Dashboard.jsx
      - Documents.jsx - Загрузка/удаление файлов
      - Profiles.jsx - Редактор профилей
      - Rules.jsx - Визуальный редактор правил
      - Styles.jsx - Загрузка книг
      - System.jsx - Статус сервисов
    - components/
      - FileUploader.jsx
      - DataTable.jsx
      - RuleEditor.jsx
  - package.json

- **tests/** - Тесты
  - unit/
    - test_document_processor.py
    - test_rule_validator.py
  - integration/
    - test_qdrant_operations.py
  - api_tests/
    - test_admin_endpoints.py

- **scripts/** - Скрипты
  - seed_demo_data.py
  - import_corporate_rules.sh
  - backup_qdrant.sh

- **uploads/** - Временное хранилище загруженных файлов
  - .gitkeep
