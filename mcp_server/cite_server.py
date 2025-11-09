"""
CiteAgent MCP Server
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from mcp_server.base_server import BaseMCPServer
from agents.cite_agent import CiteAgent


def main():
    agent = CiteAgent()
    server = BaseMCPServer(
        agent=agent,
        agent_name="CiteAgent",
        port=5004
    )
    server.run()


if __name__ == "__main__":
    main()