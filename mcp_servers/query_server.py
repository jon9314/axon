import csv
import io
import os
import sqlite3

from fastapi import Body, FastAPI, HTTPException

app = FastAPI()


def run_query(csv_path: str, sql: str):
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="csv not found")
    with open(csv_path, encoding="utf-8") as f:
        content = f.read()
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    reader = csv.reader(io.StringIO(content))
    try:
        headers = next(reader)
    except StopIteration:
        return []
    cur.execute("CREATE TABLE data (" + ", ".join(f"{h} TEXT" for h in headers) + ")")
    cur.executemany(
        "INSERT INTO data VALUES (" + ",".join("?" for _ in headers) + ")",
        list(reader),
    )
    try:
        cur.execute(sql)
    except sqlite3.Error as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    rows = cur.fetchall()
    return rows


@app.post("/query")
def query(path: str, sql: str = Body("", embed=True)):
    rows = run_query(path, sql)
    return {"rows": rows}
