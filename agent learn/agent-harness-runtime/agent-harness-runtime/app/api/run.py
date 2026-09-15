from fastapi import (
    APIRouter,
    HTTPException
)

from app.schemas.task import (
    ResumeRunRequest
)

from app.core.database import (
    get_run,
    get_events
)

from app.core.runner import (
    AgentRunner
)

from app.core.run_manager import (
    run_manager
)
import asyncio
import json

from fastapi.responses import (
    StreamingResponse
)

from app.core.database import (
    get_run,
    get_events,
    get_events_after
)

router = APIRouter(
    prefix="/runs",
    tags=["Runs"]
)


runner = AgentRunner()


@router.get("/{run_id}")
def get_run_api(
    run_id: int
):

    run = get_run(run_id)

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Run not found"
        )

    return run


@router.get("/{run_id}/events")
def get_run_events(
    run_id: int
):

    return get_events(run_id)


@router.post(
    "/{run_id}/resume",
    status_code=202
)
async def resume_run_api(
    run_id: int,
    request: ResumeRunRequest
):

    try:

        state = (
            runner.prepare_resume_run(
                run_id=run_id,
                additional_steps=
                    request.additional_steps
            )
        )

        run_manager.start(
            run_id,

            runner.execute_run(
                **state
            )
        )

        return {
            "run_id":
                run_id,
            "status":
                "running"
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post(
    "/{run_id}/cancel"
)
async def cancel_run_api(
    run_id: int
):

    run = get_run(run_id)

    if not run:

        raise HTTPException(
            status_code=404,
            detail="Run not found"
        )

    if run["status"] != "running":

        raise HTTPException(
            status_code=400,
            detail=(
                f"Run status is "
                f"{run['status']}"
            )
        )

    cancelled = (
        run_manager.cancel(
            run_id
        )
    )

    if not cancelled:

        raise HTTPException(
            status_code=409,
            detail=(
                "Run is not active "
                "in current runtime"
            )
        )

    return {
        "run_id":
            run_id,
        "status":
            "cancelling"
    }

@router.get(
    "/{run_id}/stream"
)
async def stream_run_events(
    run_id: int,
    after_id: int = 0
):

    run = get_run(run_id)

    if not run:

        raise HTTPException(
            status_code=404,
            detail="Run not found"
        )

    async def event_generator():

        last_event_id = (
            after_id
        )

        terminal_statuses = {
            "completed",
            "failed",
            "paused",
            "cancelled"
        }

        while True:

            events = (
                get_events_after(
                    run_id,
                    last_event_id
                )
            )

            for event in events:

                last_event_id = (
                    event["id"]
                )

                payload_json = (
                    event[
                        "payload_json"
                    ]
                )

                if payload_json:

                    try:
                        payload = (
                            json.loads(
                                payload_json
                            )
                        )

                    except Exception:
                        payload = (
                            payload_json
                        )

                else:
                    payload = None

                data = {
                    "id":
                        event["id"],

                    "run_id":
                        run_id,

                    "step":
                        event[
                            "step_no"
                        ],

                    "type":
                        event[
                            "event_type"
                        ],

                    "payload":
                        payload,

                    "created_at":
                        event[
                            "created_at"
                        ]
                }

                yield (
                    f"id: {event['id']}\n"
                    f"event: "
                    f"{event['event_type']}\n"
                    f"data: "
                    f"{json.dumps(data, ensure_ascii=False)}\n\n"
                )

            current_run = (
                get_run(run_id)
            )

            if (
                current_run
                and
                current_run[
                    "status"
                ]
                in terminal_statuses
            ):

                # 确保数据库最后几个 event
                # 已经发送出去

                final_events = (
                    get_events_after(
                        run_id,
                        last_event_id
                    )
                )

                for event in final_events:

                    data = {
                        "id":
                            event["id"],

                        "run_id":
                            run_id,

                        "step":
                            event[
                                "step_no"
                            ],

                        "type":
                            event[
                                "event_type"
                            ]
                    }

                    yield (
                        f"id: {event['id']}\n"
                        f"event: "
                        f"{event['event_type']}\n"
                        f"data: "
                        f"{json.dumps(data, ensure_ascii=False)}\n\n"
                    )

                break

            await asyncio.sleep(
                0.5
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":
                "no-cache",

            "Connection":
                "keep-alive"
        }
    )