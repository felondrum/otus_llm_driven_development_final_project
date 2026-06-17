#!/bin/bash

# Генерация protobuf stubs для gRPC сервисов

echo "Generating protobuf stubs..."

# Создаем папку, если её нет
mkdir -p src/chameleon/core/v1

# Генерация stubs для common.proto (общие сообщения)
python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=src \
    --grpc_python_out=src \
    protos/common.proto

# Генерация stubs для orchestrator.proto
python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=src \
    --grpc_python_out=src \
    protos/orchestrator.proto

# Генерация stubs для retriever.proto
python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=src \
    --grpc_python_out=src \
    protos/retriever.proto

# Генерация stubs для llm_gateway.proto
python -m grpc_tools.protoc \
    -Iprotos \
    --python_out=src \
    --grpc_python_out=src \
    protos/llm_gateway.proto

# Перемещаем все сгенерированные файлы в правильную папку
mv src/*_pb2*.py src/chameleon/core/v1/ 2>/dev/null

# Фиксируем импорты в stub файлах
poetry run bash scripts/fix_stub_imports.sh

echo "Protobuf stubs generated successfully!"
