"""
MetaReviewer Agent MCP Server
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from mcp_server.base_server import BaseMCPServer
from agents.meta_reviewer_agent import MetaReviewerAgent


def main():
    agent = MetaReviewerAgent()
    server = BaseMCPServer(
        agent=agent,
        agent_name="MetaReviewerAgent",
        port=5003
    )
    server.run()


if __name__ == "__main__":
    main()