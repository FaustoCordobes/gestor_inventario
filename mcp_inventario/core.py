from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app import create_app

flask_app = create_app()

import os

host = os.getenv("MCP_PUBLIC_HOST", "")

mcp = FastMCP(
    "gestor-inventario",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", host],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", f"https://{host}"],
    ),
)
