from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import auth, catalog, chat, conversations, health
from app.core.config import ROOT
from app.db.session import init_schema


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_schema()
    except SQLAlchemyError as exc:
        logging.warning("MySQL chưa sẵn sàng; chat khách vẫn có thể sử dụng (%s)", type(exc).__name__)
    yield


app = FastAPI(title="AI-4GYM Local RAG API", version="0.2.0", lifespan=lifespan)


@app.exception_handler(SQLAlchemyError)
async def database_error(_request: Request, _error: SQLAlchemyError) -> JSONResponse:
    logging.warning("MySQL unavailable while handling request: %s", type(_error).__name__)
    return JSONResponse(status_code=503, content={"detail": "MySQL chưa sẵn sàng. Bật MySQL trong Serbay và kiểm tra BE/.env."})


for router in (auth.router, conversations.router, health.router, catalog.router, chat.router):
    app.include_router(router)


FRONTEND_DIST = ROOT.parent / "FE" / "dist"


@app.get("/{full_path:path}", include_in_schema=False)
def frontend(full_path: str) -> FileResponse:
    if full_path.startswith(("auth/", "conversations/", "api/")):
        raise HTTPException(status_code=404)
    dist = FRONTEND_DIST.resolve()
    requested = (dist / full_path).resolve()
    if requested.is_relative_to(dist) and requested.is_file():
        return FileResponse(requested)
    index = dist / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="Frontend chưa build. Chạy npm run build trong FE/")
