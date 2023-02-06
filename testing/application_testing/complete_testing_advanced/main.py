import time

from src.core.core import KuiX
from MyComponent import MyComponent

config_path = "/media/x/Projects/Dev Python/KuiX/testing/application_testing/config.json"
strategy_path = "/media/x/Projects/Dev Python/KuiX/testing/application_testing/complete_testing_advanced/MyStrategy.py"

# Instance the core
core = KuiX()
core.load_json_config(config_path)
core.start()

# Load the component
core.add_component("main", MyComponent(core))
core.open_component("main")

# Create a process
core.create_process_and_wait("KXP")
# Load the strategy
core.add_strategy("MyStrategy", strategy_path)
# Create a new worker
core.create_worker("KXP", "MyStrategy", "my_strategy")
# Start the worker
core.start_worker("my_strategy")

time.sleep(5)

core.close()
