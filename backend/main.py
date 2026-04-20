from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading

from app.database import engine, Base
from app.routes import auth, users, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Kanban API", version="1.0.0", lifespan=lifespan)


@app.get("/threads")
def show_threads():
    threads = []
    for t in threading.enumerate():
        threads.append(
            {"name": t.name, "id": t.ident, "daemon": t.daemon, "alive": t.is_alive()}
        )
    return {"total_threads": threading.active_count(), "threads": threads}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/")
async def root():
    return {"message": "Kanban API работает!", "docs": "/docs"}
