import os

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app import create_app
from mcp_inventario.auth import StaticTokenVerifier

flask_app = create_app()

host = os.getenv("MCP_PUBLIC_HOST") or os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
token = os.getenv("MCP_TOKEN")
remote = os.getenv("MCP_TRANSPORT", "stdio") != "stdio"

if remote and not token:
    raise RuntimeError("Falta la variable de entorno MCP_TOKEN: el servidor MCP no puede publicarse sin clave.")

auth_options = {}
if remote:
    public_url = f"https://{host}" if host else "http://localhost"
    auth_options = {
        "token_verifier": StaticTokenVerifier(token),
        "auth": AuthSettings(
            issuer_url=public_url,
            resource_server_url=public_url,
            validate_token_resource=False,
        ),
    }

mcp = FastMCP(
    "gestor-inventario",
    host="0.0.0.0" if remote else "127.0.0.1",
    port=int(os.getenv("PORT", "8000")),
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", host],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", f"https://{host}"],
    ),
    **auth_options,
)
