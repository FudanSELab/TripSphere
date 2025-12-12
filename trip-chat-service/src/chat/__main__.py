import uvicorn

from chat.asgi import app
from chat.config.logging import configure_logging
from chat.config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    configure_logging()
    uvicorn.run(app, host=settings.server.host, port=settings.server.port)
