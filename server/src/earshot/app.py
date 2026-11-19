from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

ERROR_CODES: dict[int, str] = {
    HTTPStatus.NOT_FOUND: "not_found",
    HTTPStatus.METHOD_NOT_ALLOWED: "method_not_allowed",
}


async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        raise exc
    body = {
        "error": {
            "code": ERROR_CODES.get(exc.status_code, "http_error"),
            "message": exc.detail or HTTPStatus(exc.status_code).phrase,
        }
    }
    return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(HTTPException, http_error_handler)

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
