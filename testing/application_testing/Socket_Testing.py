from src.core.Logger import LOGGER
from src.core.network.SocketClient import SocketClient
from src.core.network.SocketServer import SocketServer

LOGGER.enable_verbose()

# --- Test IPC server ---

# Create a server
server = SocketServer("key")

# Start the server
server.accept_new_connections()

# --- Test IPC client ---

# Create a client
client = SocketClient("CLI1", "key")

# Connect to the server
client.connect()

#  --- MSG SENDING ---
server.send_data("CLI1", {"content": "Hello client!"})
client.send_data({"content": "Hello server!"})

# --- Closing ---
server.close()
client.close()


