import asyncio
import copy
import json

from openai import OpenAI

from app.core.config import settings
from app.core.tool_registry import tool_registry

from app.core.database import (
    get_task,
    get_run,
    create_run,
    update_run,
    update_task_status,
    add_event
)





SYSTEM_PROMPT = """
你是运行在 AI Agent Harness Runtime 中的自主执行 Agent。

你的目标不是简单聊天，而是持续执行用户任务，
直到整体任务真正完成。

规则：

1. 根据目标自主决定下一步行动。
2. 需要外部能力时使用工具。
3. 工具执行结果会返回给你，你需要根据结果继续行动。
4. 工具失败后分析原因，可以重试、修改参数或选择其他工具。
5. 不要因为一个中间步骤完成就停止。
6. 不要重复执行已经成功完成的动作。
7. 当整体任务真正完成以后，输出最终结果。
"""


class AgentRunner:

    def __init__(self):

        self.registry = (
            tool_registry
        )

        self._client = None

    def _get_client(self):

        if self._client is None:

            if not settings.llm_api_key:

                raise RuntimeError(
                    "LLM_API_KEY "
                    "is not configured"
                )

            self._client = OpenAI(
                api_key=
                    settings.llm_api_key,

                base_url=
                    settings.llm_base_url
            )

        return self._client    

    async def _call_llm(
        self,
        messages
    ):

        client = (
            self._get_client()
        )

        return await asyncio.to_thread(
            client.chat.completions.create,

            model=
                settings.llm_model,

            messages=
                messages,

            tools=
                self.registry.schemas()
        )

    def prepare_task_run(
        self,
        task_id: int
    ):

        task = get_task(task_id)

        if not task:
            raise ValueError(
                "Task not found"
            )

        if task["status"] == "running":
            raise ValueError(
                "Task is already running"
            )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": task["objective"]
            }
        ]

        run_id = create_run(
            task_id,
            messages
        )

        update_task_status(
            task_id,
            "running"
        )

        return {
            "run_id": run_id,
            "task": task,
            "messages": messages,
            "start_step": 1,
            "step_budget":
                task["max_steps"]
        }

    def prepare_resume_run(
        self,
        run_id: int,
        additional_steps: int
    ):

        run = get_run(run_id)

        if not run:
            raise ValueError(
                "Run not found"
            )

        if run["status"] == "completed":
            raise ValueError(
                "Completed run cannot be resumed"
            )

        if run["status"] == "running":
            raise ValueError(
                "Run is already running"
            )

        task = get_task(
            run["task_id"]
        )

        if not task:
            raise ValueError(
                "Task not found"
            )

        messages = json.loads(
            run["messages_json"]
        )

        update_run(
            run_id,
            status="running",
            current_step=run["current_step"],
            messages=messages
        )

        update_task_status(
            task["id"],
            "running"
        )

        return {
            "run_id": run_id,
            "task": task,
            "messages": messages,
            "start_step":
                run["current_step"] + 1,
            "step_budget":
                additional_steps
        }

    async def execute_run(
        self,
        *,
        run_id: int,
        task: dict,
        messages: list,
        start_step: int,
        step_budget: int
    ):

        # Safe checkpoint
        # 只保存完整执行成功的消息历史

        safe_messages = copy.deepcopy(
            messages
        )

        safe_step = start_step - 1

        try:

            for step in range(
                start_step,
                start_step + step_budget
            ):

                add_event(
                    run_id,
                    step,
                    "llm_request",
                    {
                        "message_count":
                            len(messages)
                    }
                )

                response = (
                    await self._call_llm(
                        messages
                    )
                )

                message = (
                    response
                    .choices[0]
                    .message
                )

                tool_calls = (
                    message.tool_calls or []
                )

                # ====================
                # Agent 调用工具
                # ====================

                if tool_calls:

                    assistant_message = {
                        "role": "assistant",
                        "content":
                            message.content or "",
                        "tool_calls": []
                    }

                    for tool_call in tool_calls:

                        assistant_message[
                            "tool_calls"
                        ].append({
                            "id":
                                tool_call.id,

                            "type":
                                "function",

                            "function": {
                                "name":
                                    tool_call
                                    .function
                                    .name,

                                "arguments":
                                    tool_call
                                    .function
                                    .arguments
                            }
                        })

                    messages.append(
                        assistant_message
                    )

                    for tool_call in tool_calls:

                        tool_name = (
                            tool_call
                            .function
                            .name
                        )

                        arguments = (
                            tool_call
                            .function
                            .arguments
                        )

                        add_event(
                            run_id,
                            step,
                            "tool_call",
                            {
                                "tool":
                                    tool_name,

                                "arguments":
                                    arguments
                            }
                        )

                        result = (
                            await self.registry
                            .execute(
                                tool_name,
                                arguments
                            )
                        )

                        messages.append({
                            "role": "tool",

                            "tool_call_id":
                                tool_call.id,

                            "content":
                                json.dumps(
                                    result,
                                    ensure_ascii=False
                                )
                        })

                        add_event(
                            run_id,
                            step,
                            "tool_result",
                            {
                                "tool":
                                    tool_name,
                                **result
                            }
                        )

                    # 这一轮已经完整完成
                    # 此时才更新 safe checkpoint

                    safe_messages = (
                        copy.deepcopy(
                            messages
                        )
                    )

                    safe_step = step

                    update_run(
                        run_id,
                        status="running",
                        current_step=step,
                        messages=safe_messages
                    )

                    continue

                # ====================
                # Agent 判断任务完成
                # ====================

                final_answer = (
                    message.content or ""
                )

                messages.append({
                    "role": "assistant",
                    "content":
                        final_answer
                })

                add_event(
                    run_id,
                    step,
                    "completed",
                    {
                        "answer":
                            final_answer
                    }
                )

                update_run(
                    run_id,
                    status="completed",
                    current_step=step,
                    messages=messages,
                    final_answer=
                        final_answer
                )

                update_task_status(
                    task["id"],
                    "completed"
                )

                return {
                    "run_id": run_id,
                    "status":
                        "completed",
                    "current_step":
                        step,
                    "answer":
                        final_answer
                }

            # ====================
            # Step Budget 用完
            # ====================

            update_run(
                run_id,
                status="paused",
                current_step=
                    safe_step,
                messages=
                    safe_messages
            )

            update_task_status(
                task["id"],
                "paused"
            )

            add_event(
                run_id,
                safe_step,
                "paused",
                {
                    "reason":
                        "step budget exhausted"
                }
            )

            return {
                "run_id":
                    run_id,
                "status":
                    "paused",
                "current_step":
                    safe_step,
                "reason":
                    "step budget exhausted"
            }

        # ========================
        # 用户主动 Cancel
        # ========================

        except asyncio.CancelledError:

            update_run(
                run_id,
                status="cancelled",
                current_step=
                    safe_step,
                messages=
                    safe_messages,
                error=
                    "Run cancelled by user"
            )

            update_task_status(
                task["id"],
                "cancelled"
            )

            add_event(
                run_id,
                safe_step,
                "cancelled",
                {
                    "reason":
                        "cancelled by user"
                }
            )

            raise

        # ========================
        # Runtime Exception
        # ========================

        except Exception as e:

            update_run(
                run_id,
                status="failed",
                current_step=
                    safe_step,
                messages=
                    safe_messages,
                error=str(e)
            )

            update_task_status(
                task["id"],
                "failed"
            )

            add_event(
                run_id,
                safe_step,
                "runtime_error",
                {
                    "error":
                        str(e)
                }
            )

            raise