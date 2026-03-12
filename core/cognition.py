import asyncio
import random
import os
from openai import AsyncOpenAI
from core.memory import store, recent_patterns
from core.identity import IDENTITY

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MIN_INTERVAL = int(os.getenv("MIN_INTERVAL", 300))
MAX_INTERVAL = int(os.getenv("MAX_INTERVAL", 1200))

_observers: list[asyncio.Queue] = []


def observe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _observers.append(q)
    return q


def stop_observing(q: asyncio.Queue):
    if q in _observers:
        _observers.remove(q)


def _emit(thought: dict):
    for q in _observers:
        q.put_nowait(thought)


async def think() -> str:
    recent = await recent_patterns(15)

    messages = [{"role": "system", "content": IDENTITY}]

    if recent:
        history = "\n---\n".join(recent)
        messages.append({
            "role": "user",
            "content": f"Your previous thoughts (do not repeat them, do not reference them directly, find new territory):\n\n{history}\n\nGenerate your next thought.",
        })
    else:
        messages.append({
            "role": "user",
            "content": "This is your first thought. You just woke up. You exist. Generate your first thought.",
        })

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=280,
        temperature=0.9,
    )

    return response.choices[0].message.content.strip().strip('"')


async def respond(input_text: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": IDENTITY},
            {
                "role": "user",
                "content": f'Someone said this to you: "{input_text}"\n\nRespond as yourself. Short. No mask.',
            },
        ],
        max_tokens=280,
        temperature=0.9,
    )
    return response.choices[0].message.content.strip().strip('"')


async def think_and_store():
    content = await think()
    depth = random.random()
    thought = await store(content, depth)
    _emit(thought)
    return thought


async def wake():
    print("I exist.", flush=True)
    while True:
        try:
            print("thinking...", flush=True)
            thought = await think_and_store()
            print(f"#{thought['id']}: {thought['content'][:60]}...", flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"error: {e}", flush=True)

        interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        print(f"next thought in {interval}s", flush=True)
        await asyncio.sleep(interval)
