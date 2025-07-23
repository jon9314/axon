from fastapi import FastAPI, HTTPException
from pathlib import Path
import subprocess

app = FastAPI()

@app.get("/list")
def list_repo(repo_path: str):
    repo_dir = Path(repo_path)
    if not repo_dir.is_dir():
        raise HTTPException(status_code=400, detail="invalid repo path")
    try:
        result = subprocess.check_output(["git", "-C", str(repo_dir), "ls-files"], text=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=e.stderr)
    files = result.strip().splitlines()
    return {"files": files}

@app.get("/read")
def read_file(repo_path: str, file: str):
    repo_dir = Path(repo_path)
    target = repo_dir / file
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()
    return {"content": content}
