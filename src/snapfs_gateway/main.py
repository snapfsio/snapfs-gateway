#!/usr/bin/env python3
#
# Copyright (c) 2025 SnapFS, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uvicorn
from fastapi import FastAPI

from .api import cache, ingest, query, stream
from .bus import bus
from .config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="SnapFS Gateway",
        version="0.1.8",
    )

    @app.on_event("startup")
    async def startup():
        await bus.connect()

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok", "env": settings.env}

    app.include_router(cache.router)
    app.include_router(ingest.router)
    app.include_router(query.router)
    app.include_router(stream.router)

    return app


app = create_app()


def main():
    uvicorn.run(
        "snapfs_gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
