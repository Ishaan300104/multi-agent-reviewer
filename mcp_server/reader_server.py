"""
Reader Agent MCP Server
"""

import sys
sys.path.append('../agents')

from mcp_server.base_server import BaseMCPServer
from agents.reader_agent import ReaderAgent


def main():
    agent = ReaderAgent()
    server = BaseMCPServer(
        agent=agent,
        agent_name="ReaderAgent",
        port=5001
    )
    server.run()


if __name__ == "__main__":
    main()