from tripsphere_rca.faults.base import FaultInjector
from tripsphere_rca.faults.cpu import CpuInjector
from tripsphere_rca.faults.disk import DiskInjector
from tripsphere_rca.faults.memory import MemoryInjector
from tripsphere_rca.faults.socket import SocketInjector

INJECTORS = {
    "cpu": CpuInjector,
    "memory": MemoryInjector,
    "socket": SocketInjector,
    "disk": DiskInjector,
}


def create_injector(kind: str) -> FaultInjector:
    try:
        return INJECTORS[kind]()
    except KeyError as exc:
        raise ValueError(f"unsupported fault kind: {kind}") from exc
