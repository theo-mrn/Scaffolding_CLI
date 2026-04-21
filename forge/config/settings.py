from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FORGE_",
        env_file=".env",
        extra="ignore",
        frozen=False,
    )

    github_token: str = ""
    github_org: str = ""
    default_branch: str = "main"


settings = Settings()
