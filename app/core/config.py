from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GCP_PROJECT_ID: str
    GCP_REGION: str
    LLM_MODEL_NAME: str
    APP_NAME: str = "Commercial Analyst AI"

    class Config:
        env_file = ".env"

settings = Settings()