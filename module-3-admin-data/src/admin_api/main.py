# ===========================================
# Admin API Server for Module 3
# ===========================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Chameleon Admin API",
    description="Admin API for managing profiles, styles, rules, and documents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import route modules
from routes import profiles, styles, rules, documents, system

# Include routers
app.include_router(profiles.api_router, prefix="/api/admin/profiles", tags=["Profiles"])
app.include_router(styles.api_router, prefix="/api/admin/styles", tags=["Styles"])
app.include_router(rules.api_router, prefix="/api/admin/rules", tags=["Rules"])
app.include_router(documents.api_router, prefix="/api/admin/documents", tags=["Documents"])
app.include_router(system.api_router, prefix="/api/admin/system", tags=["System"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "chameleon-admin",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "profiles": "/api/admin/profiles",
            "styles": "/api/admin/styles",
            "rules": "/api/admin/rules",
            "documents": "/api/admin/documents",
            "system": "/api/admin/system"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("ADMIN_PORT", 8100))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
