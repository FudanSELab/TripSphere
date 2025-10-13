import abc
from abc import ABC, abstractmethod

class ConnectionEventListener(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    async def on_connected(self) -> None: ...
    @abstractmethod
    async def on_disconnect(self) -> None: ...
