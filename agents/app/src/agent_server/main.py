"""FastAPI application for Qiushuiai Agents (Agent Protocol Server)"""
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add graphs directory to Python path so react_agent can be imported
current_dir = Path(__file__).parent.parent.parent  # Go up to qiushuiai-agents root
graphs_dir = current_dir / "graphs"
if str(graphs_dir) not in sys.path:
    sys.path.insert(0, str(graphs_dir))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.authentication import AuthenticationMiddleware
import logging

from .core.database import db_manager
from .core.health import router as health_router
from .api.assistants import router as assistants_router
from .api.threads import router as threads_router
from .api.runs import router as runs_router
from .api.store import router as store_router
from .models.errors import AgentProtocolError, get_error_type
from .core.auth_middleware import get_auth_backend, on_auth_error
from .middleware import DoubleEncodedJSONMiddleware

# Task management for run cancellation
active_runs: Dict[str, asyncio.Task] = {}

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown"""
    # Startup: Initialize database and LangGraph components
    await db_manager.initialize()
    
    # Initialize LangGraph service
    from .services.langgraph_service import get_langgraph_service
    langgraph_service = get_langgraph_service()
    await langgraph_service.initialize()
    
    # Initialize event store cleanup task
    from .services.event_store import event_store
    await event_store.start_cleanup_task()
    
    yield
    
    # Shutdown: Clean up connections and cancel active runs
    for task in active_runs.values():
        if not task.done():
            task.cancel()
    
    # Stop event store cleanup task
    await event_store.stop_cleanup_task()
    
    await db_manager.close()


# Create FastAPI application
app = FastAPI(
    title="Qiushuiai Agents",
    description="Qiushuiai Agents: Production-ready Agent Protocol server built on LangGraph",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to handle double-encoded JSON from frontend
app.add_middleware(DoubleEncodedJSONMiddleware)

# Add authentication middleware (must be added after CORS)
app.add_middleware(
    AuthenticationMiddleware,
    backend=get_auth_backend(),
    on_error=on_auth_error
)

# Include routers
app.include_router(health_router, prefix="/qagent", tags=["Health"])
app.include_router(assistants_router, prefix="/qagent", tags=["Assistants"])
app.include_router(threads_router, prefix="/qagent", tags=["Threads"])
app.include_router(runs_router, prefix="/qagent", tags=["Runs"])
app.include_router(store_router, prefix="/qagent", tags=["Store"])


# Error handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed logging"""
    logger.error(
        f"Validation error for {request.method} {request.url.path}: {exc.errors()}",
        exc_info=True
    )
    
    # Format validation errors for response
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type")
        })
    
    return JSONResponse(
        status_code=422,
        content=AgentProtocolError(
            error="validation_error",
            message="Request validation failed",
            details={
                "validation_errors": error_details,
                "raw_errors": exc.errors()
            }
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def agent_protocol_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTP exceptions to Agent Protocol error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=AgentProtocolError(
            error=get_error_type(exc.status_code),
            message=exc.detail,
            details=getattr(exc, 'details', None)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    return JSONResponse(
        status_code=500,
        content=AgentProtocolError(
            error="internal_error",
            message="An unexpected error occurred",
            details={"exception": str(exc)}
        ).model_dump()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Qiushuiai Agents",
        "version": "0.1.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)