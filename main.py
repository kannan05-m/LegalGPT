from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from legalgpt_backend.routers import analysis, chat, compare, documents, export, template, upload

app = FastAPI(title="LegalGPT", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(template.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(documents.router, prefix="/api")

frontend_dir = Path(__file__).parent / "legalgpt_frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
