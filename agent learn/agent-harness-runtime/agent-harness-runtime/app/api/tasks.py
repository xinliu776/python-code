from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from app.schemas.task import (
    TaskCreateRequest
)

from app.core.database import (
    create_task,
    get_task
)

from app.core.runner import (
    AgentRunner
)

from app.core.run_manager import (
    run_manager
)
from app.core.run_manager import (
    run_manager,
    RunCapacityError
)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


runner = AgentRunner()


@router.post("")
def create_task_api(
    request: TaskCreateRequest
):

    task_id = create_task(
        objective=request.objective,
        max_steps=request.max_steps
    )

    return {
        "task_id": task_id,
        "status": "pending"
    }


@router.get("/{task_id}")
def get_task_api(
    task_id: int
):

    task = get_task(task_id)

    if not task:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@router.post(
    "/{task_id}/run",
    status_code=202
)
async def run_task_api(
    task_id: int
):

    if not run_manager.has_capacity():

        raise HTTPException(
            status_code=429,
            detail=(
                "Maximum concurrent "
                "run limit reached"
            )
        )

    try:

        state = (
            runner.prepare_task_run(
                task_id
            )
        )

        run_manager.start(
            state["run_id"],

            lambda:
                runner.execute_run(
                    **state
                )
        )

        return {
            "run_id":
                state["run_id"],

            "task_id":
                task_id,

            "status":
                "running"
        }

    except RunCapacityError as e:

        raise HTTPException(
            status_code=429,
            detail=str(e)
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )