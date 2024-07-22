import asyncio
import os
from contextlib import asynccontextmanager
from enum import Enum

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi_pagination import add_pagination

from app.api_routes import api_router
from app.configs.run_configs import run_config
from app.middleware import LoggingMiddleware
from app.worker.segment_worker import SegmentWorker


class WorkerType(str, Enum):
    SEGMENT_WORKER = "segment_worker"


async def run_worker(worker_type: WorkerType):
    """ start the worker coroutine """
    if worker_type == WorkerType.SEGMENT_WORKER:
        segment_worker = SegmentWorker()
        await segment_worker.worker()
    else:
        raise ValueError(f"Unknown worker type: {worker_type}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ start the worker tasks when the app starts """
    segment_task = asyncio.create_task(run_worker(WorkerType.SEGMENT_WORKER))

    try:
        yield
    finally:
        segment_task.cancel()
        try:
            await segment_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
# added for local devlopment
if os.environ.get("ENV") == "local":
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_exception_handler(HTTPException, LoggingMiddleware.http_exception_handler)
app.add_exception_handler(
    RequestValidationError, LoggingMiddleware.validation_exception_handler
)
app.include_router(api_router, prefix="/v1")

add_pagination(app)

if __name__ == "__main__":
    uvicorn.run("main:app", **run_config.__dict__)
