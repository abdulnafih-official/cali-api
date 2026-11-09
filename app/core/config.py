from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    hf_repo_id: str
    hf_filename: str = "model.joblib"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

# role -> (requests per minute, lifetime total requests; None = unlimited)
ROLE_LIMITS: dict[str, tuple[int, int | None]] = {
    "free": (10, 1_000),
    "premium": (60, 50_000),
    "admin": (600, None),
}