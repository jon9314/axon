from fastapi import FastAPI
from datetime import datetime, UTC
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
