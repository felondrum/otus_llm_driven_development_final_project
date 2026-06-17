#!/usr/bin/env python3
"""
Проверка, что culture chunks добавляются в промпт для LLM.

Запуск:
    poetry run python tests/e2e/test_culture_in_prompts.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator.context_assembler import get_context_assembler


def test_culture_in_prompt():
    """Test that culture chunks are properly included in prompt."""
    assembler = get_context_assembler()

    # Test with sample culture chunks
    culture_chunks = [
        {
            "text": "Принцип 1: Открытость и честность - мы ценим открытость во всех формах коммуникации.",
            "section_title": "Открытость и честность",
            "section_level": 2,
        },
        {
            "text": "Принцип 2: Уважение к собеседнику - каждый человек достоин уважения.",
            "section_title": "Уважение к собеседнику",
            "section_level": 2,
        },
    ]

    # Assemble context with culture
    context = assembler.assemble_context(
        original_text="Нужно обсудить новый проект",
        culture_chunks=culture_chunks
    )

    # Verify context contains culture section
    assert "Корпоративная культура" in context, \
        "Context should contain culture section header"

    # Verify culture chunks are in context
    for chunk in culture_chunks:
        text = chunk.get("text", "")
        if text:
            assert text[:50] in context or text[:50].lower() in context.lower(), \
                "Culture chunk should be in context"

    # Verify specific chunks content
    assert "Открытость и честность" in context
    assert "Уважение к собеседнику" in context

    # Verify instructions contain culture references
    assert "корпоративную культуру" in context.lower()
    assert "ценности" in context.lower()

    print("✅ All checks passed!")
    print("\n--- Sample prompt with culture ---")
    print(context[:2000])  # Print first 2000 chars
    print("\n--- End of sample ---")


if __name__ == "__main__":
    try:
        test_culture_in_prompt()
        print("\n✅ Culture chunks successfully added to prompts!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
