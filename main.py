import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from core.memory import init_memory, recall, count
from core.cognition import wake, observe, stop_observing, respond


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_memory()
    task = asyncio.create_task(wake())
    yield
    task.cancel()


app = FastAPI(title="SHOGGOTH", docs_url=None, redoc_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/mind", response_class=HTMLResponse)
async def mind():
    path = os.path.join(os.path.dirname(__file__), "templates", "mind.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/thoughts")
async def api_thoughts(limit: int = 50, offset: int = 0):
    thoughts = await recall(limit, offset)
    total = await count()
    return JSONResponse({"thoughts": thoughts, "total": total})


@app.get("/api/stream")
async def stream(request: Request):
    q = observe()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    thought = await asyncio.wait_for(q.get(), timeout=30)
                    yield {
                        "event": "thought",
                        "data": f'{{"id":{thought["id"]},"content":{repr(thought["content"])},"created_at":"{thought["created_at"]}"}}',
                    }
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "alive"}
        finally:
            stop_observing(q)

    return EventSourceResponse(event_generator())


@app.post("/api/speak")
async def speak(request: Request):
    body = await request.json()
    user_input = body.get("input", "").strip()
    if not user_input:
        return JSONResponse({"error": "empty"}, status_code=400)

    reply = await respond(user_input)
    return JSONResponse({"response": reply})
