#!/bin/bash

# Фиксация импортов в stub файлах

echo "Fixing imports in stub files..."

# Обновление импортов в common_pb2_grpc.py
sed -i '' 's/import common_pb2 as common__pb2/import chameleon.core.v1.common_pb2 as common__pb2/g' src/chameleon/core/v1/common_pb2_grpc.py

# Обновление импортов в orchestrator_pb2_grpc.py
sed -i '' 's/import common_pb2 as common__pb2/import chameleon.core.v1.common_pb2 as common__pb2/g; s/import orchestrator_pb2 as orchestrator__pb2/import chameleon.core.v1.orchestrator_pb2 as orchestrator__pb2/g' src/chameleon/core/v1/orchestrator_pb2_grpc.py

# Обновление импортов в orchestrator_pb2.py
sed -i '' 's/import common_pb2/import chameleon.core.v1.common_pb2/g' src/chameleon/core/v1/orchestrator_pb2.py

# Обновление импортов в retriever_pb2_grpc.py
sed -i '' 's/import common_pb2 as common__pb2/import chameleon.core.v1.common_pb2 as common__pb2/g; s/import retriever_pb2 as retriever__pb2/import chameleon.core.v1.retriever_pb2 as retriever__pb2/g' src/chameleon/core/v1/retriever_pb2_grpc.py

# Обновление импортов в retriever_pb2.py
sed -i '' 's/import common_pb2/import chameleon.core.v1.common_pb2/g' src/chameleon/core/v1/retriever_pb2.py

# Обновление импортов в llm_gateway_pb2_grpc.py
sed -i '' 's/import common_pb2 as common__pb2/import chameleon.core.v1.common_pb2 as common__pb2/g; s/import llm_gateway_pb2 as llm__gateway__pb2/import chameleon.core.v1.llm_gateway_pb2 as llm__gateway__pb2/g' src/chameleon/core/v1/llm_gateway_pb2_grpc.py

# Обновление импортов в llm_gateway_pb2.py
sed -i '' 's/import common_pb2/import chameleon.core.v1.common_pb2/g' src/chameleon/core/v1/llm_gateway_pb2.py

echo "Imports fixed successfully!"
