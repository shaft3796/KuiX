from src.core.Logger import LOGGER
from src.core.ipc.IpcServer import IpcServer
from src.core.ipc.IpcClient import IpcClient
from src.core.event import CoreEvent

LOGGER.enable_verbose()

# --- Test IPC server ---

# Create a server
server = IpcServer("key")


# Subscribe to connection accept event
def broadcast(identifier):
    print("Connection accepted from " + identifier)

def cbroadcast(identifier, from_server):
    print("Connection closed from " + identifier, "from server: " + str(from_server))


server.event_handler.subscribe(CoreEvent.SOCKET_CONNECTION_ACCEPTED, broadcast)
server.event_handler.subscribe(CoreEvent.SOCKET_CONNECTION_CLOSED, cbroadcast)

server.accept_new_connections()

# --- Test IPC client ---

# Create a client
client = IpcClient("CLI1", "key")

server.close()
