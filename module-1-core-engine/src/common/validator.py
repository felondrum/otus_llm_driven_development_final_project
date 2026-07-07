# Валидация входных данных

import uuid
from typing import Dict, Any, Tuple, Optional

# Russian to English style name mapping
STYLE_NAME_MAPPING = {
    "чеховский": "chekhov",
    "чехов": "chekhov",
    "довлатовский": "dovlatov",
    "довлатов": "dovlatov",
    "пелевинский": "pelevin",
    "пелевин": "pelevin",
    "илфпетровский": "ilfpetrov",
    "илфпетров": "ilfpetrov",
    "chekhov": "chekhov",
    "dovlatov": "dovlatov",
    "pelevin": "pelevin",
    "ilfpetrov": "ilfpetrov",
}


def normalize_style_name(style_name: Optional[str]) -> Optional[str]:
    """
    Normalize style name from Russian to English.

    Args:
        style_name: Style name (can be Russian or English)

    Returns:
        English style name or None
    """
    if style_name is None or style_name == "":
        return style_name
    
    style_lower = style_name.lower().strip()
    return STYLE_NAME_MAPPING.get(style_lower, style_lower)


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate as UUID

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_message_id(value: str) -> bool:
    """
    Validate message ID.

    Accepts valid UUIDs or non-empty strings for flexibility.

    Args:
        value: String to validate as message ID

    Returns:
        True if valid message ID, False otherwise
    """
    if not isinstance(value, str) or not value:
        return False

    # Accept valid UUIDs or any non-empty string
    if validate_uuid(value):
        return True

    # Allow non-empty strings that aren't UUIDs (for backward compatibility/testing)
    return len(value.strip()) > 0


def validate_text_length(
    text: str, min_length: int = 1, max_length: int = 4000
) -> bool:
    """
    Validate text length.

    Args:
        text: Text to validate
        min_length: Minimum length (default: 1)
        max_length: Maximum length (default: 4000)

    Returns:
        True if length is valid, False otherwise
    """
    if not isinstance(text, str):
        return False
    return min_length <= len(text) <= max_length


def validate_style_name(style_name: Optional[str]) -> bool:
    """
    Validate artistic style name.

    Args:
        style_name: Style name to validate (can be None or empty string)

    Returns:
        True if valid style name, None, or empty string, False otherwise
    """
    if style_name is None or style_name == "":
        return True

    # Accept both lowercase strings and integer enum values
    if isinstance(style_name, int):
        valid_styles = [0, 1, 2, 3]  # Enum values
        return style_name in valid_styles

    # String validation - support both English IDs and Russian names
    style_lower = style_name.lower().strip()
    
    return style_lower in STYLE_NAME_MAPPING


def validate_role(role: Optional[str]) -> bool:
    """
    Validate role value.

    Args:
        role: Role to validate (can be None)

    Returns:
        True if valid role or None, False otherwise
    """
    if role is None:
        return True

    # Accept both lowercase strings and integer enum values
    if isinstance(role, int):
        valid_roles = [0, 1, 2, 3, 4, 5]  # Enum values
        return role in valid_roles

    # String validation
    valid_roles = [
        "employee",
        "engineer",
        "team_lead",
        "manager",
        "director",
        "hr",
        "intern",
    ]
    return role.lower() in valid_roles


def validate_honorific_type(honorific_type: Any) -> bool:
    """
    Validate honorific type.

    Args:
        honorific_type: Can be string (first_name, patronymic, etc.) or int (enum value)

    Returns:
        True if valid, False otherwise
    """
    if honorific_type is None:
        return True

    # Accept both strings and integer enum values
    if isinstance(honorific_type, int):
        valid_types = [0, 1, 2, 3, 4]  # HonorificType enum values
        return honorific_type in valid_types

    # String validation
    valid_types = ["first_name", "patronymic", "last_name", "title", "default"]
    return honorific_type.lower() in valid_types


