from fastapi import FastAPI, HTTPException
import math

app = FastAPI()

@app.get("/evaluate")
def evaluate(expr: str):
    try:
        # WARNING: eval is used for simplicity; avoid in production
        result = eval(expr, {"__builtins__": {}}, math.__dict__)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"result": result}

@app.get("/percent")
def percent(value: float, percent: float):
    return {"result": value * percent / 100.0}
