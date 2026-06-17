#!/bin/bash
# Скрипт для запуска e2e тестов
# Использование: ./run_e2e_tests.sh [test_file]

set -e

echo "=========================================="
echo "Запуск e2e тестов Core Engine"
echo "=========================================="

# Переменные окружения
export ORCHESTRATOR_HOST=${ORCHESTRATOR_HOST:-localhost}
export ORCHESTRATOR_PORT=${ORCHESTRATOR_PORT:-8001}
export RETRIEVER_HOST=${RETRIEVER_HOST:-localhost}
export RETRIEVER_PORT=${RETRIEVER_PORT:-8002}
export LLM_GATEWAY_URL=${LLM_GATEWAY_URL:-http://localhost:8003}
export QDRANT_HOST=${QDRANT_HOST:-localhost}
export QDRANT_PORT=${QDRANT_PORT:-6333}
export REDIS_PASSWORD=${REDIS_PASSWORD:-redis123}

# Функция проверки сервисов
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=${4:-30}
    local attempt=0
    
    echo "Ожидание $service_name на $host:$port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo "✓ $service_name готов"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo "✗ $service_name не запустился за $max_attempts секунд"
    return 1
}

# Функция проверки HTTP сервиса
wait_for_http_service() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-60}
    local attempt=0
    
    echo "Ожидание $service_name на $url..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s $url > /dev/null 2>&1; then
            echo "✓ $service_name готов"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo "✗ $service_name не запустился за $max_attempts секунд"
    return 1
}

# Основная функция
main() {
    local test_file=${1:-"tests/e2e/"}
    
    echo ""
    echo "1. Проверка зависимостей..."
    
    # Проверка poetry
    if ! command -v poetry &> /dev/null; then
        echo "✗ poetry не установлен"
        exit 1
    fi
    echo "✓ poetry установлен"
    
    # Проверка docker
    if ! command -v docker &> /dev/null; then
        echo "✗ docker не установлен"
        exit 1
    fi
    echo "✓ docker installed"
    
    echo ""
    echo "2. Запуск инфраструктуры..."
    
    # Запуск через docker-compose
    docker-compose -f docker-compose.module.yml up -d
    
    echo ""
    echo "3. Ожидание инициализации сервисов..."
    
    # Ждем инфраструктуру
    sleep 5
    
    # Проверка сервисов
    wait_for_service "$QDRANT_HOST" "$QDRANT_PORT" "Qdrant" 60 || exit 1
    wait_for_service "localhost" 6379 "Redis" 30 || exit 1
    wait_for_service "$ORCHESTRATOR_HOST" "$ORCHESTRATOR_PORT" "Orchestrator" 60 || exit 1
    wait_for_service "$RETRIEVER_HOST" "$RETRIEVER_PORT" "Retriever" 60 || exit 1
    
    # Проверка HTTP сервисов
    wait_for_http_service "$LLM_GATEWAY_URL/health" "LLM Gateway" 60 || exit 1
    wait_for_http_service "http://localhost:11434/" "Ollama" 60 || exit 1
    
    echo ""
    echo "4. Загрузка демо данных..."
    
    # Загрузка демо данных
    poetry run python scripts/e2e_load_demo_data.py
    
    echo ""
    echo "5. Запуск тестов..."
    
    # Запуск тестов
    poetry run pytest $test_file -v --tb=short
    
    echo ""
    echo "=========================================="
    echo "E2E тесты завершены успешно!"
    echo "=========================================="
}

# Обработка аргументов
case "${1:-}" in
    -h|--help)
        echo "Использование: $0 [test_file]"
        echo ""
        echo "Параметры:"
        echo "  test_file  - Файл или папка с тестами (по умолчанию: tests/e2e/)"
        echo ""
        echo "Примеры:"
        echo "  $0                    # Запустить все e2e тесты"
        echo "  $0 tests/e2e/test_full_flow.py  # Запустить конкретный файл"
        exit 0
        ;;
    "")
        main "tests/e2e/"
        ;;
    *)
        main "$1"
        ;;
esac
