import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(os.getenv("DATABASE_PATH", "./data/travel.db"))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, messages TEXT NOT NULL, plan TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS bookings (id TEXT PRIMARY KEY, session_id TEXT NOT NULL, option_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Travel Assistant API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class BookingRequest(BaseModel):
    session_id: str
    option_id: str


def get_session(session_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": row["id"], "messages": json.loads(row["messages"]), "plan": json.loads(row["plan"])}


@app.get("/health")
def health():
    with connect() as db:
        db.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/chat")
def chat(body: ChatRequest):
    if body.session_id:
        session = get_session(body.session_id)
    else:
        session = {"session_id": str(uuid4()), "messages": [], "plan": {"options": [], "selected_option_id": None}}

    # MOCK: заменим вызовом AI-агента и поискового сервиса на следующем этапе.
    reply = (
        "Я получил ваш запрос. Пока работает демонстрационный режим: "
        "ниже пример поездки, а не актуальное предложение."
    )
    if not session["plan"]["options"]:
        session["plan"]["options"] = [
            {
                "id": "demo-antalya",
                "destination": "Анталья, Турция",
                "total_price": 145000,
                "currency": "RUB",
                "nights": 7,
                "source": "demo",
                "is_live": False,
            },
            {
                "id": "demo-sharm",
                "destination": "Шарм-эль-Шейх, Египет",
                "total_price": 173000,
                "currency": "RUB",
                "nights": 7,
                "source": "demo",
                "is_live": False,
            },
        ]
    session["messages"].extend([
        {"role": "user", "content": body.message},
        {"role": "assistant", "content": reply},
    ])
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO sessions(id, messages, plan) VALUES (?, ?, ?)",
            (session["session_id"], json.dumps(session["messages"], ensure_ascii=False), json.dumps(session["plan"], ensure_ascii=False)),
        )
    return {"session_id": session["session_id"], "reply": reply, "plan": session["plan"]}


@app.get("/trips/{session_id}")
def get_trip(session_id: str):
    return get_session(session_id)


@app.post("/bookings", status_code=201)
def create_booking(body: BookingRequest):
    session = get_session(body.session_id)
    options = session["plan"]["options"]
    if not any(option["id"] == body.option_id for option in options):
        raise HTTPException(status_code=400, detail="Option does not belong to this trip")
    booking_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        db.execute(
            "INSERT INTO bookings(id, session_id, option_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (booking_id, body.session_id, body.option_id, "simulated", created_at),
        )
        session["plan"]["selected_option_id"] = body.option_id
        db.execute(
            "UPDATE sessions SET plan = ? WHERE id = ?",
            (json.dumps(session["plan"], ensure_ascii=False), body.session_id),
        )
    return {"booking_id": booking_id, "status": "simulated", "option_id": body.option_id, "created_at": created_at}
