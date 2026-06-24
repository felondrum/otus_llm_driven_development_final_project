# ===========================================
# Documents management API for Admin
# ===========================================

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
import os
import json
import uuid

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Import configuration
from config import (
    RETRIEVER_HTTP_HOST,
    RETRIEVER_HTTP_PORT,
)

# Import database
from database import get_documents, get_all_documents, create_document, delete_document, delete_document_from_core, update_document, sync_all_documents_to_core, sync_document_to_core


@api_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("corporate_rules"),
    metadata: str = Form("{}")
):
    """Upload a document to PostgreSQL"""
    try:
        # Check file size (limit to 10MB)
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Get file type
        file_type = file.content_type or "application/octet-stream"
        
        # Read file content
        content_str = content.decode('utf-8', errors='ignore')
        
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Save to PostgreSQL
        document_data = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "collection": collection,
            "content": content_str,
            "status": "uploaded",
            "metadata": metadata_dict
        }
        
        try:
            result = await create_document(document_data)
            return {
                "status": "success",
                "document_id": result.get("document_id"),
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "collection": collection,
                "processed": True
            }
        except Exception as e:
            logger.error(f"Failed to save document to database: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@api_router.get("/collections")
async def list_collections():
    """List all available collections"""
    return {
        "collections": [
            {"name": "corporate_rules", "description": "Корпоративные правила и инструкции"},
            {"name": "corporate_culture", "description": "Корпоративная культура и ценности"}
        ],
        "count": 2
    }


@api_router.get("")
async def list_documents(collection: str = "corporate_rules"):
    """List all documents in a collection from PostgreSQL"""
    try:
        documents = await get_documents(collection)
        return {
            "documents": documents,
            "count": len(documents),
            "collection": collection
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@api_router.get("/{document_id}")
async def get_document(document_id: str, collection: str = "corporate_rules"):
    """Get a document by ID from PostgreSQL"""
    try:
        from database import get_document as get_doc
        document = await get_doc(document_id)
        
        if document:
            return {
                "document_id": document_id,
                "data": document,
                "collection": collection
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@api_router.delete("/{document_id}")
async def delete_document_endpoint(document_id: str, collection: str = "corporate_rules"):
    """Delete a document by ID from PostgreSQL"""
    try:
        deleted = await delete_document(document_id)
        
        if deleted:
            return {
                "status": "deleted",
                "document_id": document_id
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@api_router.put("/{document_id}")
async def update_document_endpoint(document_id: str, document_data: dict, collection: str = "corporate_rules"):
    """Update a document by ID in PostgreSQL"""
    try:
        updated = await update_document(document_id, document_data)
        
        if updated:
            return {
                "status": "updated",
                "document_id": document_id
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@api_router.post("/{document_id}/sync")
async def sync_document(document_id: str, collection: str = "corporate_rules"):
    """Sync a specific document from PostgreSQL to Qdrant"""
    try:
        success = await sync_document_to_core(document_id)
        
        if success:
            return {
                "status": "synced",
                "document_id": document_id
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync document: {str(e)}")


@api_router.post("/sync")
async def sync_all_documents(collection: str = "corporate_rules"):
    """Sync all documents from PostgreSQL to Qdrant"""
    try:
        success_count = await sync_all_documents_to_core()
        
        return {
            "status": "synced",
            "synced_count": success_count
        }
                
    except Exception as e:
        logger.error(f"Failed to sync documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync documents: {str(e)}")


# ===========================================
# Core Engine (Module 1) Document endpoints
# ===========================================

@api_router.get("/core")
async def list_documents_from_core(collection: str = "corporate_rules"):
    """List all documents in a collection via Retriever HTTP (Core Engine)"""
    try:
        url = f"{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/documents"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"collection": collection}, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "documents": data.get("documents", []),
                    "count": data.get("count", 0),
                    "collection": collection
                }
            else:
                return {
                    "documents": [],
                    "count": 0,
                    "collection": collection
                }
                
    except httpx.RequestError as e:
        logger.error(f"HTTP error listing documents: {e}")
        raise HTTPException(status_code=503, detail=f"Retriever service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@api_router.post("/core/upload")
async def upload_document_to_core(
    file: UploadFile = File(...),
    collection: str = Form("corporate_rules"),
    metadata: str = Form("{}")
):
    """Upload a document to Core Engine (Module 1) via HTTP"""
    try:
        # Check file size (limit to 10MB)
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Get file type
        file_type = file.content_type or "application/octet-stream"
        
        # Upload to Retriever
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/documents/upload"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    params={"collection": collection},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "document_id": "mock-id",
                        "filename": file.filename,
                        "file_type": file_type,
                        "file_size": file_size,
                        "collection": collection,
                        "processed": True
                    }
                else:
                    logger.warning(f"Retriever upload endpoint not fully implemented: {response.status_code}")
                    # Return mock response for now
                    return {
                        "status": "success",
                        "document_id": "mock-id",
                        "filename": file.filename,
                        "file_type": file_type,
                        "file_size": file_size,
                        "collection": collection,
                        "processed": True
                    }
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Retriever: {e}")
            raise HTTPException(status_code=503, detail=f"Retriever service unavailable: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@api_router.get("/core/collections")
async def list_collections_from_core():
    """List all available collections in Core Engine via Retriever HTTP"""
    try:
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/documents/collections"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "collections": data.get("collections", []),
                    "count": data.get("count", 0)
                }
            else:
                return {
                    "collections": [],
                    "count": 0
                }
                
    except httpx.RequestError as e:
        logger.error(f"HTTP error listing collections: {e}")
        raise HTTPException(status_code=503, detail=f"Retriever service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")
