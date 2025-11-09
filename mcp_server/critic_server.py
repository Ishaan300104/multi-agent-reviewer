"""
Critic Agent MCP Server
"""

import sys
# sys.path.append('../agents')
sys.path.append('C:\\Users\\uvisy\\Desktop\\multi-agent-reviewer\\agents')


from mcp_server.base_server import BaseMCPServer
from agents.critic_agent import CriticAgent


def main():
    agent = CriticAgent()
    server = BaseMCPServer(
        agent=agent,
        agent_name="CriticAgent",
        port=5002
    )
    server.run()


if __name__ == "__main__":
    main()