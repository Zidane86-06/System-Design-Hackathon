import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SALESTORM High-Concurrency Flash Sale Platform"
    ENV: str = os.getenv("ENV", "development")
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./salestorm.db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() in ("true", "1", "yes")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    USE_KAFKA: bool = os.getenv("USE_KAFKA", "false").lower() in ("true", "1", "yes")
    
    # Reservation TTL
    RESERVATION_TTL_SECONDS: int = 30
    
    # Service Chaos Flags (can be toggled dynamically at runtime)
    ORDER_SERVICE_OUTAGE: bool = False
    PAYMENT_GATEWAY_DOWN: bool = False
    DATABASE_DOWN: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
