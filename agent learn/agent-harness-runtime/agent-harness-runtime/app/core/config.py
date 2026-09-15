from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):

    llm_api_key: str = ""

    llm_base_url: str = (
        "https://api.deepseek.com"
    )

    llm_model: str = "deepseek-chat"

    database_path: str = (
        "data/agent_harness.db"
    )

    max_concurrent_runs: int = 3

    enable_mcp: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()