import sys

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import (
    init_db,
    recover_interrupted_runs
)

from app.core.mcp_adapter import (
    MCPServerAdapter
)

from app.api.tasks import (
    router as tasks_router
)

from app.api.run import (
    router as runs_router
)

from app.core.tool_registry import (
    tool_registry
)

import app.tools.builtin
from app.core.config import settings

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    recover_interrupted_runs()

    app.state.mcp_servers = []

    if settings.enable_mcp:

        workspace_server = (
            MCPServerAdapter(
                name="workspace",

                command=sys.executable,

                args=[
                    str(
                        PROJECT_ROOT
                        / "mcp_servers"
                        / "workspace_server.py"
                    )
                ],

                cwd=str(
                    PROJECT_ROOT
                )
            )
        )

        await workspace_server.connect()

        app.state.mcp_servers.append(
            workspace_server
        )

    yield

    for server in (
        app.state.mcp_servers
    ):
        await server.close()

app = FastAPI(
    title=(
        "AI Agent Harness Runtime"
    ),
    version="0.2.0",
    lifespan=lifespan
)


app.include_router(
    tasks_router
)

app.include_router(
    runs_router
)


@app.get("/health")
def health():

    return {
        "status": "ok",
        "tools":
            tool_registry.list_tools()
    }