import aio_pika
from aio_pika.abc import AbstractRobustConnection
from .. import env

class RabbitMQSessionManager:
    def __init__(self, url: str):
        self._url = url
        self._connection: AbstractRobustConnection | None = None

    async def connect(self):
        if self._connection is None:
            self._connection = await aio_pika.connect_robust(self._url)

    async def close(self):
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def reopen(self):
        if self._connection is None:
            self._connection = await aio_pika.connect_robust(self._url)

    def get_connection(self) -> AbstractRobustConnection:
        if self._connection is None:
            raise RuntimeError("RabbitMQ connection is not initialized. Call connect() first.")
        return self._connection

rabbitmq_manager = RabbitMQSessionManager(env.rabbit.url)