def validate_communication_mode(communication_mode: Any) -> bool:
    """
    Validate communication mode.

    Args:
        communication_mode: Can be string (informal, formal, etc.) or int (enum value)

    Returns:
        True if valid, False otherwise
    """
    if communication_mode is None:
        return True

    # Accept both strings and integer enum values
    if isinstance(communication_mode, int):
        valid_modes = [0, 1, 2, 3, 4]  # CommunicationMode enum values
        return communication_mode in valid_modes

    # String validation
    valid_modes = ["informal", "formal", "neutral", "authoritative", "collaborative"]
    return communication_mode.lower() in valid_modes


class InputValidator:
    """Validator for incoming message data."""

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate message data structure and values.

        Args:
            message: Dictionary containing message data

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Проверка обязательных полей
        required_fields = ["message_id", "sender_id", "recipient_id", "text"]
        for field in required_fields:
            if field not in message:
                return False, f"Missing required field: {field}"
            if message[field] is None:
                return False, f"Required field cannot be null: {field}"

        # Валидация message_id (UUID or non-empty string)
        if not validate_message_id(str(message["message_id"])):
            return (
                False,
                "Invalid message_id format (must be valid UUID or non-empty string)",
            )

        # Валидация sender_id (UUID)
        if not validate_uuid(str(message["sender_id"])):
            return False, "Invalid sender_id format (must be valid UUID)"

        # Валидация recipient_id (UUID or user_id string)
        # Accept UUID5 format OR non-empty string (for user_id like 'alex_i')
        recipient_id_str = str(message["recipient_id"])
        is_valid_recipient = (
            validate_uuid(recipient_id_str) or 
            (isinstance(message["recipient_id"], str) and len(message["recipient_id"].strip()) > 0)
        )
        if not is_valid_recipient:
            return False, "Invalid recipient_id format (must be valid UUID or user_id string)"

        # Валидация room_id (optional, UUID if present)
        if "room_id" in message and message["room_id"] is not None:
            if not validate_uuid(str(message["room_id"])):
                return False, "Invalid room_id format (must be valid UUID)"

        # Валидация текста
        if not validate_text_length(str(message["text"])):
            return False, "Text length must be between 1 and 4000 characters"

        # Валидация style_name (optional)
        if "style_name" in message and message["style_name"] is not None:
            if not validate_style_name(message["style_name"]):
                return (
                    False,
                    "Invalid style_name (must be: chekhov, dovlatov, pelevin, ilfpetrov)",
                )

        # Валидация metadata (optional)
        if "metadata" in message and message["metadata"] is not None:
            if not isinstance(message["metadata"], dict):
                return False, "metadata must be a dictionary"
            for key, value in message["metadata"].items():
                if not isinstance(key, str) or not isinstance(value, str):
                    return False, "All metadata keys and values must be strings"

        return True, ""

    @staticmethod
    def validate_profile(profile: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate user profile data.

        Args:
            profile: Dictionary containing profile data

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        required_fields = ["user_id", "full_name"]
        for field in required_fields:
            if field not in profile:
                return False, f"Missing required field: {field}"

        # Валидация user_id (UUID)
        if not validate_uuid(str(profile["user_id"])):
            return False, "Invalid user_id format (must be valid UUID)"

        # Валидация роли если есть
        if "role" in profile and profile["role"] is not None:
            if not validate_role(profile["role"]):
                return (
                    False,
                    "Invalid role (must be: employee, team_lead, manager, director, hr, intern)",
                )

        # Валидация department (optional string)
        if "department" in profile and profile["department"] is not None:
            if not isinstance(profile["department"], str):
                return False, "department must be a string"

        # Валидация honorific_type (can be string or int)
        if "honorific_type" in profile and profile["honorific_type"] is not None:
            if not validate_honorific_type(profile["honorific_type"]):
                return False, "Invalid honorific_type"

        # Валидация communication_mode (can be string or int)
        if (
            "communication_mode" in profile
            and profile["communication_mode"] is not None
        ):
            if not validate_communication_mode(profile["communication_mode"]):
                return False, "Invalid communication_mode"

        return True, ""
