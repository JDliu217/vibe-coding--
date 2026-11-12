import logging
import uuid

from fastapi import FastAPI, Request

logger = logging.getLogger("freshmart")


def install_trace(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        trace_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("trace=%s %s %s failed", trace_id, request.method, request.url.path)
            raise
        response.headers["x-request-id"] = trace_id
        logger.info("trace=%s %s %s -> %s", trace_id, request.method, request.url.path, response.status_code)
        return response
