"""
Main FastAPI application for ELAMS
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import db_manager, init_database
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    AuditMiddleware,
    RequestIDMiddleware
)
from app.core.exceptions import ELAMSException
from app.core.logging import setup_logging
from app.api import router as api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting ELAMS application...")
    
    try:
        # Initialize database connections
        await db_manager.connect()
        logger.info("Database connections established")
        
        # Initialize database tables
        if settings.is_development:
            await init_database()
            logger.info("Database tables initialized")
        
        # Start background tasks
        asyncio.create_task(start_background_tasks())
        logger.info("Background tasks started")
        
        logger.info("ELAMS application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ELAMS application...")
    
    try:
        # Close database connections
        await db_manager.disconnect()
        logger.info("Database connections closed")
        
        # Stop background tasks
        await stop_background_tasks()
        logger.info("Background tasks stopped")
        
        logger.info("ELAMS application shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def start_background_tasks():
    """Start background tasks"""
    # Import here to avoid circular imports
    from app.core.tasks import (
        cleanup_expired_sessions,
        cleanup_expired_tokens,
        process_audit_logs,
        check_password_expiry,
        send_notification_digests
    )
    
    # Schedule background tasks
    tasks = [
        asyncio.create_task(cleanup_expired_sessions()),
        asyncio.create_task(cleanup_expired_tokens()),
        asyncio.create_task(process_audit_logs()),
        asyncio.create_task(check_password_expiry()),
        asyncio.create_task(send_notification_digests()),
    ]
    
    logger.info(f"Started {len(tasks)} background tasks")


async def stop_background_tasks():
    """Stop background tasks"""
    # Cancel all running tasks
    tasks = [task for task in asyncio.all_tasks() if not task.done()]
    if tasks:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url=settings.api_docs_url if settings.is_development else None,
        redoc_url=settings.api_redoc_url if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(api_router, prefix="/api")
    
    # Add health check endpoint
    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Health check endpoint"""
        try:
            db_status = await db_manager.health_check()
            return {
                "status": "healthy",
                "version": settings.app_version,
                "environment": settings.environment,
                "database": db_status
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "version": settings.app_version,
                    "environment": settings.environment
                }
            )
    
    # Add metrics endpoint (for Prometheus)
    if settings.prometheus_enabled:
        @app.get("/metrics", include_in_schema=False)
        async def metrics():
            """Prometheus metrics endpoint"""
            from app.core.metrics import generate_metrics
            return generate_metrics()
    
    return app


def setup_middleware(app: FastAPI):
    """Setup application middleware"""
    
    # Request ID middleware (should be first)
    app.add_middleware(RequestIDMiddleware)
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Trusted host middleware
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"] if settings.is_development else ["yourdomain.com", "*.yourdomain.com"]
        )
    
    # Gzip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Audit middleware (should be last to capture all request data)
    app.add_middleware(AuditMiddleware)


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers"""
    
    @app.exception_handler(ELAMSException)
    async def elams_exception_handler(request: Request, exc: ELAMSException):
        """Handle custom ELAMS exceptions"""
        logger.error(f"ELAMS exception: {exc.message}", extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details if settings.is_development else None
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP exception: {exc.detail}", extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()}", extra={
            "path": request.url.path,
            "method": request.method
        })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors() if settings.is_development else None
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }, exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": str(exc) if settings.is_development else None
                }
            }
        )


# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True,
        workers=1 if settings.is_development else settings.workers,
    )