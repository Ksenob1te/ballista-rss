import json
import logging
import aio_pika
from .engine import rabbitmq_manager

logger = logging.getLogger("rabbit_module")

async def get_rabbit_connection() -> aio_pika.abc.AbstractRobustConnection:
    return rabbitmq_manager.get_connection()

async def subscribe_to_events(queue_name: str, callback):
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                async with message.process():
                    data = json.loads(message.body)
                    headers = dict(message.headers) if message.headers else {}
                    logger.info(f"Received message from {queue_name}: {data}, headers: {headers}")
                    # Pass both payload and headers to callback
                    await callback({"payload": data, "headers": headers})
            except Exception as e:
                logger.exception(f"Error processing message: {e}")

async def publish_event(queue_name: str, event: dict, headers: dict = None):
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    await channel.declare_queue(queue_name, durable=True)
    message = aio_pika.Message(
        body=json.dumps(event).encode(),
        headers=headers or {}
    )
    await channel.default_exchange.publish(
        message,
        routing_key=queue_name,
    )
    logger.info(f"Published event to {queue_name}: {event}, headers: {headers}")