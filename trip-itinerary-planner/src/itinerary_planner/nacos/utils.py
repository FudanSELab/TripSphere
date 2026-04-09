import socket
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from itinerary_planner.nacos.naming import NacosNaming


def get_local_ip() -> str:
    """Get the local IP address by connecting to a public endpoint."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return socket.gethostbyname(socket.gethostname())


async def client_shutdown(nacos_naming: "NacosNaming | None") -> None:
    """Shut down the Nacos naming client connection pool."""
    if nacos_naming is not None:
        await nacos_naming.shutdown()
