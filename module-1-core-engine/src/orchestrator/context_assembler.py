# Сборщик контекста - сборка промпта для LLM

from typing import Dict, Any, List, Optional
from common.schemas import UserProfile, CorporateRule, ArtisticStyle, ClassificationResult


class ContextAssembler:
    """Assembles context for LLM from various sources."""

    def __init__(self):
        # Маппинг для перевода числовых кодов в читаемые строки
        self.honorific_type_map = {
            0: "не указано",
            1: "по имени (например, Алексей)",
            2: "по имени и фамилии (например, Алексей Иванов)",
            3: "по имени и отчеству (например, Алексей Петрович)",
            4: "с титулом (например, господин Иванов)",
        }

        self.communication_mode_map = {
            0: "не указано",
            1: "формальный",
            2: "неформальный",
            3: "технический",
            4: "дипломатичный",
        }

        self.role_map = {
            0: "не указано",
            1: "сотрудник",
            2: "старший сотрудник",
            3: "менеджер",
            4: "директор",
            5: "HR специалист",
            6: "стажер",
        }

    def assemble_context(
        self,
        original_text: str,
        profile: Optional[UserProfile] = None,
        rules: List[CorporateRule] = None,
        styles: List[ArtisticStyle] = None,
        style_name: Optional[str] = None,
        culture_chunks: List[Dict[str, Any]] = None,
        classification_result: Optional[ClassificationResult] = None,
    ) -> str:
        """
        Assembles context for LLM.

        Args:
            original_text: Original message text
            profile: Recipient user profile (optional)
            rules: Corporate rules to apply (optional)
            styles: Artistic styles examples (optional)
            style_name: Selected style name (optional)
            culture_chunks: Corporate culture chunks for RAG (optional)
            classification_result: Message classification result (optional)

        Returns:
            Formatted prompt for LLM
        """
        prompt_parts = []

        # Task description
        prompt_parts.append("Вы - помощник AI для адаптации деловых сообщений.")
        prompt_parts.append("")

        # Original message
        prompt_parts.append("## Исходное сообщение:")
        prompt_parts.append(original_text)
        prompt_parts.append("")

        # Message classification (new)
        if classification_result:
            prompt_parts.append("## Классификация сообщения:")
            prompt_parts.append(f"Категория: {classification_result.category}")
            prompt_parts.append("")
            prompt_parts.append("ВАЖНО: Учти классификацию сообщения при адаптации.")
            prompt_parts.append("")

        # Recipient profile
        if profile:
            # Support both dict and UserProfile objects
            profile_role = profile.get("role", "") if isinstance(profile, dict) else profile.role
            profile_department = profile.get("department", "") if isinstance(profile, dict) else profile.department
            profile_full_name = profile.get("full_name", "") if isinstance(profile, dict) else profile.full_name
            profile_honorific_type = profile.get("honorific_type", 0) if isinstance(profile, dict) else profile.honorific_type
            profile_communication_mode = profile.get("communication_mode", 0) if isinstance(profile, dict) else profile.communication_mode
            profile_known_triggers = profile.get("known_triggers", []) if isinstance(profile, dict) else profile.known_triggers
            
            prompt_parts.append("## Профиль получателя:")
            if profile_full_name:
                prompt_parts.append(f"Полное имя: {profile_full_name}")
            prompt_parts.append(f"Роль: {self._format_role(profile_role)}")
            prompt_parts.append(f"Отдел: {profile_department}")
            prompt_parts.append(
                f"Стиль общения: {self._format_communication_mode(profile_communication_mode)}"
            )
            prompt_parts.append(
                f"Форма обращения: {self._format_honorific_type(profile_honorific_type)}"
            )

            if profile_known_triggers:
                prompt_parts.append(
                    f"Известные триггеры общения: {', '.join(profile_known_triggers)}"
                )

            prompt_parts.append("")

        # Corporate rules
        if rules:
            prompt_parts.append("")
            prompt_parts.append("## Корпоративные правила коммуникации:")
            for i, rule in enumerate(rules, 1):
                # Handle both dict and Pydantic model (and protobuf)
                # Protobuf uses transformation_prompt, Pydantic uses transformation
                transformation = None
                category = None
                priority = 0
                if isinstance(rule, dict):
                    transformation = rule.get("transformation_prompt") or rule.get("transformation")
                    category = rule.get("category")
                    priority = rule.get("priority", 0)
                else:
                    # Check for protobuf/dict-like attribute
                    if hasattr(rule, "transformation_prompt"):
                        transformation = rule.transformation_prompt
                    elif hasattr(rule, "transformation"):
                        transformation = rule.transformation
                    if hasattr(rule, "category"):
                        category = rule.category
                    if hasattr(rule, "priority"):
                        priority = rule.priority
                
                if transformation:
                    category_str = category if category else "general"
                    prompt_parts.append(
                        f"{i}. [{category_str}] Приоритет {priority}: {transformation}"
                    )
                if hasattr(rule, "example_original") and hasattr(rule, "example_adapted"):
                    if rule.example_original and rule.example_adapted:
                        prompt_parts.append(
                            f"   Пример: '{rule.example_original}' → '{rule.example_adapted}'"
                        )
                # Add instruction for rule application
                prompt_parts.append(f"   ВАЖНО: Применяйте это правило при адаптации сообщения.")
            prompt_parts.append("")

        # Corporate culture (RAG)
        if culture_chunks:
            prompt_parts.append("")
            prompt_parts.append("## Корпоративная культура:")
            for i, chunk in enumerate(culture_chunks, 1):
                # Extract section title if available
                section_title = chunk.get('section_title', 'Раздел')
                text = chunk.get('text', '')
                # Increased limit to 500 chars for better context
                if len(text) > 500:
                    text = text[:500] + '...'
                prompt_parts.append(f"{i}. [{section_title}] {text}")
            prompt_parts.append("")

        # Selected style
        if style_name:
            prompt_parts.append(f"## Требуемый стиль: {style_name}")
            prompt_parts.append("")

        # Artistic styles (with style instructions)
        if styles:
            prompt_parts.append("")
            prompt_parts.append("## Примеры применения стиля:")
            
            # Add system instruction for style (only if style_name is specified)
            if style_name:
                prompt_parts.append(f"**Инструкция:** Применяйте стиль '{style_name}' при адаптации сообщения.")
                prompt_parts.append("Используйте характерные для этого стиля:")
                prompt_parts.append("- Лексику и терминологию")
                prompt_parts.append("- Ритм и интонацию предложений")
                prompt_parts.append("- Эмоциональную окраску")
                prompt_parts.append("- Общую манеру выражения мыслей")
                prompt_parts.append("")
            
            for i, style in enumerate(styles[:3], 1):
                # Handle both PostgreSQL and Qdrant style formats
                style_name_local = None
                author = ""
                sample_text = ""
                emotion_tags = []
                
                if hasattr(style, 'style_name'):
                    # Qdrant format
                    style_name_local = style.style_name or style.name or ""
                    author = style.author or ""
                    sample_text = style.sample_text or ""
                    if hasattr(style, 'emotion_tags'):
                        emotion_tags = style.emotion_tags or []
                else:
                    # PostgreSQL format (dict)
                    style_name_local = style.get("name") or style.get("style_name") or ""
                    author = style.get("author", "")
                    sample_text = style.get("sample_text", "")
                    emotion_tags = style.get("emotion_tags", []) or []
                    
                    # Try to extract from examples if not directly available
                    examples = style.get("examples", [])
                    if examples and isinstance(examples, list) and len(examples) > 0:
                        first_example = examples[0]
                        if isinstance(first_example, dict):
                            sample_text = first_example.get("output", "") or sample_text
                            note = first_example.get("note", "")
                            if note and "Author:" in note:
                                author = note.replace("Author:", "").strip()
                    
                    # Extract emotion_tags from tone
                    tone = style.get("tone", "")
                    if tone and isinstance(tone, str):
                        emotion_tags = [t.strip() for t in tone.split(",") if t.strip()]
                
                # Show more context from sample (300 chars instead of 150)
                sample = sample_text[:300] if len(sample_text) > 300 else sample_text
                
                prompt_parts.append(f"{i}. {style_name_local} — {author}")
                prompt_parts.append(f"   Пример: {sample}")
                
                # Add emotion tags if available
                if emotion_tags:
                    prompt_parts.append(f"   Эмоции: {', '.join(emotion_tags)}")
            prompt_parts.append("")

        # Detailed instructions
        prompt_parts.append("")
        prompt_parts.append("## Инструкции:")
        prompt_parts.append("1. Примените системный стиль (если указан) — используйте характерную лексику и интонацию")
        prompt_parts.append("2. Учтите профиль получателя (роль, отдел, стиль общения)")
        prompt_parts.append("3. Примените корпоративные правила коммуникации (если указаны)")
        prompt_parts.append("4. Следуйте примерам стиля для выбора тона и формулировок")
        prompt_parts.append("5. Учтите корпоративную культуру (ценности, принципы)")
        prompt_parts.append("6. Сохраните исходный смысл и ключевую информацию")
        prompt_parts.append(
            "7. Выведите ТОЛЬКО переписанное сообщение, без объяснений или дополнительного текста"
        )
        prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _format_honorific_type(self, value: Any) -> str:
        """Convert honorific type to readable string (handles both int and string values)."""
        if value is None:
            return "не указано"

        # If it's a string, map it directly
        string_map = {
            "first_name": "по имени (например, Алексей)",
            "patronymic": "по имени и отчеству (например, Алексей Петрович)",
            "last_name": "по имени и фамилии (например, Алексей Иванов)",
            "title": "с титулом (например, господин Иванов)",
        }
        
        if isinstance(value, str):
            return string_map.get(value.lower(), "не указано")

        # If it's an integer enum value
        if isinstance(value, int):
            return self.honorific_type_map.get(value, "не указано")

        return str(value)

    def _format_communication_mode(self, value: Any) -> str:
        """Convert communication mode to readable string (handles both int and string values)."""
        if value is None:
            return "не указано"

        # If it's a string, map it directly
        string_map = {
            "informal": "неформальный",
            "formal": "формальный",
            "neutral": "нейтральный",
            "technical": "технический",
            "collaborative": "дипломатичный",
        }
        
        if isinstance(value, str):
            return string_map.get(value.lower(), "не указано")

        # If it's an integer enum value
        if isinstance(value, int):
            return self.communication_mode_map.get(value, "не указано")

        return str(value)

    def _format_role(self, value: Any) -> str:
        """Convert role to readable string (handles both int and string values)."""
        if value is None:
            return "не указано"

        # If it's a string, map it to readable format
        string_map = {
            "engineer": "инженер",
            "senior_engineer": "старший инженер",
            "team_lead": "тимлид",
            "manager": "менеджер",
            "hr_manager": "HR менеджер",
            "director": "директор",
            "sales_director": "директор по продажам",
            "frontend": "frontend разработчик",
            "backend": "backend разработчик",
            "employee": "сотрудник",
            "intern": "стажер",
        }
        
        if isinstance(value, str):
            return string_map.get(value.lower(), value)

        # If it's an integer enum value
        if isinstance(value, int):
            return self.role_map.get(value, "не указано")

        return str(value)

    def parse_llm_response(self, response: str, original_text: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract adaptation info.

        Args:
            response: Raw response from LLM
            original_text: Original message text

        Returns:
            Dictionary with adaptation info
        """
        # Check if response is different from original
        was_adapted = response.strip() != original_text.strip()

        # Extract confidence (in production, would use LLM confidence score)
        confidence = 0.95 if was_adapted else 1.0

        return {
            "adapted_text": response,
            "was_adapted": was_adapted,
            "confidence": confidence,
        }


# Global assembler instance
_assembler: Optional[ContextAssembler] = None


def get_context_assembler() -> ContextAssembler:
    """Get global assembler instance."""
    global _assembler
    if _assembler is None:
        _assembler = ContextAssembler()
    return _assembler
