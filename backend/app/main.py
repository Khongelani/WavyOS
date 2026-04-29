import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.routers import auth, companies, contacts, outreach, pipeline, tasks, dashboard, admin, execution, sprint

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.seed import run_seed
    await run_seed()
    log.info("startup_complete", environment=settings.ENVIRONMENT)
    yield
    await engine.dispose()


app = FastAPI(title="WavyOS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"] if settings.ENVIRONMENT == "development" else settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "code": "INTERNAL_ERROR"},
    )


app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(contacts.router)
app.include_router(outreach.router)
app.include_router(pipeline.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(execution.router)
app.include_router(sprint.router)


@app.get("/")
async def root():
    return {"service": "WavyOS API", "version": "1.0.0", "status": "running"}
