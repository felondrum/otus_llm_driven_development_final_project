# Как решить проблему с профилями

## Проблема
Профили не попадают в промпт, отображается "Unknown User" вместо реальных данных профиля.

## Причина
- Профили в системе хранятся с `user_id` в формате: `alex_i`, `petr_s`, `anna_k`
- При отправке сообщения используется имя пользователя ("Иван")
- `user_id` ≠ имя пользователя → профиль не находится → дефолтный профиль с "Unknown User"

## Решение

### Шаг 1: Найдите правильный user_id

Запустите скрипт поиска профиля по имени в Docker контейнере:

```bash
docker exec -it chameleon-orchestrator python /app/scripts/find_profile_by_name.py Иван
```

Результат:
```
Поиск профилей, содержащих 'Иван'...
============================================================
Найдено 1 профилей:

  user_id:    alex_i
  full_name:  Иванов Алексей Петрович
  role:       engineer
  department: backend
```

### Шаг 2: Используйте правильный user_id при отправке сообщения

**ПЛОХО:**
```python
recipient_id = "Иван"  # Имя пользователя - не найдет профиль
```

**ХОРОШО:**
```python
recipient_id = "alex_i"  # user_id из профиля - найдет профиль
```

### Шаг 3: Проверьте решение

Запустите тест полного потока:

```bash
docker exec -it chameleon-orchestrator python /app/scripts/test_profile_full_flow.py
```

Проверьте логи оркестратора:

```bash
docker logs chameleon-orchestrator -f | grep "Profile found"
```

Должно отображаться:
```
Profile found: user_id=alex_i, full_name=Иванов Алексей Петрович
```

## Дополнительные инструменты

### find_profile_by_name.py
Поиск профиля по частичному совпадению имени:
```bash
docker exec -it chameleon-orchestrator python /app/scripts/find_profile_by_name.py Иван
docker exec -it chameleon-orchestrator python /app/scripts/find_profile_by_name.py alex
```

### test_profile_lookup.py
Диагностика поиска профилей:
```bash
docker exec -it chameleon-retriever python /app/scripts/test_profile_lookup.py
```

### test_profile_full_flow.py
Полный тест потока с профилями:
```bash
docker exec -it chameleon-orchestrator python /app/scripts/test_profile_full_flow.py
```

## Что должно отображаться в промпте

После исправления в промпте должно отображаться:

```
## Профиль получателя:
Полное имя: Иванов Алексей Петрович
Роль: engineer
Отдел: backend
Стиль общения: неформальный
Форма обращения: по имени (например, Алексей)
```

## Документация

- `docs/PROFILE_FIX.md` - Полное руководство по решению проблемы
- `docs/PROFILE_FIX_QUICK.md` - Краткое руководство с примерами
- `docs/PROFILE_SUMMARY.md` - Резюме проблемы и решений
- `README.md` - Обновленный README с разделом о профилях

## Если проблема не решена

1. Проверьте, что профили загружены в Qdrant:
```bash
docker exec chameleon-qdrant curl http://localhost:6333/collections/user_profiles/points/count
```

2. Проверьте логи оркестратора на ошибки:
```bash
docker logs chameleon-orchestrator | grep -i "profile"
```

3. Запустите диагностику:
```bash
docker exec -it chameleon-retriever python /app/scripts/test_profile_lookup.py
```

## Пример полного потока

```bash
# 1. Найти user_id
docker exec -it chameleon-orchestrator python /app/scripts/find_profile_by_name.py Иван

# 2. Проверить загрузку в Qdrant
docker exec -it chameleon-retriever python /app/scripts/test_profile_lookup.py

# 3. Запустить полный тест
docker exec -it chameleon-orchestrator python /app/scripts/test_profile_full_flow.py

# 4. Проверить логи
docker logs chameleon-orchestrator -f | grep "Profile found"
```

## Контакты

Если проблема не решена:
1. Проверьте логи оркестратора на ошибки
2. Запустите `test_profile_lookup.py` для диагностики
3. Убедитесь, что используется правильный `user_id`
