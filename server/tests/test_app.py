from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException

from earshot.app import create_app


def test_health_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok"}


def test_unknown_path_is_not_found_envelope() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "not_found"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]
    assert "detail" not in body


def test_wrong_method_is_method_not_allowed_envelope() -> None:
    client = TestClient(create_app())
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    body = response.json()
    assert body["error"]["code"] == "method_not_allowed"
    assert body["error"]["message"]
    assert "detail" not in body


def test_other_http_exception_is_http_error() -> None:
    app = create_app()

    @app.get("/api/v1/teapot")
    def teapot() -> None:
        raise HTTPException(status_code=418, detail="short and stout")

    response = TestClient(app).get("/api/v1/teapot")
    assert response.status_code == 418
    body = response.json()
    assert body["error"]["code"] == "http_error"
    assert "detail" not in body
