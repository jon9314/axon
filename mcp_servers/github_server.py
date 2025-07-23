from fastapi import FastAPI, HTTPException
from fastapi import Body
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
    except subprocess.CalledProcessError as err:
        raise HTTPException(status_code=400, detail=err.stderr) from err
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


@app.post("/write")
def write_file(
    repo_path: str,
    file: str,
    message: str = "update",
    content: str = Body("", embed=True),
):
    repo_dir = Path(repo_path)
    target = repo_dir / file
    if not repo_dir.is_dir():
        raise HTTPException(status_code=400, detail="invalid repo path")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "-C", str(repo_dir), "add", file], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "commit", "-m", message], check=True)
    except subprocess.CalledProcessError as err:
        raise HTTPException(status_code=400, detail=err.stderr) from err
    return {"status": "ok"}
