# Admin API routes package
from .profiles import api_router as profiles_router
from .rules import api_router as rules_router
from .styles import api_router as styles_router
from .documents import api_router as documents_router
from .system import api_router as system_router
from .users import api_router as users_router

__all__ = [
    'profiles_router',
    'rules_router', 
    'styles_router',
    'documents_router',
    'system_router',
    'users_router'
]
