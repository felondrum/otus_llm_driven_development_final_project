#!/bin/bash
# ===========================================
# Chameleon Chat - Проверка статуса
# ===========================================
# Проверяет доступность всех сервисов

echo "=========================================="
echo "📋 Chameleon Chat - Проверка статуса"
echo "=========================================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

# Проверка .env
if [ ! -f .env ]; then
    echo "❌ .env не найден. Скопируйте .env.example в .env"
    exit 1
fi

# Проверка ключей Langfuse
if grep -q "your-langfuse-public-key-here" .env; then
    echo "⚠️  Используются дефолтные ключи Langfuse. Обновите .env"
fi

echo "🔧 Проверка контейнеров..."
echo ""

# Статус контейнеров
docker-compose ps

echo ""
echo "=========================================="
echo "🌐 Проверка портов..."
echo "=========================================="

# Проверка портов
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port &> /dev/null; then
        echo "✅ $service (port $port) - запущен"
    else
        echo "❌ $service (port $port) - не запущен"
    fi
}

check_port 3000 "Langfuse"
check_port 8001 "Orchestrator"
check_port 8002 "Retriever"
check_port 8003 "LLM Gateway"
check_port 5432 "PostgreSQL"
check_port 6333 "Qdrant"
check_port 6379 "Redis"
check_port 11434 "Ollama"

echo ""
echo "=========================================="
echo "📡 Проверка HTTP сервисов..."
echo "=========================================="

# Проверка HTTP endpoints
check_http() {
    local url=$1
    local service=$2
    if curl -s -o /dev/null -w "%{http_code}" $url | grep -q "200\|301\|302"; then
        echo "✅ $service - доступен"
    else
        echo "❌ $service - недоступен (проверьте логи: make logs)"
    fi
}

echo "Проверка HTTP сервисов (может занять время)..."
sleep 2

check_http "http://localhost:3000" "Langfuse Web"
check_http "http://localhost:8001/health" "Orchestrator"
check_http "http://localhost:8002/health" "Retriever"
check_http "http://localhost:8003/health" "LLM Gateway"

echo ""
echo "=========================================="
echo "📝 Логи последних 20 строк..."
echo "=========================================="
docker-compose logs --tail=20

echo ""
echo "=========================================="
echo "💡 Дополнительно:"
echo "=========================================="
echo "  make logs           - Логи (Ctrl+C для выхода)"
echo "  docker-compose ps   - Статус контейнеров"
echo "  docker-compose down - Остановить все"
echo ""
