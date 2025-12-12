import uvicorn

from chat.asgi import app
from chat.config.logging import config_logging
from chat.config.settings import get_settings

if __name__ == "__main__":
    config_logging()
    server_settings = get_settings().server
    uvicorn.run(app, host=server_settings.host, port=server_settings.port)
