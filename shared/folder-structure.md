# Код, общий для всех модулей

## Папка shared/

### Файлы:

- pyproject.toml - Общая Python библиотека

### Подпапки:

- **src/shared_models/** - Общие модели данных
  - message.py
  - profile.py
  - rule.py
  - event.py

- **src/shared_utils/** - Утилиты
  - logging_utils.py
  - serialization.py
  - retry_decorator.py

- **src/grpc_stubs/** - Сгенерированные gRPC стабы из contracts/
  - orchestrator_pb2.py
  - orchestrator_pb2_grpc.py
  - ...

- **src/config/** - Общая конфигурация
  - settings.py
  - schemas.py

- **tests/** - Тесты
  - test_shared_utils.py
