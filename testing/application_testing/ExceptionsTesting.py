import json

from src.core.Exceptions import *
from src.core.Logger import LOGGER


class Test:
    pass

try:
    # raise SocketClientSendError().add_ctx("Une exception !")
    raise GenericException()
except Exception as e:
    _e = GenericException(e)
    LOGGER.error_exception(_e, "CORE")
