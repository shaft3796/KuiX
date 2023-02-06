import time

from src.strategies.BaseStrategy import DebugStrategy

strat = DebugStrategy("test")
strat.__open__()
strat.__start__()
time.sleep(5)
strat.__stop__()
strat.__close__()
