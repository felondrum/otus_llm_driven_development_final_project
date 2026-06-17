#!/bin/bash
# ===========================================
# Chameleon Chat - Простой запуск
# ===========================================
# Запуск всех сервисов с одной командой
# Использует централизованный .env в корне

set -e

echo "=========================================="
echo "🚀 Chameleon Chat - Запуск"
echo "=========================================="
echo ""

# Проверка .env
if [ ! -f .env ]; then
    echo "⚠️  .env не найден, копируем из .env.example..."
    cp .env.example .env
    echo "✅ Создан .env. Обновите ключи в .env перед запуском!"
    exit 1
fi

# Проверка ключей Langfuse
if grep -q "your-langfuse-public-key-here" .env; then
    echo "❌ Используются дефолтные ключи Langfuse в .env"
    echo "Обновите .env с актуальными ключами и повторите попытку."
    exit 1
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен или не в PATH"
    exit 1
fi

# Проверка docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не установлен или не в PATH"
    exit 1
fi

echo "📝 Используется .env файл:"
echo "   $(pwd)/.env"
echo ""

# Запуск
echo "🚀 Запуск всех сервисов..."
docker-compose up -d

echo ""
echo "=========================================="
echo "✅ Сервисы запущены!"
echo "=========================================="
echo ""
echo "🔗 Langfuse UI: http://localhost:3000"
echo ""
echo "🔗 Core Engine:"
echo "   - Orchestrator: localhost:8001 (gRPC)"
echo "   - Retriever: localhost:8002 (gRPC)"
echo "   - LLM Gateway: localhost:8003 (HTTP)"
echo ""
echo "📊 Мониторинг:"
echo "   - ClickHouse: http://localhost:8123"
echo "   - MinIO Console: http://localhost:9001"
echo ""
echo "📈 Логи: docker-compose logs -f"
echo ""
