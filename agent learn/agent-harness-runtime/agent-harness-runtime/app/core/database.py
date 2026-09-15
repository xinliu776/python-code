import sqlite3
import json
from pathlib import Path
from datetime import datetime

from app.core.config import settings


def now():
    return datetime.now().isoformat()


def get_connection():
    path = Path(settings.database_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(
        path,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        objective TEXT NOT NULL,
        status TEXT NOT NULL,
        max_steps INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        current_step INTEGER NOT NULL DEFAULT 0,
        messages_json TEXT NOT NULL,
        final_answer TEXT,
        error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        step_no INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )
    """)

    conn.commit()
    conn.close()


def create_task(
    objective: str,
    max_steps: int
):

    conn = get_connection()
    cursor = conn.cursor()

    time = now()

    cursor.execute(
        """
        INSERT INTO tasks (
            objective,
            status,
            max_steps,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            objective,
            "pending",
            max_steps,
            time,
            time
        )
    )

    task_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return task_id


def get_task(task_id: int):

    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def update_task_status(
    task_id: int,
    status: str
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE tasks
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            now(),
            task_id
        )
    )

    conn.commit()
    conn.close()


def create_run(
    task_id: int,
    messages: list
):

    conn = get_connection()
    cursor = conn.cursor()

    time = now()

    cursor.execute(
        """
        INSERT INTO runs (
            task_id,
            status,
            current_step,
            messages_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            "running",
            0,
            json.dumps(
                messages,
                ensure_ascii=False
            ),
            time,
            time
        )
    )

    run_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return run_id


def update_run(
    run_id: int,
    *,
    status: str,
    current_step: int,
    messages: list,
    final_answer=None,
    error=None
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE runs
        SET
            status = ?,
            current_step = ?,
            messages_json = ?,
            final_answer = ?,
            error = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            current_step,
            json.dumps(
                messages,
                ensure_ascii=False
            ),
            final_answer,
            error,
            now(),
            run_id
        )
    )

    conn.commit()
    conn.close()


def add_event(
    run_id: int,
    step_no: int,
    event_type: str,
    payload
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO events (
            run_id,
            step_no,
            event_type,
            payload_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            run_id,
            step_no,
            event_type,
            json.dumps(
                payload,
                ensure_ascii=False
            ),
            now()
        )
    )

    conn.commit()
    conn.close()


def get_events(run_id: int):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT * FROM events
        WHERE run_id = ?
        ORDER BY id ASC
        """,
        (run_id,)
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]

def get_run(run_id: int):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM runs
        WHERE id = ?
        """,
        (run_id,)
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def recover_interrupted_runs():
    """
    服务如果运行到一半突然关闭，
    数据库中的 running 状态说明任务被中断。
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, task_id
        FROM runs
        WHERE status = 'running'
        """
    ).fetchall()

    for row in rows:

        conn.execute(
            """
            UPDATE runs
            SET
                status = 'paused',
                error = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                "Runtime interrupted. "
                "Run can be resumed.",
                now(),
                row["id"]
            )
        )

        conn.execute(
            """
            UPDATE tasks
            SET
                status = 'paused',
                updated_at = ?
            WHERE id = ?
            """,
            (
                now(),
                row["task_id"]
            )
        )

    conn.commit()
    conn.close()

def get_events_after(
    run_id: int,
    after_id: int = 0
):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM events
        WHERE run_id = ?
        AND id > ?
        ORDER BY id ASC
        """,
        (
            run_id,
            after_id
        )
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]