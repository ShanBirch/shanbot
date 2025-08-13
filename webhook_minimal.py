import os
import sys
import json
import time
import asyncio
import logging
import traceback
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Shanbot Minimal Webhook", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Shanbot minimal webhook is running"
    }

# Basic webhook endpoint for ManyChat
@app.post("/webhook/manychat")
async def manychat_webhook(request: Request, background_tasks: BackgroundTasks):
    """Basic ManyChat webhook handler"""
    try:
        # Get the request body
        data = await request.json()
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        # Simple response
        response = {
            "status": "received",
            "timestamp": datetime.now().isoformat(),
            "subscriber_id": data.get("subscriber_id", "unknown"),
            "message": "Message received successfully"
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint
@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify the webhook is working"""
    return {
        "message": "Test endpoint working",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Shanbot minimal webhook on port {port}")
    uvicorn.run(
        "webhook_minimal:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 