import inspect

from src.strategies.BaseStrategy import BaseStrategy, DebugStrategy


def get_builtin_types():
    """
    Return a list of couple (name, path) of the built in types (strategies).
    :return: A list of couple (name, path)
    """
    return [("BaseStrategy", inspect.getfile(BaseStrategy)),
            ("DebugStrategy", inspect.getfile(DebugStrategy))]

