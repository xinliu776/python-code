from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):

    objective: str = Field(
        min_length=1,
        max_length=5000
    )

    max_steps: int = Field(
        default=10,
        ge=1,
        le=100
    )


class ResumeRunRequest(BaseModel):

    additional_steps: int = Field(
        default=10,
        ge=1,
        le=100
    )