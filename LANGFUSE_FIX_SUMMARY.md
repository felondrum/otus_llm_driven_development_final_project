# Решение проблемы с трейсами в module-1-core-engine

## Проблема

После первого fix attempt трейсы стали пустыми. Пользователь сообщил: "в тресах все логи стали еще хуже. пропали даже редки логи взаимодействия с llm".

## Причины и решение

### 1. Отсутствие инициализации Langfuse в LLM Gateway

**Проблема**: LLM GatewayNever вызывал `init_langfuse()` в startup_event(), поэтому получал ошибку "Cannot log generation - Langfuse not initialized".

**Решение**: Добавлен вызов `init_langfuse()` в `app.on_event("startup")` в файле `/src/llm_gateway/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    try:
        init_langfuse()  # ← Добавлено
        init_components()
        log_info("LLM Gateway started")
    except Exception as e:
        log_error("Failed to initialize LLM Gateway", error=str(e))
```

### 2. Неправильный импорт в llm_gateway/main.py

**Проблема**: Дублирование импорта `log_generation` и отсутствие других необходимых импортов (`OllamaProvider`, `YandexProvider`, `Router`, `get_cache`, `LoadBalancer`, `CircuitBreaker`).

**Решение**: Исправлены импорты в начале файла:

```python
# Import common modules
from common.logging import logger, log_info, log_error
from common.metrics import measure_latency
from common.schemas import (
    GenerationConfig,
    ModelComplexity,
)
from common.langfuse_integration import init_langfuse, log_generation
from .providers.base import LLMProvider
from .providers.ollama_provider import OllamaProvider
from .providers.yandex_provider import YandexProvider
from .router import get_router, Router
from .cache import get_cache, LLMCache
from .load_balancer import get_load_balancer, LoadBalancer
from .circuit_breaker import CircuitBreaker
```

### 3. Конфликт локальных и глобальных переменных

**Проблема**: В функции `generate()` был локальный импорт `from common.langfuse_integration import log_generation`, который создавал конфликт с глобальным импортом и приводил к ошибке "cannot access local variable 'log_generation' where it is not associated with a value".

**Решение**: Удален локальный импорт внутри блока `if cached`, используется только глобальный импорт:

```python
# ДО (ошибка):
if cached:
    log_info("Cache hit for generate", model=model)
    try:
        from common.langfuse_integration import log_generation  # ← Удалить
        
        log_generation(...)

# ПОСЛЕ (правильно):
if cached:
    log_info("Cache hit for generate", model=model)
    try:
        # Убран локальный импорт - используем глобальный
        log_generation(...)  # ← Теперь используем глобальный импорт
```

### 4. Неправильный API для Langfuse v3

**Проблема**: В Langfuse v3 API изменился:
- Метод `span.log()` не поддерживается (`'LangfuseSpan' object has no attribute 'log'`)
- Метод `langfuse.generation()` не поддерживается (`'Langfuse' object has no attribute 'generation'`)
- Метод `langfuse.trace()` не поддерживается (`'Langfuse' object has no attribute 'trace'`)

**Решение**: Использование правильного API для Langfuse v3 - метод `start_as_current_generation()`:

```python
def log_generation(
    name: str,
    model: str,
    prompt: str,
    completion: str,
    usage: Optional[Dict[str, int]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Log a generation to Langfuse using Langfuse v3 API."""
    logger.info(f"Logging generation to Langfuse: {name}, model={model}")

    if _langfuse:
        try:
            # Используем start_as_current_generation для Langfuse v3
            with _langfuse.start_as_current_generation(
                name=name,
                model=model,
                input=prompt,
                output=completion,
                usage_details=usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata=metadata or {},
            ) as generation:
                # Generation автоматически завершается при выходе из контекста
                logger.info(f"Generation logged to Langfuse: {name}")
        except Exception as e:
            logger.error(f"Failed to log generation to Langfuse: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.warning("Cannot log generation - Langfuse not initialized")
```

## Итоговый результат

После всех исправлений трейсы успешно записываются в ClickHouse:

### Типы наблюдаемых генераций:
- `orchestrator-processing` - 257 генераций от Orchestrator
- `generation-yandex:ya-llm` - генерации от LLM Gateway (напрямую к LLM)
- `generation-cache-hit` - кэш-хиты от LLM Gateway

### Экспорт в Langfuse:
- Данные отправляются через OTLP gRPC на `langfuse-worker:4317`
- Окружение настроено в docker-compose:
  ```
  OTEL_EXPORTER_OTLP_ENDPOINT=http://langfuse-worker:4317
  OTEL_EXPORTER_OTLP_PROTOCOL=grpc
  ```

### Доступ к данным:
- ClickHouse: `http://localhost:8123` (пользователь: clickhouse, пароль: clickhouse123)
- Langfuse UI: `http://localhost:3000`
- Таблицы в ClickHouse:
  - `default.observations` - все наблюдения (SPAN, GENERATION)
  - `default.traces` - трейсы
  - `default.analytics_traces`, `default.analytics_observations` - аналитические таблицы

## Ключевые особенности Langfuse v3 в этом стеке

1. **OTLP gRPC**: Langfuse v3 использует OpenTelemetry Protocol для отправки данных через gRPC, а не HTTP API.

2. **Контекстные менеджеры**: Методы `start_as_current_span()` и `start_as_current_generation()` возвращают контекстные менеджеры, которые должны использоваться с `with` statement. Прямой вызов `__enter__()`/`__exit__()` не работает.

3. **Методы SDK**:
   - `langfuse.start_as_current_generation()` - создает GENERATION observation
   - `langfuse.start_as_current_span()` - создает SPAN observation
   - `langfuse.trace()` - создает трейс (но в Langfuse v3 SDK эти методы могут отличаться)

4. **Автоматическая отправка**: Нет необходимости вручную вызывать `flush()` - данные автоматически отправляются через OTLP экспортер.

## Файлы, которые были изменены

1. `/module-1-core-engine/src/llm_gateway/main.py` - добавлен `init_langfuse()` в startup_event, исправлены импорты
2. `/module-1-core-engine/src/common/langfuse_integration.py` - обновлен `log_generation()` для использования `start_as_current_generation()`
3. Созданы тесты: `tests/e2e/test_langfuse.py`, `tests/e2e/test_full_flow_traces.py`
