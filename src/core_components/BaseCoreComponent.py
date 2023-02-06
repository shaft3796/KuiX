from src.core.Logger import LOGGER, CORE_COMP
from src.core.Utils import Respond


class BaseCoreComponent:

    # Constructor of the component
    def __init__(self, core):
        """
        Instance the component.
        :param core: The KuiX instance
        """
        self.core = core

    # --- Core ---
    def __open__(self):
        """
        To override, called only once to open the component.
        """
        pass

    def __start__(self):
        """
        To override, called to start the component.
        """
        pass

    def __stop__(self):
        """
        To override, called to stop the component.
        """
        pass

    def __close__(self):
        """
        To override, called only once to close the component.
        """
        pass


class DebugCoreComponent(BaseCoreComponent):

    # Constructor for the component
    def __init__(self, core):
        super().__init__(core)
        LOGGER.info("DebugCoreComponent created.", CORE_COMP)

    def __open__(self):
        LOGGER.info("DebugCoreComponent opened.", CORE_COMP)

        # We add a blocking endpoint to print something from the core
        @Respond("debug_call")
        def callback(rid, data):
            LOGGER.info("DebugCoreComponent debug call.", CORE_COMP)
            return {"status": "success", "return": "Debug call success !"}

        self.core.add_blocking_endpoint("debug_call", callback)

    def __start__(self):
        LOGGER.info("DebugCoreComponent started.", CORE_COMP)

    def __stop__(self):
        LOGGER.info("DebugCoreComponent stopped.", CORE_COMP)

    def __close__(self):
        LOGGER.info("DebugCoreComponent closed.", CORE_COMP)

