import logging
import uvicorn
from src import env
from src.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
logger.info("Starting uvicorn server on %s:%s", env.server.host, env.server.port)

if __name__ == '__main__':
    uvicorn.run("src.module:app", host=env.server.host, port=env.server.port, reload=False, log_config=None)
