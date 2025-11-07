import os
import sys
from typing import NoReturn

from litestar.cli.main import litestar_group

from chat.config.settings import get_settings


def setup_environment() -> None:
    """
    Configure the environment variables and path.
    """
    settings = get_settings()
    os.environ.setdefault("LITESTAR_APP", "chat.asgi:create_app")
    os.environ.setdefault("LITESTAR_APP_NAME", settings.app.name)


def run_cli() -> NoReturn:
    """
    Application Entrypoint.

    Sets up the environment and runs the Litestar CLI.

    Returns:
        NoReturn: It either runs the CLI or exits the program.

    Raises:
        SystemExit: If there's an error loading required libraries.
    """
    setup_environment()

    try:
        settings = get_settings()
        sys.exit(
            litestar_group(  # pyright: ignore
                args=[
                    "run",
                    "--host",
                    settings.server.host,
                    "--port",
                    str(settings.server.port),
                ],
            )
        )
    except ImportError as exc:
        print(
            "Could not load required libraries.",
            "Please check your installation and "
            "make sure you activated any necessary virtual environment.",
        )
        print(exc)
        sys.exit(1)
