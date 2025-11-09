"""
MetaReviewer Agent: Synthesizes reviews and generates summaries
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List


class MetaReviewerAgent:
    """
    Agent responsible for synthesizing reviews and creating student-friendly summaries.
    """
    
    def __init__(self, agent_id: str = None, llm_client=None):
        self.agent_id = agent_id or f"meta-{uuid.uuid4().hex[:8]}"
        self.name = "MetaReviewerAgent"
        self.llm_client = llm_client
        
    def generate_review(self, paper_content: Dict[str, Any],
                       critic_analysis: Dict[str, Any],
                       citation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive review synthesizing all agent inputs.
        
        Args:
            paper_content: From Reader Agent
            critic_analysis: From Critic Agent
            citation_data: From CiteAgent (optional)
            
        Returns:
            Final review with multiple summary levels
        """
        review = {
            "executive_summary": "",
            "detailed_review": "",
            "eli5_summary": "",
            "key_takeaways": [],
            "recommendation": "",
            "confidence": 0.0,
            "visual_elements": {}
        }
        
        # Generate executive summary
        review["executive_summary"] = self._create_executive_summary(
            paper_content, critic_analysis
        )
        
        # Generate detailed review
        review["detailed_review"] = self._create_detailed_review(
            paper_content, critic_analysis, citation_data
        )
        
        # Generate ELI5 summary
        review["eli5_summary"] = self._create_eli5_summary(
            paper_content, critic_analysis
        )
        
        # Extract key takeaways
        review["key_takeaways"] = self._extract_key_takeaways(
            paper_content, critic_analysis
        )
        
        # Make recommendation
        review["recommendation"] = self._make_recommendation(critic_analysis)
        
        # Calculate confidence
        review["confidence"] = self._calculate_confidence(critic_analysis)
        
        # Generate visual elements
        review["visual_elements"] = self._generate_visual_elements(
            paper_content, critic_analysis
        )
        
        return review
    
    def _create_executive_summary(self, paper_content: Dict[str, Any],
                                 critic_analysis: Dict[str, Any]) -> str:
        """Create concise executive summary."""
        title = paper_content.get("title", "Unknown Title")
        abstract = paper_content.get("abstract", "")
        overall_score = critic_analysis.get("overall_score", 0)
        
        # Extract first sentence of abstract
        first_sentence = abstract.split('.')[0] if abstract else "No abstract available"
        
        summary = f"""**{title}**

**Quick Assessment**: Overall Score {overall_score:.1f}/10

**Main Contribution**: {first_sentence}.

**Verdict**: This paper presents {'a strong' if overall_score >= 7 else 'a moderate' if overall_score >= 5 else 'a weak'} contribution to the field."""
        
        return summary
    
    def _create_detailed_review(self, paper_content: Dict[str, Any],
                               critic_analysis: Dict[str, Any],
                               citation_data: Dict[str, Any] = None) -> str:
        """Create comprehensive detailed review."""
        title = paper_content.get("title", "Unknown Title")
        abstract = paper_content.get("abstract", "")
        scores = critic_analysis.get("detailed_scores", {})
        strengths = critic_analysis.get("strengths", [])
        weaknesses = critic_analysis.get("weaknesses", [])
        recommendations = critic_analysis.get("recommendations", [])
        
        review_parts = []
        
        # Header
        review_parts.append(f"# Detailed Review: {title}\n")
        
        # Overview
        review_parts.append("## Overview")
        review_parts.append(abstract[:500] + "..." if len(abstract) > 500 else abstract)
        review_parts.append("")
        
        # Scores
        review_parts.append("## Assessment Scores")
        for category, score in scores.items():
            review_parts.append(f"- **{category.title()}**: {score:.1f}/10")
        review_parts.append("")
        
        # Strengths
        review_parts.append("## Strengths")
        for i, strength in enumerate(strengths, 1):
            review_parts.append(f"{i}. {strength}")
        review_parts.append("")
        
        # Weaknesses
        review_parts.append("## Weaknesses")
        for i, weakness in enumerate(weaknesses, 1):
            review_parts.append(f"{i}. {weakness}")
        review_parts.append("")
        
        # Recommendations
        review_parts.append("## Recommendations for Improvement")
        for i, rec in enumerate(recommendations, 1):
            review_parts.append(f"{i}. {rec}")
        review_parts.append("")
        
        # Related Work (if available)
        if citation_data:
            related = citation_data.get("related_papers", [])[:3]
            if related:
                review_parts.append("## Related Work")
                for paper in related:
                    review_parts.append(f"- {paper.get('title', 'Unknown')} (Similarity: {paper.get('similarity_score', 0):.2f})")
                review_parts.append("")
        
        return "\n".join(review_parts)
    
    def _create_eli5_summary(self, paper_content: Dict[str, Any],
                            critic_analysis: Dict[str, Any]) -> str:
        """Create Explain-Like-I'm-5 summary."""
        title = paper_content.get("title", "This paper")
        abstract = paper_content.get("abstract", "")
        
        # Simplify the abstract
        simplified_parts = []
        
        simplified_parts.append("**What is this paper about?**")
        simplified_parts.append(f"Imagine you're trying to solve a puzzle. {title.split(':')[0] if ':' in title else title} is like finding a new way to put the pieces together.")
        simplified_parts.append("")
        
        simplified_parts.append("**What did they do?**")
        simplified_parts.append("The researchers looked at a problem and tried a new approach to solve it. They tested their idea and checked if it worked better than previous methods.")
        simplified_parts.append("")
        
        simplified_parts.append("**Why does it matter?**")
        overall_score = critic_analysis.get("overall_score", 0)
        if overall_score >= 7:
            simplified_parts.append("This work is important because it shows a new way to tackle this problem that works really well!")
        elif overall_score >= 5:
            simplified_parts.append("This work adds to our understanding of the problem, though there's still room for improvement.")
        else:
            simplified_parts.append("This work explores an interesting idea, but needs more development to be really useful.")
        simplified_parts.append("")
        
        simplified_parts.append("**The bottom line:**")
        strengths = critic_analysis.get("strengths", [])
        if strengths:
            simplified_parts.append(f"The main good thing: {strengths[0]}")
        weaknesses = critic_analysis.get("weaknesses", [])
        if weaknesses:
            simplified_parts.append(f"Something to improve: {weaknesses[0]}")
        
        return "\n".join(simplified_parts)
    
    def _extract_key_takeaways(self, paper_content: Dict[str, Any],
                              critic_analysis: Dict[str, Any]) -> List[str]:
        """Extract 3-5 key takeaways."""
        takeaways = []
        
        # Add main contribution
        title = paper_content.get("title", "")
        if title:
            takeaways.append(f"Main focus: {title}")
        
        # Add top strength
        strengths = critic_analysis.get("strengths", [])
        if strengths:
            takeaways.append(f"Key strength: {strengths[0]}")
        
        # Add critical insight
        scores = critic_analysis.get("detailed_scores", {})
        if scores:
            best_aspect = max(scores.items(), key=lambda x: x[1])
            takeaways.append(f"Strongest aspect: {best_aspect[0]} ({best_aspect[1]:.1f}/10)")
        
        # Add improvement area
        weaknesses = critic_analysis.get("weaknesses", [])
        if weaknesses:
            takeaways.append(f"Area for improvement: {weaknesses[0]}")
        
        # Add overall assessment
        overall = critic_analysis.get("overall_score", 0)
        takeaways.append(f"Overall quality: {overall:.1f}/10 - {'Excellent' if overall >= 8 else 'Good' if overall >= 6 else 'Fair' if overall >= 4 else 'Needs work'}")
        
        return takeaways[:5]
    
    def _make_recommendation(self, critic_analysis: Dict[str, Any]) -> str:
        """Make publication recommendation."""
        overall_score = critic_analysis.get("overall_score", 0)
        
        if overall_score >= 7.5:
            return "Accept - Strong contribution with minor revisions"
        elif overall_score >= 6.0:
            return "Weak Accept - Good work but needs improvements"
        elif overall_score >= 4.5:
            return "Major Revisions - Significant improvements needed"
        else:
            return "Reject - Does not meet publication standards"
    
    def _calculate_confidence(self, critic_analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the review."""
        # Base confidence on score consistency
        scores = list(critic_analysis.get("detailed_scores", {}).values())
        
        if not scores:
            return 0.5
        
        # Lower confidence if scores are very spread out
        score_range = max(scores) - min(scores)
        confidence = 1.0 - (score_range / 10.0)
        
        # Boost confidence if we have many data points
        if len(scores) >= 4:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_visual_elements(self, paper_content: Dict[str, Any],
                                 critic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for visualizations."""
        scores = critic_analysis.get("detailed_scores", {})
        
        return {
            "score_chart": {
                "categories": list(scores.keys()),
                "values": list(scores.values())
            },
            "summary_card": {
                "title": paper_content.get("title", "Unknown"),
                "overall_score": critic_analysis.get("overall_score", 0),
                "recommendation": self._make_recommendation(critic_analysis)
            },
            "metrics": {
                "sections": len(paper_content.get("sections", [])),
                "references": len(paper_content.get("references", [])),
                "word_count": paper_content.get("metadata", {}).get("word_count", 0)
            }
        }
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming MCP message."""
        action = message.get("payload", {}).get("action")
        data = message.get("payload", {}).get("data", {})
        
        if action == "generate_review":
            paper_content = data.get("paper_content", {})
            critic_analysis = data.get("critic_analysis", {})
            citation_data = data.get("citation_data")
            
            try:
                review = self.generate_review(
                    paper_content, 
                    critic_analysis,
                    citation_data
                )
                
                return {
                    "message_id": str(uuid.uuid4()),
                    "sender": self.name,
                    "receiver": message.get("sender"),
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "response",
                    "payload": {
                        "action": "generate_review",
                        "data": review
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
    agent = MetaReviewerAgent()
    
    test_paper = {
        "title": "Novel Deep Learning Approach",
        "abstract": "This paper presents innovative methods...",
        "sections": [{"heading": "Intro", "content": "..."}] * 5,
        "references": ["Ref"] * 20,
        "metadata": {"word_count": 5000}
    }
    
    test_critique = {
        "overall_score": 7.5,
        "strengths": ["Strong methodology", "Clear presentation"],
        "weaknesses": ["Limited baseline comparison"],
        "detailed_scores": {
            "novelty": 8.0,
            "methodology": 7.5,
            "clarity": 7.0,
            "reproducibility": 7.0
        },
        "recommendations": ["Add more ablations"]
    }
    
    review = agent.generate_review(test_paper, test_critique)
    print(review["eli5_summary"])