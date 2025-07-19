from fastapi import FastAPI, Body
import os

app = FastAPI()

@app.get("/list")
def list_files(path: str = "."):
    return {"files": os.listdir(path)}

@app.get("/read")
def read_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.post("/write")
def write_file(path: str, content: str = Body("", embed=True)):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"status": "ok"}

@app.get("/exists")
def exists(path: str):
    return {"exists": os.path.exists(path)}
