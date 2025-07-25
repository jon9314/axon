from datetime import datetime

from fastapi import FastAPI

try:  # Python 3.11+
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - for Python <3.11
    UTC = UTC
import time

app = FastAPI()


@app.get("/now")
def get_now():
    return {"timestamp": datetime.now(UTC).isoformat()}


@app.get("/timezone")
def get_timezone():
    return {"timezone": time.tzname[0]}


@app.get("/duration")
def duration_between(start: float, end: float):
    return {"seconds": end - start}
