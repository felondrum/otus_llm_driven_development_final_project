# ========== МОДУЛЬ 4 ==========

## Папка module-4-analytics/

### Файлы:

- README.md
- pyproject.toml
- Dockerfile
- docker-compose.module.yml

### Подпапки:

- **src/black_box/** - Black box consumer
  - main.py - Consumer из Redis/RabbitMQ
  - classifiers/
    - style_classifier.py - Тон сообщения
    - toxicity_detector.py
    - intent_classifier.py
    - cultural_analyzer.py
  - impact_analyzer.py - "А что было бы без адаптации"
  - profile_updater.py - Обновление профилей на основе истории
  - few_shot_generator.py - Создание примеров для обучения
  - storage/
    - postgres_writer.py
    - minio_writer.py
    - qdrant_writer.py

- **src/dashboard/** - FastAPI + Plotly дашборд
  - main.py - Сервер дашборда (порт 8200)
  - routes/
    - metrics.py
    - reports.py
    - export.py
  - visualizations/
    - sentiment_trends.py
    - adaptation_effectiveness.py
    - user_behavior.py
    - conflict_predictor.py
  - static/
    - index.html - Встроенный дашборд

- **src/rag_evaluator/** - RAGas интеграция
  - runner.py - Запуск оценки
  - test_sets/
    - create_benchmark.py
    - benchmark_v1.json
  - reporters/
    - console_report.py
    - html_report.py

- **tests/** - Тесты
  - unit/
    - test_style_classifier.py
    - test_impact_analyzer.py
  - integration/
    - test_black_box_pipeline.py
  - test_ragas/
    - test_rag_evaluation.py

- **scripts/** - Скрипты
  - run_nightly_evaluation.sh
  - generate_weekly_report.py
  - migrate_analytics_db.py

- **notebooks/** - Jupyter ноутбуки для исследования данных
  - 01_explore_messages.ipynb
  - 02_classifier_training.ipynb
  - 03_adaptation_impact_analysis.ipynb
