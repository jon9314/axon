from fastapi import FastAPI, HTTPException
import os
import requests

app = FastAPI()

@app.get("/query")
def query(expression: str):
    """Query the WolframAlpha API and return the plaintext result."""
    app_id = os.environ.get("WOLFRAM_APP_ID")
    if not app_id:
        raise HTTPException(status_code=500, detail="WOLFRAM_APP_ID not set")
    resp = requests.get(
        "https://api.wolframalpha.com/v2/query",
        params={"input": expression, "appid": app_id, "output": "json"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    pods = data.get("queryresult", {}).get("pods", [])
    for pod in pods:
        if pod.get("primary") or pod.get("id") == "Result":
            subpods = pod.get("subpods", [])
            if subpods:
                text = subpods[0].get("plaintext")
                if text:
                    return {"result": text}
    for pod in pods:
        subpods = pod.get("subpods", [])
        if subpods:
            text = subpods[0].get("plaintext")
            if text:
                return {"result": text}
    raise HTTPException(status_code=400, detail="no result")
