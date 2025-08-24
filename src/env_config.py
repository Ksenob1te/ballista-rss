from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class LocalSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")


# class RedisConfig(LocalSettings):
#     host: str = Field(default="localhost", alias="REDIS_HOST")
#     port: int = Field(default="6379", alias="REDIS_PORT")
#     user: str = Field(default="default", alias="REDIS_USER")
#     password: str = Field(alias="REDIS_PASSWORD")
#
#     @property
#     def url(self) -> str:
#         return f"redis://{self.user}:{self.password}@{self.host}:{self.port}"


# class AIConfig(LocalSettings):
#     openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
#     chutes_api_key: str = Field(alias="CHUTES_API_KEY")
#     groq_api_key: str = Field(alias="GROQ_API_KEY")
#     google_api_key: str = Field(alias="GOOGLE_API_KEY")
#     result_expire: int = Field(default=86400, alias="DEEPSEEK_REDIS_EXPIRE")
#     g4f_host: str = Field(default="localhost", alias="G4F_HOST")


class RabbitConfig(LocalSettings):
    host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    port: int = Field(default=5672, alias="RABBITMQ_PORT")
    user: str = Field(default="guest", alias="RABBITMQ_USER")
    password: str = Field(default="guest", alias="RABBITMQ_PASSWORD")
    vhost: str = Field(default="/", alias="RABBITMQ_VHOST")

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}{self.vhost}"


class PostgresConfig(LocalSettings):
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default="5432", alias="POSTGRES_PORT")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    db: str = Field(default="ballista-rss", alias="POSTGRES_DB")

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

class ServerConfig(LocalSettings):
    host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    port: int = Field(default=8000, alias="SERVER_PORT")


class Env(LocalSettings):
    rabbit: RabbitConfig = Field(default_factory=RabbitConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    @classmethod
    def load(cls) -> "Env":
        return cls()


env = Env.load()
