from src.core.Logger import LOGGER
from src.core.process.KxProcess import __launch__

LOGGER.enable_verbose()

__launch__("CLI1", "test", "127.0.0.1", 60000, 0.1)
