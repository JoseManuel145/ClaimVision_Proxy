from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    BACKEND_TRANSACCIONAL_URL: str = "http://backend:8000"

    RATE_LIMIT_DEFAULT: str = "60/minute"

    ORIGINS: list[str] = ["*"]

    BLOCKED_IPS: list[str] = []
    MAX_REQUEST_SIZE_DEFAULT: int = 10_485_760
    MAX_REQUEST_SIZE_UPLOAD: int = 104_857_600
    UPLOAD_PATHS: list[str] = [
        "/api/v1/ia/predict",
        "/api/v1/ia/v2/predict",
        "/api/v1/ia/predict/v2",
        "/api/v1/ia/ocr",
        "/api/v1/ia/nlp/transcribir",
    ]

    ENVIRONMENT: str = "production"

    GATEWAY_INTERNAL_SECRET: str = ""

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = GatewaySettings()
