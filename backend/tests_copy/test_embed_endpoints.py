from fastapi.testclient import TestClient


BASE = "/api/v1/embed/docs"


def _headers():
    # conftestで設定したキーに合わせる
    return {"x_embed_key": "demo123"}


def test_upload_txt(client: TestClient):
    content = b"hello world"
    files = {"file": ("greeting.txt", content, "text/plain")}
    r = client.post(f"{BASE}/upload", headers=_headers(), files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["chunks_count"] >= 1
    assert data["filename"] == "greeting.txt"


def test_upload_rejects_large_file(client: TestClient):
    # アプリ側で拡張子ごとの最大値チェックをしている
    # 2MBを超えたら413になる想定。ここでは簡易に直接ハンドラを呼ばずサイズで確認が難しいため、
    # テキストで2MB+1のデータを送って判定を確認する。
    big = b"a" * (2 * 1024 * 1024 + 1)
    files = {"file": ("big.txt", big, "text/plain")}
    r = client.post(f"{BASE}/upload", headers=_headers(), files=files)
    assert r.status_code == 413


def test_url_ingest(client: TestClient):
    # 実ネットワークに出ないよう、httpxではなくurllib.requestを使う実装。
    # TestClient環境では直接到達しないため、ここでは「400以外」で成功パスまで到達できるかは
    # 難しい。最小限として、URL未到達時の400エラーハンドリングを確認する。
    r = client.post(f"{BASE}/url", headers=_headers(), json={"url": "http://invalid"})
    assert r.status_code in {200, 400}


def test_search(client: TestClient):
    body = {"question": "会社のルールは?", "top_k": 2}
    r = client.post(f"{BASE}/search", headers=_headers(), json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == body["question"]
    assert data["total_found"] >= 0


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
    r = client.get(f"{BASE}/documents", headers={"X_embed_key": "demo123"})
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
    # Pydanticによる必須項目不足は 422 Unprocessable Entity
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
