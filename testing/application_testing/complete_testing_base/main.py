import time

from src.core.core import KuiX

config_path = "/media/x/Projects/Dev Python/KuiX/testing/application_testing/config.json"
strategy_path = "/media/x/Projects/Dev Python/KuiX/testing/application_testing/complete_testing_base/MyStrategy.py"

# Instance the core
core = KuiX()
core.load_json_config(config_path)
core.start()

# Create a process
core.create_process("KXP")

time.sleep(1)

# Load the strategy
core.add_strategy("MyStrategy", strategy_path)

# Create a new worker
core.create_worker("KXP", "MyStrategy", "my_strategy")

# Start the worker
core.start_worker("KXP", "my_strategy")

time.sleep(5)

# Stop the worker
core.stop_worker("KXP", "my_strategy")

# Close the worker
core.close_worker("KXP", "my_strategy")

# Close the process
core.close_process("KXP")
time.sleep(5)
core.ipc_server.close()