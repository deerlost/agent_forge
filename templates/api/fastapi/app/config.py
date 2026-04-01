from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./app.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
