from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # PostgreSQL
    postgres_user: str = "quant"
    postgres_password: str = ""
    postgres_db: str = "quant_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Trading Safety
    trading_mode: str = "paper"  # paper | live

    # Broker
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_no: str = ""

    # AI
    anthropic_api_key: str = ""

    # Notifications
    slack_webhook_url: str = ""

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_live(self) -> bool:
        return self.trading_mode == "live"


settings = Settings()
