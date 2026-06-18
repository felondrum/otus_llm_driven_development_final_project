# ===========================================
# Backend configuration
# ===========================================

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server configuration
PORT = int(os.environ.get("PORT", 8080))
WS_PORT = int(os.environ.get("WS_PORT", 8081))

# Core Engine (Orchestrator) configuration
ORCHESTRATOR_HOST = os.environ.get("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.environ.get("ORCHESTRATOR_PORT", 8001))

# Logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# App configuration
DEBUG = os.environ.get("NODE_ENV", "development") == "development"
