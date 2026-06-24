# ===========================================
# Admin API Server for Module 3
# ===========================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import pathlib

# Create FastAPI app
app = FastAPI(
    title="Chameleon Admin API",
    description="Admin API for managing profiles, styles, rules, and documents",
    version="1.0.0",
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
from routes import profiles, chat_profiles, styles, rules, documents, system, users

# Include routers - must be before fallback to work correctly
app.include_router(profiles.api_router, prefix="/api/v1/admin/profiles", tags=["Profiles"])
app.include_router(chat_profiles.api_router, prefix="/api/v1/admin/chat_profiles", tags=["Chat Profiles"])
app.include_router(styles.api_router, prefix="/api/v1/admin/styles", tags=["Styles"])
app.include_router(rules.api_router, prefix="/api/v1/admin/rules", tags=["Rules"])
app.include_router(documents.api_router, prefix="/api/v1/admin/documents", tags=["Documents"])
app.include_router(system.api_router, prefix="/api/v1/admin/system", tags=["System"])
app.include_router(users.api_router, prefix="/api/v1/admin/users", tags=["Users"])


# Serve React frontend static files
frontend_dir = pathlib.Path(__file__).parent.parent / "frontend" / "dist"

# Mount static files directory
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")


@app.get("/")
async def root():
    """Root endpoint - serve React frontend"""
    if frontend_dir.exists():
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    return {"service": "chameleon-admin", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/v1/admin")
async def api_docs():
    """API documentation"""
    return {
        "service": "chameleon-admin",
        "version": "1.0.0",
        "endpoints": {
            "profiles": "/api/v1/admin/profiles",
            "chat_profiles": "/api/v1/admin/chat_profiles",
            "styles": "/api/v1/admin/styles",
            "rules": "/api/v1/admin/rules",
            "documents": "/api/v1/admin/documents",
            "system": "/api/v1/admin/system",
            "users": "/api/v1/admin/users"
        }
    }


# Fallback for all other routes - serve React frontend for SPA routing
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    """Serve React frontend for SPA routing"""
    # Don't serve React for API endpoints - these should return 404
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    
    # Serve React frontend for all other paths (SPA routing)
    if frontend_dir.exists():
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    return JSONResponse({"detail": "Not Found"}, status_code=404)


if __name__ == "__main__":
    port = int(os.environ.get("ADMIN_PORT", 8100))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
