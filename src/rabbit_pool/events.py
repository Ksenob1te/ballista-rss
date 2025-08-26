import json
import logging
import aio_pika
import traceback
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
                    logger.info("Received message from %s: %s, headers: %s", queue_name, data, headers)
                    await callback({"payload": data, "headers": headers})
            except Exception as e:
                tb = traceback.format_exc()
                logger.error("Error processing message: %s\n%s", e, tb)

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
    logger.info("Published event to %s: %s, headers: %s", queue_name, event, headers)
