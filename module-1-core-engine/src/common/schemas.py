# Схемы данных

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# ===== UserProfile =====


class UserProfile(BaseModel):
    """User profile model."""

    user_id: str
    full_name: str
    role: str  # engineer, team_lead, director, hr, intern
    department: str
    honorific_type: int  # HonorificType enum
    communication_mode: int  # CommunicationMode enum
    known_triggers: List[str] = []
    adaptive_history_vector: List[float] = []
    last_updated: int = 0


# ===== CorporateRule =====


class CorporateRule(BaseModel):
    """Corporate rule model."""

    rule_id: str
    category: str  # address, tone, content, timing
    priority: int  # 1-10
    condition: str
    transformation: str
    example_original: str
    example_adapted: str


# ===== ArtisticStyle =====


class ArtisticStyle(BaseModel):
    """Artistic style model."""

    style_id: str
    style_name: str
    author: str
    sample_text: str
    emotion_tags: List[str] = []
    era: str


# ===== MessageRequest =====


class MessageRequest(BaseModel):
    """Incoming message request."""

    message_id: str
    sender_id: str
    recipient_id: str
    room_id: Optional[str] = None
    text: str
    style_name: Optional[str] = None
    metadata: Dict[str, str] = {}


# ===== MessageResponse =====


class MessageResponse(BaseModel):
    """Response with adapted message."""

    adapted_text: str
    was_adapted: bool
    confidence: float
    model_used: str
    processing_time_ms: int
    rules_applied: List[str] = []
    adaptation_metadata: Optional["AdaptationMetadata"] = None


# ===== AdaptationMetadata =====


class AdaptationMetadata(BaseModel):
    """Metadata about the adaptation process."""

    from_cache: bool = False
    fallback_used: bool = False
    fallback_reason: str = ""
    tokens_prompt: int = 0
    tokens_completion: int = 0


# ===== GenerationConfig =====


class GenerationConfig(BaseModel):
    """Configuration for text generation."""

    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: bool = False
    stop_sequences: List[str] = []
    style: Optional[str] = None


# ===== GenerateRequest =====


class GenerateRequest(BaseModel):
    """Request for text generation."""

    prompt: str
    complexity: int = 0  # ModelComplexity enum
    config: Optional[GenerationConfig] = None


# ===== GenerateResponse =====


class GenerateResponse(BaseModel):
    """Response from text generation."""

    text: str
    model_used: str
    complexity_used: int
    token_usage: Dict[str, int]
    latency_ms: int
    from_cache: bool


# ===== Enums (as integers for protobuf compatibility) =====


class HonorificType:
    """Honorific type enum."""

    HONORIFIC_UNSPECIFIED = 0
    FIRST_NAME = 1
    FIRST_LAST = 2
    PATRONYMIC = 3
    TITLE_LAST = 4


class CommunicationMode:
    """Communication mode enum."""

    MODE_UNSPECIFIED = 0
    FORMAL = 1
    INFORMAL = 2
    TECHNICAL = 3
    DIPLOMATIC = 4


class ModelComplexity:
    """Model complexity enum."""

    COMPLEXITY_UNSPECIFIED = 0
    FAST = 1
    BALANCED = 2
    POWERFUL = 3


# ===== Classification schemas =====

class MessageCategory:
    """Message category enum for classification."""

    GREETING = "приветствие"
    FAREWELL = "прощание"
    CRITICISM = "критика"
    FLATTERY = "ласть"
    OFFTOPIC = "офтопик"
    COMPLIMENT = "комплимент"
    COMPLAINT = "жалоба"
    REQUEST = "запрос"
    INFORMATION = "информация"
    EMOTION = "эмоция"
    UNKNOWN = "неизвестно"


class ClassificationResult(BaseModel):
    """Result of message classification."""

    category: str
    category_code: str
    confidence: float = 1.0
    processed_at: int = 0


class CultureSearchParams(BaseModel):
    """Parameters for culture search with classification."""

    query: str
    limit: int = 3
    category: Optional[str] = None
