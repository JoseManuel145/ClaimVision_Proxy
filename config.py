from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    BACKEND_TRANSACCIONAL_URL: str = "http://backend-transaccional:8000"

    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    ORIGINS: list[str] = ["*"]

    BLOCKED_IPS: list[str] = []
    MAX_REQUEST_SIZE: int = 10_485_760

    ENVIRONMENT: str = "production"

    GATEWAY_INTERNAL_SECRET: str = ""

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = GatewaySettings()
