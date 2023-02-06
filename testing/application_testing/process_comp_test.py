import time

from src.core.core import KuiX

config_path = "/media/x/Projects/Dev Python/KuiX/testing/application_testing/config.json"
comp_path = "/media/x/Projects/Dev Python/KuiX/src/process_components/BaseProcessComponent.py"

# Instance the core
core = KuiX()
core.load_json_config(config_path)
core.start()

# Create a process
core.create_process("KXP")

time.sleep(1)

# Load the strategy
core.add_process_component("DebugProcessComponent", comp_path)

time.sleep(5)
core.ipc_server.close()