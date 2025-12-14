from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "InstaLite"
    secret_key: str = "CHANGE_ME"
    access_token_expire_minutes: int = 120
    database_url: str = "sqlite:///./app.db"
    frontend_origin: str = "http://localhost:5173"

settings = Settings()
