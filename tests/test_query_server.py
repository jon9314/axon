from fastapi.testclient import TestClient
from mcp_servers.query_server import app

client = TestClient(app)


def test_query_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    resp = client.post(
        "/query",
        params={"path": str(csv_file)},
        json={"sql": "SELECT SUM(CAST(a AS INTEGER)) FROM data"},
    )
    assert resp.status_code == 200
    assert resp.json()["rows"][0][0] == 4
