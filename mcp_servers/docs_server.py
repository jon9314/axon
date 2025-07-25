import pydoc

from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/get")
def get_doc(topic: str):
    """Return documentation for a Python topic."""
    try:
        text = pydoc.render_doc(topic)
    except ImportError as err:
        raise HTTPException(status_code=404, detail="topic not found") from err
    return {"content": text}
