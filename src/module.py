from src.rabbit_pool import subscribe_to_events, rabbitmq_manager
from fastapi import FastAPI, Response, Depends
from contextlib import asynccontextmanager
from .postgre import *
from .service import *
import asyncio
from .service.service import RSSService


async def rabbitmq_line():
    await rabbitmq_manager.connect()

    async def handle_event(message: dict):
        payload = message.get("payload", {})
        async for db_session in get_db_session():
            service = RSSService(db_session)
            await service.create_item(payload)

    try:
        await subscribe_to_events("ballista-rss", handle_event)
    finally:
        await rabbitmq_manager.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    task = asyncio.create_task(rabbitmq_line())  # фоновая подписка на RabbitMQ

    try:
        yield
    finally:
        task.cancel()
        await sessionmanager.close()

app = FastAPI(lifespan=lifespan)

@app.get("/rss/{league_id}", response_class=Response)
async def get_rss_feed(league_id: int, db_session=Depends(get_db_session)):
    service = RSSService(db_session)
    try:
        rss_xml = await service.generate_rss(league_id)
    except DatabaseException as e:
        return Response(content=str(e), status_code=404)
    except Exception as e:
        return Response(content=str(e), status_code=500)
    return Response(content=rss_xml, media_type="application/rss+xml")
