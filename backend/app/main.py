from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .db import Base, engine
from .core.config import settings
from .mqtt.paho_adapter import MosquittoTelemetrySubscriber

app = FastAPI(title="Aquaculture AIoT Backend", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
mqtt_subscriber = MosquittoTelemetrySubscriber()


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    mqtt_subscriber.start()


@app.get("/health")
def health():
    return {"status": "ok", "mode": "MOCK_BACKEND"}
