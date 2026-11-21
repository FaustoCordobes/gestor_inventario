import os

from mcp_inventario.core import mcp
from mcp_inventario.tools import products


def main():
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))
