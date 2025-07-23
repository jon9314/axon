from fastapi import FastAPI, HTTPException
import pydoc

app = FastAPI()

@app.get("/get")
def get_doc(topic: str):
    """Return documentation for a Python topic."""
    try:
        text = pydoc.render_doc(topic)
    except ImportError:
        raise HTTPException(status_code=404, detail="topic not found")
    return {"content": text}
