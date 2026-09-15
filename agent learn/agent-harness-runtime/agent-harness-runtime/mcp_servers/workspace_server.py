from pathlib import Path

from mcp.server import MCPServer


mcp = MCPServer(
    "Harness Workspace"
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

WORKSPACE = (
    PROJECT_ROOT
    / "workspace"
)

WORKSPACE.mkdir(
    parents=True,
    exist_ok=True
)


def safe_path(
    relative_path: str
):

    path = (
        WORKSPACE
        / relative_path
    ).resolve()

    if (
        path != WORKSPACE
        and
        WORKSPACE not in path.parents
    ):
        raise ValueError(
            "Access outside workspace "
            "is not allowed"
        )

    return path


@mcp.tool()
def list_files(
    path: str = "."
) -> list[str]:
    """
    列出 workspace 中的文件。
    """

    target = safe_path(path)

    if not target.exists():
        raise ValueError(
            "Path does not exist"
        )

    if not target.is_dir():
        raise ValueError(
            "Path is not directory"
        )

    return [
        str(
            item.relative_to(
                WORKSPACE
            )
        )
        for item in target.iterdir()
    ]


@mcp.tool()
def read_text_file(
    path: str
) -> str:
    """
    读取 workspace 中的文本文件。
    """

    target = safe_path(path)

    if not target.exists():
        raise ValueError(
            "File does not exist"
        )

    return target.read_text(
        encoding="utf-8"
    )


@mcp.tool()
def write_text_file(
    path: str,
    content: str
) -> dict:
    """
    在 workspace 中创建或覆盖文本文件。
    """

    target = safe_path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        content,
        encoding="utf-8"
    )

    return {
        "path": str(
            target.relative_to(
                WORKSPACE
            )
        ),
        "characters":
            len(content)
    }


if __name__ == "__main__":
    mcp.run()