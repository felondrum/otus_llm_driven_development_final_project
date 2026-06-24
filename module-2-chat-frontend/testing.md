# Testing Guide — Module 2: Chat Frontend

## Тестирование

### Интеграционные тесты

```bash
cd module-2-chat-frontend

# Установить зависимости
pip install -r requirements.txt

# Запустить тесты
pytest tests/integration/ -v
```

### Покрытие тестами

Тесты покрывают основные сценарии:
- WebSocket соединение
- Аутентификация
- Отправка и получение сообщений
- Синхронизация профилей

### Локальный запуск для разработки

```bash
cd module-2-chat-frontend

# Установить зависимости Python
pip install -r requirements.txt

# Запустить backend
cd src/backend
python -m main
```

### Верификация endpoints

```bash
# Проверка REST API
curl http://localhost:8080/api/v1/users

# Проверка профилей
curl http://localhost:8080/api/v1/profiles

# Проверка состояния
curl http://localhost:8080/health
```

### Демонстрация работы

1. Откройте `http://localhost:8080` в браузере
2. Выберите пользователя (например, `alex_i`)
3. Выберите получателя (например, `petr_s`)
4. Отправьте сообщение
5. В том же окне или в другом окне браузера с другим пользователем получите и прочитайте сообщение
