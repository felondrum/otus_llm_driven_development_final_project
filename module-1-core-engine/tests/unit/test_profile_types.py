"""Тест для проверки типов полей в profile."""

import sys
import os

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import chameleon.core.v1.retriever_pb2 as retriever_pb2

# Создаем тестовый profile
profile = retriever_pb2.UserProfile(
    user_id="test_user",
    full_name="Test User",
    role="engineer",
    department="backend",
    honorific_type=1,  # FIRST_NAME
    communication_mode=2,  # INFORMAL
)

print("Типы полей в retriever_pb2.UserProfile:")
print(f"  user_id: {type(profile.user_id)} = {profile.user_id}")
print(f"  full_name: {type(profile.full_name)} = {profile.full_name}")
print(f"  role: {type(profile.role)} = {profile.role}")
print(f"  department: {type(profile.department)} = {profile.department}")
print(f"  honorific_type: {type(profile.honorific_type)} = {profile.honorific_type}")
print(f"  communication_mode: {type(profile.communication_mode)} = {profile.communication_mode}")

# Проверяем маппинг
from orchestrator.context_assembler import get_context_assembler

assembler = get_context_assembler()

print("\nРезультаты маппинга:")
print(f"  role: {assembler._format_role(profile.role)}")
print(f"  honorific_type: {assembler._format_honorific_type(profile.honorific_type)}")
print(f"  communication_mode: {assembler._format_communication_mode(profile.communication_mode)}")

# Проверяем сборку контекста
prompt = assembler.assemble_context(
    original_text="Привет, как дела?",
    profile=profile,
)

print("\nПромпт для LLM:")
print(prompt)
