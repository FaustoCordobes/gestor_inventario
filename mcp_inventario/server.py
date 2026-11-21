import os

from mcp_inventario.core import mcp
from mcp_inventario.tools import dashboard, products, suppliers


def main():
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))
