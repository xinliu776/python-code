import asyncio
from collections.abc import (
    Awaitable,
    Callable
)

from app.core.config import settings


class RunCapacityError(
    RuntimeError
):
    pass


class RunManager:

    def __init__(
        self,
        max_concurrent_runs: int
    ):
        self.max_concurrent_runs = (
            max_concurrent_runs
        )

        self._tasks: dict[
            int,
            asyncio.Task
        ] = {}

    @property
    def active_count(self):

        return len(
            self._tasks
        )

    def has_capacity(self):

        return (
            self.active_count
            <
            self.max_concurrent_runs
        )

    async def _execute(
        self,
        run_id: int,
        coroutine_factory:
            Callable[
                [],
                Awaitable
            ]
    ):

        await coroutine_factory()

    def start(
        self,
        run_id: int,
        coroutine_factory:
            Callable[
                [],
                Awaitable
            ]
    ):

        old_task = (
            self._tasks.get(
                run_id
            )
        )

        if (
            old_task
            and
            not old_task.done()
        ):
            raise ValueError(
                f"Run {run_id} "
                "is already running"
            )

        if not self.has_capacity():

            raise RunCapacityError(
                "Maximum concurrent "
                "run limit reached"
            )

        task = asyncio.create_task(
            self._execute(
                run_id,
                coroutine_factory
            ),
            name=(
                f"agent-run-{run_id}"
            )
        )

        self._tasks[
            run_id
        ] = task

        task.add_done_callback(
            lambda _:
                self._tasks.pop(
                    run_id,
                    None
                )
        )

    def cancel(
        self,
        run_id: int
    ):

        task = (
            self._tasks.get(
                run_id
            )
        )

        if (
            not task
            or task.done()
        ):
            return False

        task.cancel()

        return True

    def is_active(
        self,
        run_id: int
    ):

        task = (
            self._tasks.get(
                run_id
            )
        )

        return bool(
            task
            and
            not task.done()
        )


run_manager = RunManager(
    max_concurrent_runs=
        settings.max_concurrent_runs
)