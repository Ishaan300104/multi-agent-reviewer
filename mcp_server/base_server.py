"""
Base MCP Server: Foundation for agent MCP servers
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid


class BaseMCPServer:
    """
    Base class for MCP servers that wrap agents.
    """
    
    def __init__(self, agent, agent_name: str, port: int):
        self.agent = agent
        self.agent_name = agent_name
        self.port = port
        self.app = FastAPI(title=f"{agent_name} MCP Server")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Active connections
        self.active_connections = []
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "server": self.agent_name,
                "status": "running",
                "version": "1.0.0",
                "protocol": "MCP",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "connections": len(self.active_connections),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/process")
        async def process(message: dict):
            """HTTP endpoint for processing messages."""
            try:
                response = self.agent.process_message(message)
                return response
            except Exception as e:
                return {
                    "message_type": "error",
                    "payload": {"error": str(e)},
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await self.handle_websocket(websocket)
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        print(f"[{self.agent_name}] New connection. Total: {len(self.active_connections)}")
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                print(f"[{self.agent_name}] Received: {message.get('payload', {}).get('action')}")
                
                # Process message
                response = self.agent.process_message(message)
                
                # Send response
                await websocket.send_text(json.dumps(response))
                
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)
            print(f"[{self.agent_name}] Connection closed. Total: {len(self.active_connections)}")
        except Exception as e:
            print(f"[{self.agent_name}] Error: {str(e)}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"[{self.agent_name}] Broadcast error: {str(e)}")
    
    def run(self):
        """Run the MCP server."""
        print(f"Starting {self.agent_name} MCP Server on port {self.port}")
        print(f"HTTP: http://localhost:{self.port}")
        print(f"WebSocket: ws://localhost:{self.port}/ws")
        
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )


class MCPMessage:
    """Helper class for creating standardized MCP messages."""
    
    @staticmethod
    def create_request(sender: str, receiver: str, action: str, 
                      data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a request message."""
        return {
            "message_id": str(uuid.uuid4()),
            "sender": sender,
            "receiver": receiver,
            "timestamp": datetime.now().isoformat(),
            "message_type": "request",
            "payload": {
                "action": action,
                "data": data
            },
            "context": context or {}
        }
    
    @staticmethod
    def create_response(original_message: Dict[str, Any], 
                       sender: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a response message."""
        return {
            "message_id": str(uuid.uuid4()),
            "sender": sender,
            "receiver": original_message.get("sender"),
            "timestamp": datetime.now().isoformat(),
            "message_type": "response",
            "payload": {
                "action": original_message.get("payload", {}).get("action"),
                "data": data
            },
            "context": original_message.get("context", {})
        }
    
    @staticmethod
    def create_error(original_message: Dict[str, Any],
                    sender: str, error: str) -> Dict[str, Any]:
        """Create an error message."""
        return {
            "message_id": str(uuid.uuid4()),
            "sender": sender,
            "receiver": original_message.get("sender"),
            "timestamp": datetime.now().isoformat(),
            "message_type": "error",
            "payload": {
                "error": error,
                "action": original_message.get("payload", {}).get("action")
            },
            "context": original_message.get("context", {})
        }


if __name__ == "__main__":
    # Example usage
    class DummyAgent:
        def process_message(self, message):
            return {"message_type": "response", "payload": {"data": "test"}}
    
    server = BaseMCPServer(DummyAgent(), "TestAgent", 5000)
    server.run()