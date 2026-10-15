from tripsphere_rca.faults import create_injector
from tripsphere_rca.faults.cpu import CpuInjector
from tripsphere_rca.faults.disk import DiskInjector
from tripsphere_rca.faults.memory import MemoryInjector
from tripsphere_rca.faults.socket import SocketInjector


def test_all_migrated_faults_are_registered():
    assert isinstance(create_injector("cpu"), CpuInjector)
    assert isinstance(create_injector("memory"), MemoryInjector)
    assert isinstance(create_injector("socket"), SocketInjector)
    assert isinstance(create_injector("disk"), DiskInjector)
