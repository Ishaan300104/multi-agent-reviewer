"""
Orchestrator: Manages workflow between agents using LangGraph
"""

import uuid
from datetime import datetime
from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

from reader_agent import ReaderAgent
from critic_agent import CriticAgent
from meta_reviewer_agent import MetaReviewerAgent
from cite_agent import CiteAgent


class ReviewState(TypedDict):
    """State passed between agents in the workflow."""
    # Input
    paper_source: str
    source_type: str
    session_id: str
    
    # Agent outputs
    paper_content: Dict[str, Any]
    critic_analysis: Dict[str, Any]
    citation_data: Dict[str, Any]
    final_review: Dict[str, Any]
    
    # Metadata
    errors: Annotated[list, operator.add]
    stage: str
    start_time: str
    tool_calls: int


class ResearchReviewOrchestrator:
    """
    Orchestrates the multi-agent research paper review workflow.
    """
    
    def __init__(self):
        # Initialize agents
        self.reader_agent = ReaderAgent()
        self.critic_agent = CriticAgent()
        self.meta_reviewer_agent = MetaReviewerAgent()
        self.cite_agent = CiteAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ReviewState)
        
        # Add nodes (agent functions)
        workflow.add_node("extract", self.extract_paper)
        workflow.add_node("analyze", self.analyze_paper)
        workflow.add_node("find_citations", self.find_citations)
        workflow.add_node("generate_review", self.generate_review)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("extract")
        workflow.add_edge("extract", "analyze")
        workflow.add_edge("analyze", "find_citations")
        workflow.add_edge("find_citations", "generate_review")
        workflow.add_edge("generate_review", END)
        
        return workflow
    
    def extract_paper(self, state: ReviewState) -> ReviewState:
        """Node: Extract paper content using Reader Agent."""
        print(f"[{datetime.now()}] Stage: Extracting paper content...")
        
        state["stage"] = "extraction"
        state["tool_calls"] = state.get("tool_calls", 0) + 1
        
        try:
            message = {
                "message_id": str(uuid.uuid4()),
                "sender": "orchestrator",
                "receiver": "ReaderAgent",
                "timestamp": datetime.now().isoformat(),
                "message_type": "request",
                "payload": {
                    "action": "extract_paper",
                    "data": {
                        "source": state["paper_source"],
                        "source_type": state.get("source_type", "pdf")
                    }
                },
                "context": {
                    "session_id": state.get("session_id")
                }
            }
            
            response = self.reader_agent.process_message(message)
            
            if response["message_type"] == "response":
                state["paper_content"] = response["payload"]["data"]
                print(f"✓ Extracted: {state['paper_content'].get('title', 'Unknown')}")
            else:
                error_msg = f"Reader Agent error: {response['payload'].get('error')}"
                state["errors"] = state.get("errors", []) + [error_msg]
                print(f"✗ {error_msg}")
                
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            state["errors"] = state.get("errors", []) + [error_msg]
            print(f"✗ {error_msg}")
        
        return state
    
    def analyze_paper(self, state: ReviewState) -> ReviewState:
        """Node: Analyze paper using Critic Agent."""
        print(f"[{datetime.now()}] Stage: Analyzing paper quality...")
        
        state["stage"] = "analysis"
        state["tool_calls"] = state.get("tool_calls", 0) + 1
        
        try:
            message = {
                "message_id": str(uuid.uuid4()),
                "sender": "orchestrator",
                "receiver": "CriticAgent",
                "timestamp": datetime.now().isoformat(),
                "message_type": "request",
                "payload": {
                    "action": "analyze_paper",
                    "data": {
                        "paper_content": state.get("paper_content", {})
                    }
                },
                "context": {
                    "session_id": state.get("session_id")
                }
            }
            
            response = self.critic_agent.process_message(message)
            
            if response["message_type"] == "response":
                state["critic_analysis"] = response["payload"]["data"]
                overall = state["critic_analysis"].get("overall_score", 0)
                print(f"✓ Analysis complete: Overall score {overall:.1f}/10")
            else:
                error_msg = f"Critic Agent error: {response['payload'].get('error')}"
                state["errors"] = state.get("errors", []) + [error_msg]
                print(f"✗ {error_msg}")
                
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            state["errors"] = state.get("errors", []) + [error_msg]
            print(f"✗ {error_msg}")
        
        return state
    
    def find_citations(self, state: ReviewState) -> ReviewState:
        """Node: Find related papers using CiteAgent."""
        print(f"[{datetime.now()}] Stage: Finding related papers...")
        
        state["stage"] = "citation_analysis"
        state["tool_calls"] = state.get("tool_calls", 0) + 1
        
        try:
            message = {
                "message_id": str(uuid.uuid4()),
                "sender": "orchestrator",
                "receiver": "CiteAgent",
                "timestamp": datetime.now().isoformat(),
                "message_type": "request",
                "payload": {
                    "action": "analyze_citations",
                    "data": {
                        "paper_content": state.get("paper_content", {}),
                        "max_related": 10
                    }
                },
                "context": {
                    "session_id": state.get("session_id")
                }
            }
            
            response = self.cite_agent.process_message(message)
            
            if response["message_type"] == "response":
                state["citation_data"] = response["payload"]["data"]
                related_count = len(state["citation_data"].get("related_papers", []))
                print(f"✓ Found {related_count} related papers")
            else:
                error_msg = f"CiteAgent error: {response['payload'].get('error')}"
                state["errors"] = state.get("errors", []) + [error_msg]
                print(f"⚠ {error_msg} (continuing with limited data)")
                state["citation_data"] = {}  # Continue without citation data
                
        except Exception as e:
            error_msg = f"Citation analysis failed: {str(e)}"
            state["errors"] = state.get("errors", []) + [error_msg]
            print(f"⚠ {error_msg} (continuing with limited data)")
            state["citation_data"] = {}
        
        return state
    
    def generate_review(self, state: ReviewState) -> ReviewState:
        """Node: Generate final review using MetaReviewer Agent."""
        print(f"[{datetime.now()}] Stage: Generating final review...")
        
        state["stage"] = "review_generation"
        state["tool_calls"] = state.get("tool_calls", 0) + 1
        
        try:
            message = {
                "message_id": str(uuid.uuid4()),
                "sender": "orchestrator",
                "receiver": "MetaReviewerAgent",
                "timestamp": datetime.now().isoformat(),
                "message_type": "request",
                "payload": {
                    "action": "generate_review",
                    "data": {
                        "paper_content": state.get("paper_content", {}),
                        "critic_analysis": state.get("critic_analysis", {}),
                        "citation_data": state.get("citation_data")
                    }
                },
                "context": {
                    "session_id": state.get("session_id")
                }
            }
            
            response = self.meta_reviewer_agent.process_message(message)
            
            if response["message_type"] == "response":
                state["final_review"] = response["payload"]["data"]
                print(f"✓ Review generated successfully")
            else:
                error_msg = f"MetaReviewer error: {response['payload'].get('error')}"
                state["errors"] = state.get("errors", []) + [error_msg]
                print(f"✗ {error_msg}")
                
        except Exception as e:
            error_msg = f"Review generation failed: {str(e)}"
            state["errors"] = state.get("errors", []) + [error_msg]
            print(f"✗ {error_msg}")
        
        return state
    
    def review_paper(self, paper_source: str, source_type: str = "pdf") -> Dict[str, Any]:
        """
        Main entry point for paper review workflow.
        
        Args:
            paper_source: Path to PDF or ArXiv ID
            source_type: Type of source ('pdf' or 'arxiv_id')
            
        Returns:
            Complete review results
        """
        session_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"Starting paper review - Session: {session_id}")
        print(f"Source: {paper_source}")
        print(f"{'='*60}\n")
        
        # Initialize state
        initial_state = ReviewState(
            paper_source=paper_source,
            source_type=source_type,
            session_id=session_id,
            paper_content={},
            critic_analysis={},
            citation_data={},
            final_review={},
            errors=[],
            stage="initialized",
            start_time=start_time.isoformat(),
            tool_calls=0
        )
        
        # Run workflow
        try:
            config = {"configurable": {"thread_id": session_id}}
            final_state = self.app.invoke(initial_state, config)
            
            # Calculate metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = {
                "session_id": session_id,
                "paper_content": final_state.get("paper_content", {}),
                "critic_analysis": final_state.get("critic_analysis", {}),
                "citation_data": final_state.get("citation_data", {}),
                "final_review": final_state.get("final_review", {}),
                "metadata": {
                    "processing_time_seconds": processing_time,
                    "tool_calls": final_state.get("tool_calls", 0),
                    "errors": final_state.get("errors", []),
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            }
            
            print(f"\n{'='*60}")
            print(f"✓ Review completed in {processing_time:.2f} seconds")
            print(f"Tool calls: {result['metadata']['tool_calls']}")
            print(f"Errors: {len(result['metadata']['errors'])}")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"\n✗ Workflow failed: {str(e)}\n")
            return {
                "session_id": session_id,
                "error": str(e),
                "metadata": {
                    "processing_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "failed": True
                }
            }


if __name__ == "__main__":
    # Test orchestrator
    orchestrator = ResearchReviewOrchestrator()
    
    # Example usage
    result = orchestrator.review_paper(
        paper_source="data/sample_papers/sample.pdf",
        source_type="pdf"
    )
    
    if "final_review" in result:
        print("\n=== Final Review ===")
        print(result["final_review"].get("executive_summary", "No summary available"))