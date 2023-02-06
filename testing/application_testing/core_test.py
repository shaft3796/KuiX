import time

from src.core.core import KuiX
from src.core.Logger import LOGGER

LOGGER.enable_verbose()


core = KuiX()
# core.generate_json_config()
core.load_json_config()
core.start()


core.create_process_and_wait("KXP 1")
core.create_worker("KXP 1", "DebugStrategy", "WORKER 1")
core.start_worker("KXP 1", "WORKER 1")
time.sleep(5)
time.sleep(2)
print("Stopping worker 1...")
core.stop_worker("KXP 1", "WORKER 1")
time.sleep(2)
print("destroying worker 1...")
core.close_worker("KXP 1", "WORKER 1")
core.close_process("KXP 1")
core.ipc_server.close()

