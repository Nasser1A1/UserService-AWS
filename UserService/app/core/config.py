from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "User Service"
    LOG_LEVEL: str = "INFO"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
