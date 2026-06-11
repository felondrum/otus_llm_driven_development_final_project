```
otus_llm_driven_development_final_project/
│
├── README.md                          # Общее описание проекта
├── Makefile                           # Общие команды (make up, make test)
├── docker-compose.yaml                # Оркестрация всех модулей
├── docker-compose.override.yaml       # Для разработки (горячая перезагрузка)
├── .env.example
├── .gitignore
│
├── docs/                              # Общая документация
│   ├── architecture/
│   │   ├── system_architecture.md
│   │   ├── data_flow.md
│   │   └── api_contracts.md          # Контракты между модулями
│   ├── deployment/
│   │   ├── local_development.md
│   │   ├── production_guide.md
│   │   └── kubernetes/
│   └── user_guides/
│       ├── user_manual.md
│       └── admin_manual.md
│
├── contracts/                         # Общие protobuf/OpenAPI схемы
│   ├── proto/
│   │   ├── orchestrator.proto
│   │   ├── retriever.proto
│   │   ├── llm_gateway.proto
│   │   └── analytics.proto
│   ├── openapi/
│   │   ├── admin_api.yaml
│   │   └── chat_api.yaml
│   └── events/
│       └── message_event.avsc        # Avro схема для Kafka/Redis
│
├── scripts/                           # Общие скрипты
│   ├── bootstrap.sh                   # Первый запуск (скачать модели)
│   ├── seed_data.py                   # Загрузка тестовых данных
│   ├── generate_mock_profiles.py
│   └── run_e2e_tests.sh
│
├── tests/                             # E2E тесты (общие для всех модулей)
│   ├── e2e/
│   │   ├── test_full_flow.py
│   │   ├── test_adaptation.py
│   │   └── test_fallbacks.py
│   ├── performance/
│   │   ├── locustfile.py
│   │   └── scenarios/
│   └── fixtures/
│       ├── messages.json
│       ├── profiles.yaml
│       └── rules.md
│
├── module-1-core-engine/              # ========== МОДУЛЬ 1 ==========
│   ├── README.md
│   ├── pyproject.toml                 # Python проект
│   ├── Dockerfile
│   ├── docker-compose.module.yml      # Только для этого модуля
│   ├── .env
│   │
│   ├── src/
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # FastAPI/gRPC сервер
│   │   │   ├── handlers.py
│   │   │   ├── context_assembler.py
│   │   │   ├── cache_manager.py
│   │   │   └── config.py
│   │   │
│   │   ├── retriever/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── qdrant_client.py
│   │   │   ├── embeddings.py
│   │   │   ├── chunking.py
│   │   │   ├── hybrid_search.py
│   │   │   └── ingestion/
│   │   │       ├── file_loader.py
│   │   │       └── api_loader.py
│   │   │
│   │   ├── llm_gateway/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── router.py
│   │   │   ├── providers/
│   │   │   │   ├── base.py
│   │   │   │   ├── ollama_provider.py
│   │   │   │   └── openai_provider.py
│   │   │   ├── cache.py
│   │   │   └── load_balancer.py
│   │   │
│   │   └── common/
│   │       ├── schemas.py
│   │       ├── logging.py
│   │       ├── metrics.py             # Prometheus метрики
│   │       └── langfuse_integration.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── orchestrator/
│   │   │   ├── retriever/
│   │   │   └── llm_gateway/
│   │   ├── integration/
│   │   │   ├── test_orchestrator_retriever.py
│   │   │   └── test_llm_fallbacks.py
│   │   └── conftest.py
│   │
│   ├── scripts/
│   │   ├── download_models.py
│   │   └── warmup_cache.py
│   │
│   └── config/
│       ├── development.yaml
│       ├── production.yaml
│       └── models.yaml                # Какие модели доступны
│
├── module-2-chat-frontend/            # ========== МОДУЛЬ 2 ==========
│   ├── README.md
│   ├── package.json                   # Node.js/React проект
│   ├── Dockerfile
│   ├── docker-compose.module.yml
│   │
│   ├── src/
│   │   ├── backend/
│   │   │   ├── server.js              # Express/WebSocket сервер
│   │   │   ├── websocket/
│   │   │   │   ├── connection_manager.js
│   │   │   │   └── message_handler.js
│   │   │   ├── api/
│   │   │   │   ├── messages.js
│   │   │   │   ├── users.js
│   │   │   │   └── rooms.js
│   │   │   ├── grpc_client/
│   │   │   │   └── orchestrator_client.js
│   │   │   └── config.js
│   │   │
│   │   └── frontend/
│   │       ├── index.html
│   │       ├── src/
│   │       │   ├── App.jsx
│   │       │   ├── components/
│   │       │   │   ├── ChatWindow.jsx
│   │       │   │   ├── MessageList.jsx
│   │       │   │   ├── MessageInput.jsx
│   │       │   │   ├── UserList.jsx
│   │       │   │   ├── StyleSelector.jsx  # Выбор стиля (Чехов и т.д.)
│   │       │   │   └── AdaptationIndicator.jsx
│   │       │   ├── hooks/
│   │       │   │   ├── useWebSocket.js
│   │       │   │   └── useMessages.js
│   │       │   ├── services/
│   │       │   │   └── api.js
│   │       │   └── styles/
│   │       │       └── app.css
│   │       └── public/
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   └── websocket.test.js
│   │   ├── integration/
│   │   │   └── grpc_integration.test.js
│   │   └── e2e/
│   │       └── chat_flow.spec.js       # Playwright
│   │
│   ├── config/
│   │   ├── nginx.conf
│   │   └── env/
│   │       ├── development.env
│   │       └── production.env
│   │
│   └── assets/
│       ├── default_avatar.png
│       └── sounds/
│           └── notification.mp3
│
├── module-3-admin-data/               # ========== МОДУЛЬ 3 ==========
│   ├── README.md
│   ├── pyproject.toml                 # Python + FastAPI
│   ├── Dockerfile
│   ├── docker-compose.module.yml
│   │
│   ├── src/
│   │   ├── admin_api/
│   │   │   ├── main.py                # FastAPI сервер (порт 8100)
│   │   │   ├── routes/
│   │   │   │   ├── documents.py       # CRUD для RAG документов
│   │   │   │   ├── profiles.py        # Управление профилями
│   │   │   │   ├── rules.py           # Управление правилами
│   │   │   │   ├── styles.py          # Загрузка книг
│   │   │   │   ├── users.py           # Управление пользователями чата
│   │   │   │   └── system.py          # Статус, перезагрузка
│   │   │   ├── services/
│   │   │   │   ├── document_processor.py
│   │   │   │   ├── bulk_importer.py
│   │   │   │   └── profile_generator.py
│   │   │   └── auth.py                # Простая админ-авторизация
│   │   │
│   │   ├── data_loader/
│   │   │   ├── cli.py                 # Команды: load-rules, load-books
│   │   │   ├── connectors/
│   │   │   │   ├── local_fs.py
│   │   │   │   ├── s3_connector.py
│   │   │   │   └── notion_connector.py  # бонус
│   │   │   └── validators/
│   │   │       ├── rule_validator.py
│   │   │       └── book_format_validator.py
│   │   │
│   │   └── frontend_admin/            # React админка
│   │       ├── src/
│   │       │   ├── App.jsx
│   │       │   ├── pages/
│   │       │   │   ├── Dashboard.jsx
│   │       │   │   ├── Documents.jsx   # Загрузка/удаление файлов
│   │       │   │   ├── Profiles.jsx    # Редактор профилей
│   │       │   │   ├── Rules.jsx       # Визуальный редактор правил
│   │       │   │   ├── Styles.jsx      # Загрузка книг
│   │       │   │   └── System.jsx      # Статус сервисов
│   │       │   └── components/
│   │       │       ├── FileUploader.jsx
│   │       │       ├── DataTable.jsx
│   │       │       └── RuleEditor.jsx
│   │       └── package.json
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_document_processor.py
│   │   │   └── test_rule_validator.py
│   │   ├── integration/
│   │   │   └── test_qdrant_operations.py
│   │   └── api_tests/
│   │       └── test_admin_endpoints.py
│   │
│   ├── scripts/
│   │   ├── seed_demo_data.py
│   │   ├── import_corporate_rules.sh
│   │   └── backup_qdrant.sh
│   │
│   └── uploads/                       # Временное хранилище загруженных файлов
│       └── .gitkeep
│
├── module-4-analytics/                # ========== МОДУЛЬ 4 ==========
│   ├── README.md
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── docker-compose.module.yml
│   │
│   ├── src/
│   │   ├── black_box/
│   │   │   ├── main.py                # Consumer из Redis/RabbitMQ
│   │   │   ├── classifiers/
│   │   │   │   ├── style_classifier.py    # Тон сообщения
│   │   │   │   ├── toxicity_detector.py
│   │   │   │   ├── intent_classifier.py
│   │   │   │   └── cultural_analyzer.py
│   │   │   ├── impact_analyzer.py     # "А что было бы без адаптации"
│   │   │   ├── profile_updater.py     # Обновление профилей на основе истории
│   │   │   ├── few_shot_generator.py  # Создание примеров для обучения
│   │   │   └── storage/
│   │   │       ├── postgres_writer.py
│   │   │       ├── minio_writer.py
│   │   │       └── qdrant_writer.py
│   │   │
│   │   ├── dashboard/                 # FastAPI + Plotly
│   │   │   ├── main.py                # Сервер дашборда (порт 8200)
│   │   │   ├── routes/
│   │   │   │   ├── metrics.py
│   │   │   │   ├── reports.py
│   │   │   │   └── export.py
│   │   │   ├── visualizations/
│   │   │   │   ├── sentiment_trends.py
│   │   │   │   ├── adaptation_effectiveness.py
│   │   │   │   ├── user_behavior.py
│   │   │   │   └── conflict_predictor.py
│   │   │   └── static/
│   │   │       └── index.html         # Встроенный дашборд
│   │   │
│   │   └── rag_evaluator/             # RAGas интеграция
│   │       ├── runner.py              # Запуск оценки
│   │       ├── test_sets/
│   │       │   ├── create_benchmark.py
│   │       │   └── benchmark_v1.json
│   │       └── reporters/
│   │           ├── console_report.py
│   │           └── html_report.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_style_classifier.py
│   │   │   └── test_impact_analyzer.py
│   │   ├── integration/
│   │   │   └── test_black_box_pipeline.py
│   │   └── test_ragas/
│   │       └── test_rag_evaluation.py
│   │
│   ├── scripts/
│   │   ├── run_nightly_evaluation.sh
│   │   ├── generate_weekly_report.py
│   │   └── migrate_analytics_db.py
│   │
│   └── notebooks/                     # Jupyter для исследования данных
│       ├── 01_explore_messages.ipynb
│       ├── 02_classifier_training.ipynb
│       └── 03_adaptation_impact_analysis.ipynb
│
└── shared/                            # Код, общий для всех модулей
    ├── pyproject.toml                 # Общая Python библиотека
    ├── src/
    │   ├── shared_models/
    │   │   ├── message.py
    │   │   ├── profile.py
    │   │   ├── rule.py
    │   │   └── event.py
    │   ├── shared_utils/
    │   │   ├── logging_utils.py
    │   │   ├── serialization.py
    │   │   └── retry_decorator.py
    │   ├── grpc_stubs/                # Сгенерированные из contracts/
    │   │   ├── orchestrator_pb2.py
    │   │   ├── orchestrator_pb2_grpc.py
    │   │   └── ...
    │   └── config/
    │       ├── settings.py
    │       └── schemas.py
    │
    └── tests/
        └── test_shared_utils.py
```