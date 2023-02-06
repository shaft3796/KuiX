from src.core.Logger import LOGGER
from src.core_components.BaseCoreComponent import BaseCoreComponent


class MyComponent(BaseCoreComponent):

    def __init__(self, core):
        super().__init__(core)
        self._name = "MyComponent"
        self._version = "0.0.1"
        self._author = "KuiX"
        self._description = "MyComponent"

    def __open__(self):
        # Let's add an endpoint to print something received from a worker
        def callback(identifier, data):
            LOGGER.info(f"CORE PROCESS: received log from worker {data['worker']}: {data['message']}", "CORE")

        self.core.add_endpoint("log", callback)
