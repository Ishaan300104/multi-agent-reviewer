"""
Critic Agent: Analyzes paper quality and provides critical feedback
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
import re
from collections import Counter


class CriticAgent:
    """
    Agent responsible for critical analysis of research papers.
    Evaluates methodology, clarity, novelty, and identifies weaknesses.
    """
    
    def __init__(self, agent_id: str = None, llm_client=None):
        self.agent_id = agent_id or f"critic-{uuid.uuid4().hex[:8]}"
        self.name = "CriticAgent"
        self.llm_client = llm_client
        
    def analyze_paper(self, paper_content: Dict[str, Any], 
                     focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Perform critical analysis of paper.
        
        Args:
            paper_content: Structured paper content from Reader Agent
            focus_areas: Specific areas to focus on
            
        Returns:
            Critical analysis with scores and recommendations
        """
        if focus_areas is None:
            focus_areas = ["methodology", "clarity", "novelty", "reproducibility"]
        
        analysis = {
            "overall_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "detailed_scores": {},
            "recommendations": [],
            "methodology_analysis": {},
            "clarity_metrics": {}
        }
        
        # Perform different analyses
        analysis["detailed_scores"]["novelty"] = self._assess_novelty(paper_content)
        analysis["detailed_scores"]["methodology"] = self._assess_methodology(paper_content)
        analysis["detailed_scores"]["clarity"] = self._assess_clarity(paper_content)
        analysis["detailed_scores"]["reproducibility"] = self._assess_reproducibility(paper_content)
        
        # Calculate overall score
        scores = list(analysis["detailed_scores"].values())
        analysis["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        
        # Identify strengths and weaknesses
        analysis["strengths"] = self._identify_strengths(paper_content, analysis["detailed_scores"])
        analysis["weaknesses"] = self._identify_weaknesses(paper_content, analysis["detailed_scores"])
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(
            paper_content, 
            analysis["weaknesses"]
        )
        
        # Detailed methodology analysis
        analysis["methodology_analysis"] = self._analyze_methodology_details(paper_content)
        
        # Clarity metrics
        analysis["clarity_metrics"] = self._compute_clarity_metrics(paper_content)
        
        return analysis
    
    def _assess_novelty(self, paper_content: Dict[str, Any]) -> float:
        """Assess the novelty of the research."""
        score = 5.0  # Base score
        
        abstract = paper_content.get("abstract", "")
        title = paper_content.get("title", "")
        
        # Check for novelty indicators
        novelty_keywords = [
            "novel", "new", "first", "innovative", "breakthrough",
            "unprecedented", "unique", "original"
        ]
        
        text = f"{title} {abstract}".lower()
        novelty_count = sum(1 for kw in novelty_keywords if kw in text)
        
        # Increase score based on novelty indicators
        score += min(novelty_count * 0.5, 3.0)
        
        return min(score, 10.0)
    
    def _assess_methodology(self, paper_content: Dict[str, Any]) -> float:
        """Assess research methodology quality."""
        score = 5.0
        
        sections = paper_content.get("sections", [])
        
        # Check for methodology-related sections
        has_methodology = any(
            "method" in s.get("heading", "").lower() or
            "approach" in s.get("heading", "").lower() or
            "experiment" in s.get("heading", "").lower()
            for s in sections
        )
        
        if has_methodology:
            score += 2.0
        
        # Check for statistical analysis mentions
        all_text = " ".join([s.get("content", "") for s in sections]).lower()
        
        methodology_indicators = [
            "baseline", "benchmark", "evaluation", "metrics",
            "dataset", "validation", "cross-validation"
        ]
        
        indicator_count = sum(1 for ind in methodology_indicators if ind in all_text)
        score += min(indicator_count * 0.3, 2.0)
        
        return min(score, 10.0)
    
    def _assess_clarity(self, paper_content: Dict[str, Any]) -> float:
        """Assess paper clarity and readability."""
        score = 5.0
        
        abstract = paper_content.get("abstract", "")
        sections = paper_content.get("sections", [])
        
        # Check abstract length (should be substantial but not too long)
        abstract_words = len(abstract.split())
        if 100 <= abstract_words <= 300:
            score += 1.5
        
        # Check section structure
        if len(sections) >= 4:  # Good structure
            score += 1.5
        
        # Check for clear section headings
        standard_sections = [
            "introduction", "method", "result", "conclusion", "discussion"
        ]
        
        section_headings = [s.get("heading", "").lower() for s in sections]
        standard_count = sum(
            1 for std in standard_sections 
            if any(std in heading for heading in section_headings)
        )
        
        score += min(standard_count * 0.4, 2.0)
        
        return min(score, 10.0)
    
    def _assess_reproducibility(self, paper_content: Dict[str, Any]) -> float:
        """Assess reproducibility of the research."""
        score = 4.0
        
        all_text = " ".join([
            s.get("content", "") 
            for s in paper_content.get("sections", [])
        ]).lower()
        
        # Check for reproducibility indicators
        reproducibility_keywords = [
            "code", "github", "implementation", "hyperparameter",
            "dataset", "open source", "available", "repository"
        ]
        
        repro_count = sum(1 for kw in reproducibility_keywords if kw in all_text)
        score += min(repro_count * 0.5, 4.0)
        
        # Check for detailed methodology
        detail_keywords = [
            "architecture", "configuration", "parameter", "setting"
        ]
        
        detail_count = sum(1 for kw in detail_keywords if kw in all_text)
        score += min(detail_count * 0.3, 2.0)
        
        return min(score, 10.0)
    
    def _identify_strengths(self, paper_content: Dict[str, Any], 
                           scores: Dict[str, float]) -> List[str]:
        """Identify paper strengths based on analysis."""
        strengths = []
        
        # High scoring areas
        for category, score in scores.items():
            if score >= 7.5:
                strengths.append(f"Strong {category}: well-executed and clearly presented")
        
        # Specific strengths
        if len(paper_content.get("references", [])) > 30:
            strengths.append("Comprehensive literature review with extensive citations")
        
        if len(paper_content.get("sections", [])) > 6:
            strengths.append("Well-structured paper with detailed sections")
        
        abstract = paper_content.get("abstract", "")
        if len(abstract.split()) > 150:
            strengths.append("Detailed abstract providing good overview")
        
        return strengths if strengths else ["Clear research question"]
    
    def _identify_weaknesses(self, paper_content: Dict[str, Any],
                            scores: Dict[str, float]) -> List[str]:
        """Identify paper weaknesses."""
        weaknesses = []
        
        # Low scoring areas
        for category, score in scores.items():
            if score < 5.0:
                weaknesses.append(f"Weak {category}: needs improvement")
        
        # Specific weaknesses
        if len(paper_content.get("references", [])) < 10:
            weaknesses.append("Limited references - needs more literature review")
        
        sections = paper_content.get("sections", [])
        if len(sections) < 4:
            weaknesses.append("Limited section structure - could be more detailed")
        
        # Check for missing important sections
        section_headings = [s.get("heading", "").lower() for s in sections]
        if not any("result" in h for h in section_headings):
            weaknesses.append("No clear results section identified")
        
        return weaknesses if weaknesses else ["Minor presentation improvements needed"]
    
    def _generate_recommendations(self, paper_content: Dict[str, Any],
                                 weaknesses: List[str]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if "literature review" in str(weaknesses).lower():
            recommendations.append("Expand literature review to include more recent work")
        
        if "result" in str(weaknesses).lower():
            recommendations.append("Add dedicated results section with clear presentation")
        
        if "reproducibility" in str(weaknesses).lower():
            recommendations.append("Include implementation details and code availability")
        
        if not recommendations:
            recommendations.append("Consider adding more ablation studies")
            recommendations.append("Expand discussion of limitations")
        
        return recommendations
    
    def _analyze_methodology_details(self, paper_content: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed methodology analysis."""
        sections = paper_content.get("sections", [])
        method_sections = [
            s for s in sections 
            if "method" in s.get("heading", "").lower()
        ]
        
        return {
            "has_methodology_section": len(method_sections) > 0,
            "methodology_length": sum(len(s.get("content", "")) for s in method_sections),
            "experimental_design": "present" if method_sections else "unclear"
        }
    
    def _compute_clarity_metrics(self, paper_content: Dict[str, Any]) -> Dict[str, Any]:
        """Compute quantitative clarity metrics."""
        abstract = paper_content.get("abstract", "")
        
        return {
            "abstract_length": len(abstract.split()),
            "section_count": len(paper_content.get("sections", [])),
            "reference_count": len(paper_content.get("references", [])),
            "has_clear_structure": len(paper_content.get("sections", [])) >= 4
        }
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming MCP message."""
        action = message.get("payload", {}).get("action")
        data = message.get("payload", {}).get("data", {})
        
        if action == "analyze_paper":
            paper_content = data.get("paper_content", {})
            focus_areas = data.get("focus_areas")
            
            try:
                analysis = self.analyze_paper(paper_content, focus_areas)
                
                return {
                    "message_id": str(uuid.uuid4()),
                    "sender": self.name,
                    "receiver": message.get("sender"),
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "response",
                    "payload": {
                        "action": "analyze_paper",
                        "data": analysis
                    },
                    "context": message.get("context", {})
                }
            except Exception as e:
                return {
                    "message_id": str(uuid.uuid4()),
                    "sender": self.name,
                    "receiver": message.get("sender"),
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "error",
                    "payload": {
                        "error": str(e),
                        "action": action
                    },
                    "context": message.get("context", {})
                }
        
        return {
            "message_type": "error",
            "payload": {"error": f"Unknown action: {action}"}
        }


if __name__ == "__main__":
    # Test the agent
    agent = CriticAgent()
    
    test_paper = {
        "title": "A Novel Approach to Deep Learning",
        "abstract": "This paper presents a novel approach to deep learning that improves performance...",
        "sections": [
            {"heading": "Introduction", "content": "Deep learning has..."},
            {"heading": "Methodology", "content": "Our approach uses..."},
            {"heading": "Results", "content": "We achieved..."},
            {"heading": "Conclusion", "content": "In conclusion..."}
        ],
        "references": ["Ref " + str(i) for i in range(25)]
    }
    
    analysis = agent.analyze_paper(test_paper)
    print(f"Analysis: {analysis}")