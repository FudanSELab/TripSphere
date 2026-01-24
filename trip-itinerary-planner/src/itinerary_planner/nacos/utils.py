import socket
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from itinerary_planner.nacos.ai import NacosAI
    from itinerary_planner.nacos.naming import NacosNaming


def get_local_ip() -> str:
    """Get local IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return socket.gethostbyname(socket.gethostname())


async def client_shutdown(
    nacos_ai: "NacosAI | None", nacos_naming: "NacosNaming | None"
) -> None:
    if nacos_ai is not None:
        await nacos_ai.shutdown()
        return  # Return early to avoid double shutdown
    if nacos_naming is not None:
        await nacos_naming.shutdown()
