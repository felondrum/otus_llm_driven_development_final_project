#!/bin/bash

# ===========================================
# Скрипт запуска модуля 2 - Chat Frontend
# ===========================================

echo "=== Запуск Chameleon Chat Frontend ==="
echo ""

# Проверить, установлен ли docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

# Проверить, установлен ли docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

# Проверить, запущен ли docker daemon
docker info &> /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Docker daemon не запущен. Запустите Docker и повторите попытку."
    exit 1
fi

echo "✓ Docker доступен"

# Перейти в директорию модуля 2
cd "$(dirname "$0")/.."

echo "✓ Перешли в директорию модуля 2"
echo ""

# Проверить наличие Dockerfile
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile не найден"
    exit 1
fi

echo "✓ Dockerfile найден"

# Проверить наличие docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml не найден"
    exit 1
fi

echo "✓ docker-compose.yml найден"
echo ""

# Спросить пользователя, что он хочет сделать
echo "Выберите действие:"
echo "1) Запустить все контейнеры"
echo "2) Остановить все контейнеры"
echo "3) Пересобрать и запустить"
echo "4) Показать статус контейнеров"
echo "5) Посмотреть логи"
echo ""

read -p "Введите номер действия [1]: " action

case $action in
    1|*)
        echo ""
        echo "=== Запуск контейнеров ==="
        docker-compose up -d
        echo ""
        echo "=== Контейнеры запущены ==="
        echo ""
        echo "Чат 1: http://localhost:8080"
        echo "Чат 2: http://localhost:8082"
        echo ""
        echo "Для остановки: docker-compose down"
        echo "Для просмотра логов: docker-compose logs -f"
        ;;
    2)
        echo ""
        echo "=== Остановка контейнеров ==="
        docker-compose down
        echo ""
        echo "=== Контейнеры остановлены ==="
        ;;
    3)
        echo ""
        echo "=== Пересборка и запуск ==="
        docker-compose down
        docker-compose build
        docker-compose up -d
        echo ""
        echo "=== Контейнеры пересобраны и запущены ==="
        ;;
    4)
        echo ""
        echo "=== Статус контейнеров ==="
        docker-compose ps
        ;;
    5)
        echo ""
        echo "=== Логи контейнеров (Ctrl+C для выхода) ==="
        docker-compose logs -f
        ;;
    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac
