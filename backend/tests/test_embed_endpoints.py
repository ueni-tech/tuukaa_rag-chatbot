from fastapi.testclient import TestClient

BASE = "/api/v1/embed/docs"


def _headers():
    return {"x-embed-key": "demo123"}


def test_upload_txt(client: TestClient):
    content = b"hello world"
    files = {"file": ("greeting.txt", content, "text/plain")}
    r = client.post(f"{BASE}/upload", headers=_headers(), files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["chunks_count"] >= 1
    assert data["filename"] == "greeting.txt"


def test_upload_rejects_large_files(client: TestClient):
    big = b"a" * (2 * 1024 * 1024 + 1)
    files = {"file": ("big.txt", big, "text/plain")}
    r = client.post(f"{BASE}/upload", headers=_headers(), files=files)
    assert r.status_code == 413


def test_url_ingest_success(client: TestClient):
    r = client.post(
        f"{BASE}/url", headers=_headers(), json={"url": "https://www.google.com/"}
    )
    assert r.status_code == 200


def test_url_ingest_failed(client: TestClient):
    r = client.post(f"{BASE}/url", headers=_headers(), json={"url": "http://invalid"})
    assert r.status_code == 400


def test_search(client: TestClient):
    body = {"question": "会社のルールは?", "top_k": 2}
    r = client.post(f"{BASE}/search", headers=_headers(), json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == body["question"]
    assert data["total_found"] >= 0


def test_search_requires_top_k(client: TestClient):
    body = {"question": "会社のルールは?", "top_k": 0}
    r = client.post(f"{BASE}/search", json=body)
    assert r.status_code == 422


def test_search_requires_embed_key(client: TestClient):
    body = {"question": "会社のルールは?", "top_k": 2}
    r = client.post(f"{BASE}/search", json=body)
    assert r.status_code == 401


def test_ask(client: TestClient):
    body = {"question": "勤怠の申請方法は?", "top_k": 2}
    r = client.post(f"{BASE}/ask", headers=_headers(), json=body)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["question"] == body["question"]
    assert "documents" in data


def test_documents_list(client: TestClient):
    r = client.get(f"{BASE}/documents", headers=_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["total_files"] >= 0


def test_documents_delete_requires_fields(client: TestClient):
    r = client.request(
        "DELETE",
        f"{BASE}/documents",
        headers=_headers(),
        json={"filename": "sample.txt"},
    )
    assert r.status_code == 422


def test_documents_delete_success(client: TestClient):
    body = {"filename": "sample.txt", "file_id": "file-1"}
    r = client.request("DELETE", f"{BASE}/documents", headers=_headers(), json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"


def test_system_info(client: TestClient):
    r = client.get(f"{BASE}/system/info")
    assert r.status_code == 200
    data = r.json()
    assert data["vectorstore_ready"] in {True, False}


def test_system_reset(client: TestClient):
    r = client.post(f"{BASE}/system/reset")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
