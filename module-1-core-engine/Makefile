# ===========================================
# Makefile для module-1-core-engine
# ===========================================

.PHONY: help install test generate-proto fix-stubs run clean e2e e2e-setup

help:
	@echo "=========================================="
	@echo "Module 1 - Core Engine"
	@echo "=========================================="
	@echo ""
	@echo "Установка:"
	@echo "  make install         - Установить зависимости через poetry"
	@echo ""
	@echo "Тестирование:"
	@echo "  make test            - Запустить все тесты"
	@echo "  make test-unit       - Запустить юнит-тесты"
	@echo "  make test-int        - Запустить интеграционные тесты"
	@echo "  make test-e2e        - Запустить e2e тесты"
	@echo "  make e2e-setup       - Подготовить среду для e2e тестов"
	@echo ""
	@echo "Разработка:"
	@echo "  make lint            - Запустить linting"
	@echo "  make generate-proto  - Сгенерировать protobuf stubs"
	@echo "  make fix-stubs       - Исправить импорты в stub файлах"
	@echo ""
	@echo "Docker:"
	@echo "  make run             - Запустить все сервисы через docker-compose"
	@echo "  make run-orchestrator - Запустить только orchestrator"
	@echo "  make run-retriever   - Запустить только retriever"
	@echo "  make run-llm-gateway - Запустить только llm-gateway"
	@echo "  make stop            - Остановить сервисы"
	@echo ""
	@echo "Очистка:"
	@echo "  make clean           - Удалить кэш и папки"
	@echo ""

install:
	poetry install

test:
	poetry run pytest

test-unit:
	poetry run pytest tests/unit/

test-int:
	poetry run pytest tests/integration/

test-e2e:
	poetry run pytest tests/e2e/ -v

e2e-setup:
	@echo "Подготовка среды для e2e тестов..."
	@echo "1. Запуск инфраструктуры..."
	docker-compose -f docker-compose.module.yml up -d
	@echo "2. Ожидание инициализации (60 сек)..."
	@sleep 60
	@echo "3. Загрузка демо данных..."
	poetry run python scripts/e2e_load_demo_data.py
	@echo "4. Готово!"

lint:
	poetry run ruff check src/
	poetry run black --check src/

generate-proto:
	bash scripts/generate_proto.sh

fix-stubs:
	bash scripts/fix_stub_imports.sh

run:
	docker-compose -f docker-compose.module.yml up -d

run-orchestrator:
	docker-compose -f docker-compose.module.yml up orchestrator

run-retriever:
	docker-compose -f docker-compose.module.yml up retriever

run-llm-gateway:
	docker-compose -f docker-compose.module.yml up llm-gateway

stop:
	docker-compose -f docker-compose.module.yml down

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	docker-compose -f docker-compose.module.yml down -v
