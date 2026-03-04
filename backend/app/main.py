from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import Body, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logger import logger
from app.tasks.celery import celery_app
from app.services.transformers.embedders import openai_text_small
from app.core.errors import AppError
from app.vector_store.qdrant import qdrant_store
from app.core.middleware.request_id import RequestIDMiddleware
from app.api.v0.auth import router as auth_router
from app.api.v0.usage import router as usage_router
from app.api.v0.files import router as files_router
from app.api.v0.events import router as events_router
from app.api.v0.chats import router as chats_router
from app.agents.persistence.pool import initialize_pool, close_pool
from app.agents.persistence.checkpointer import initialize_checkpointer
from app.agents.persistence.store import initialize_store
from app.db.duckdb import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Current dir: {os.getcwd()}")
    # Startup
    logger.info("Setting the default Celery app...")
    celery_app.set_default()
    logger.info(f"Celery default app is set to {celery_app.main}")
    logger.info("Initializing vector store...")
    try:
        await qdrant_store.create_collection(name=settings.QDRANT_COLLECTION, vector_size=openai_text_small.dimensions)
        await qdrant_store.create_indexed_payload_keys(
            collection=settings.QDRANT_COLLECTION, 
            keys=["user_id", "file_id", "parent_id", "chunk_type", "page_label"]
        )
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize vector store.")
        exit(1)
    logger.info("Initializing agent DB pool, checkpointer, and store..")
    await initialize_pool()
    await initialize_checkpointer()
    await initialize_store()
    logger.info("Initializing DuckDB...")
    await init_db()
    logger.info(f"App start up successful. Running on port: {settings.PORT or 8000}")
    
    yield
    
    # Shutdown 
    logger.info("Application shutdown")
    await close_pool()
    await close_db()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)

@app.exception_handler(AppError)
async def error_handler(_: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': {
                'code': exc.code,
                'message': exc.message,
                'field': exc.field,
            }
        }

    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v0")
app.include_router(usage_router, prefix="/api/v0")
app.include_router(files_router, prefix="/api/v0")
app.include_router(events_router, prefix="/api/v0")
app.include_router(chats_router, prefix="/api/v0")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME
    }

# Extend to a management/notification service if needed
@app.post("/api/v0/feedback", status_code=204)
async def get_feedback(data = Body(...)):
    ts = datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")
    with open("feedback-log.text", "a", encoding="utf-16") as f:
        record = f'ts: {ts}\nText: {data['text']}\n\n'
        f.write(record)
    



# Path to your built Vite app
static_dir = Path("dist") 
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    # Catch-all route: serve index.html for any other path and let FE app handle routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Serve the SPA for all routes not matched above.
        This allows client-side routing to work on refresh.
        """
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        return FileResponse(static_dir / "index.html")