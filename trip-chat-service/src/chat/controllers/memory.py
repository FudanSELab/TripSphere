from litestar import Controller


class MemoryController(Controller):
    path = "/memories"
    tags = ["Memories"]
