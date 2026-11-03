from pathlib import Path

from tripsphere_rca.cli import load_case
from tripsphere_rca.faults.disk import DiskInjector
from tripsphere_rca.faults.socket import SocketInjector


class DummyProcess:
    pass


def test_socket_injector_uses_predeployed_target_helper(monkeypatch):
    spec = Path(__file__).parents[1] / "configs" / "cases" / "socket" / "chat.toml"
    case = load_case(spec)
    commands = []

    def capture_command(command, **kwargs):
        commands.append(command)
        return DummyProcess()

    monkeypatch.setattr("tripsphere_rca.faults.socket.subprocess.Popen", capture_command)

    result = SocketInjector().start(case)

    assert commands[0] == [
        "docker", "exec", "tripsphere-fault-tools-socket-chat", "stress-ng",
        "--sock", "8", "--timeout", "300s", "--metrics-brief",
    ]
    assert result.mode == "predeployed_tool_container"


def test_disk_injector_uses_predeployed_tool_and_mounted_volume(monkeypatch):
    spec = Path(__file__).parents[1] / "configs" / "cases" / "disk" / "postgres.toml"
    case = load_case(spec)
    commands = []

    def capture_command(command, **kwargs):
        commands.append(command)
        return DummyProcess()

    monkeypatch.setattr("tripsphere_rca.faults.disk.subprocess.Popen", capture_command)

    result = DiskInjector().start(case)

    assert commands[0][:4] == [
        "docker", "exec", "tripsphere-fault-tools", "fio",
    ]
    assert "--filename=/volumes/postgres/.tripsphere-disk-stress-TS-RCA-DISK-IO-POSTGRES-postgres.bin" in commands[0]
    assert "--runtime=300s" in commands[0]
    assert "apk" not in " ".join(commands[0])
    assert result.mode == "predeployed_tool_container"
