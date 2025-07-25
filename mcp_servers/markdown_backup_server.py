import os

from fastapi import Body, FastAPI, HTTPException

BASE_DIR = "markdown_notes"
app = FastAPI()

os.makedirs(BASE_DIR, exist_ok=True)


@app.post("/save")
def save_note(name: str, content: str = Body("", embed=True)):
    path = os.path.join(BASE_DIR, f"{name}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"status": "ok"}


@app.get("/get")
def get_note(name: str):
    path = os.path.join(BASE_DIR, f"{name}.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="not found")
    with open(path, encoding="utf-8") as f:
        return {"content": f.read()}


@app.get("/search")
def search_notes(query: str):
    results = []
    for fname in os.listdir(BASE_DIR):
        if fname.endswith(".md"):
            with open(os.path.join(BASE_DIR, fname), encoding="utf-8") as f:
                text = f.read()
                if query.lower() in text.lower():
                    results.append(fname[:-3])
    return {"matches": results}
