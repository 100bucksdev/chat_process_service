from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.model import load_model
from routers.pattern import pattern_router


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.model = load_model()
        yield



    app = FastAPI(lifespan=lifespan)

    @app.exception_handler(Exception)
    async def _unhandled_exc_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "internal error"})

    app.include_router(pattern_router, prefix="/pattern")
    return app

app = create_app()





if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8004)