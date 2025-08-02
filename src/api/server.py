"""Main FastAPI server application for the Intelligent MCP Chatbot."""

import time
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import router, init_chatbot_engine
from .auth import init_auth_manager
from .middleware import setup_middleware
from .websocket import websocket_endpoint
from utils.logger import get_logger

logger = get_logger(__name__)


def create_app(config: Dict[str, Any]) -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title="Intelligent MCP Chatbot API",
        description="A highly extensible, plugin-based chatbot system with Model Context Protocol (MCP) server integration support",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Initialize authentication
    auth_config = config.get("api", {}).get("auth", {})
    init_auth_manager(auth_config)
    
    # Setup middleware
    api_config = config.get("api", {})
    setup_middleware(app, api_config)
    
    # Include API routes
    app.include_router(router, prefix="/api/v1", tags=["chatbot"])
    
    # Add WebSocket endpoint
    app.add_websocket_route("/ws", websocket_endpoint)
    app.add_websocket_route("/ws/{user_id}", websocket_endpoint)
    
    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "timestamp": time.time()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "timestamp": time.time()
            }
        )
    
    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        logger.info("Starting Intelligent MCP Chatbot API server...")
        
        # Initialize chatbot engine
        from core.chatbot_engine import ChatbotEngine
        engine = ChatbotEngine(config)
        await engine.start()
        init_chatbot_engine(engine)
        
        logger.info("API server started successfully")
    
    # Add shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logger.info("Shutting down Intelligent MCP Chatbot API server...")
        
        # Stop chatbot engine
        from .routes import get_chatbot_engine
        try:
            engine = get_chatbot_engine()
            await engine.stop()
        except Exception as e:
            logger.error(f"Error stopping chatbot engine: {e}")
        
        logger.info("API server shutdown completed")
    
    return app


def run_server(config: Dict[str, Any], host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    import uvicorn
    
    # Create app
    app = create_app(config)
    
    # Get server config
    api_config = config.get("api", {})
    server_host = api_config.get("host", host)
    server_port = api_config.get("port", port)
    
    # Run server
    uvicorn.run(
        app,
        host=server_host,
        port=server_port,
        log_level="info",
        access_log=True,
        reload=False  # Set to True for development
    )


if __name__ == "__main__":
    # Load configuration
    from utils.config_manager import ConfigurationManager
    
    config_manager = ConfigurationManager()
    config = config_manager.get_all_config()
    
    # Run server
    run_server(config) 