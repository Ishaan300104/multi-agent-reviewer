"""
CiteAgent: Analyzes citations and finds related papers
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
import arxiv
import re
from collections import Counter


class CiteAgent:
    """
    Agent responsible for citation analysis and finding related papers.
    Uses ArXiv API to discover related work.
    """
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"cite-{uuid.uuid4().hex[:8]}"
        self.name = "CiteAgent"
        self.arxiv_client = arxiv.Client()
        
    def analyze_citations(self, paper_content: Dict[str, Any],
                         max_related: int = 10) -> Dict[str, Any]:
        """
        Analyze citations and find related papers.
        
        Args:
            paper_content: Paper content from Reader Agent
            max_related: Maximum number of related papers to return
            
        Returns:
            Citation analysis and related papers
        """
        analysis = {
            "citation_count": 0,
            "key_citations": [],
            "related_papers": [],
            "citation_context": "",
            "citation_network": {},
            "topics": []
        }
        
        # Extract and analyze citations
        references = paper_content.get("references", [])
        analysis["citation_count"] = len(references)
        analysis["key_citations"] = self._identify_key_citations(references)
        
        # Find related papers using ArXiv API
        title = paper_content.get("title", "")
        abstract = paper_content.get("abstract", "")
        
        analysis["related_papers"] = self._find_related_papers(
            title, abstract, max_related
        )
        
        # Extract topics from title and abstract
        analysis["topics"] = self._extract_topics(title, abstract)
        
        # Analyze citation context
        analysis["citation_context"] = self._analyze_citation_context(
            paper_content, references
        )
        
        # Build citation network (simplified)
        analysis["citation_network"] = self._build_citation_network(
            references, analysis["related_papers"]
        )
        
        return analysis
    
    def _identify_key_citations(self, references: List[str]) -> List[Dict[str, Any]]:
        """Identify key/influential citations."""
        key_citations = []
        
        for ref in references[:10]:  # Top 10 references
            # Parse reference (simplified)
            citation_info = self._parse_reference(ref)
            if citation_info:
                key_citations.append(citation_info)
        
        return key_citations
    
    def _parse_reference(self, reference: str) -> Dict[str, Any]:
        """Parse a reference string into structured data."""
        # Simple parsing - extract year and approximate authors/title
        year_match = re.search(r'\b(19|20)\d{2}\b', reference)
        year = int(year_match.group(0)) if year_match else None
        
        # Try to identify if it's a high-impact reference
        # (e.g., contains "Nature", "Science", etc.)
        high_impact_venues = ["Nature", "Science", "Cell", "PNAS", "Lancet"]
        relevance = "high" if any(venue in reference for venue in high_impact_venues) else "medium"
        
        return {
            "text": reference[:200],  # Truncate
            "year": year,
            "relevance": relevance,
            "type": "journal" if any(j in reference.lower() for j in ["journal", "proceedings"]) else "unknown"
        }
    
    def _find_related_papers(self, title: str, abstract: str, 
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """Find related papers using ArXiv API."""
        related_papers = []
        
        # Extract keywords for search
        keywords = self._extract_keywords(title, abstract)
        
        if not keywords:
            return []
        
        # Search ArXiv
        search_query = " ".join(keywords[:5])  # Use top 5 keywords
        
        try:
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for result in self.arxiv_client.results(search):
                # Calculate similarity score (simplified)
                similarity = self._calculate_similarity(
                    title, abstract,
                    result.title, result.summary
                )
                
                related_papers.append({
                    "arxiv_id": result.entry_id.split('/')[-1],
                    "title": result.title,
                    "authors": [author.name for author in result.authors[:3]],
                    "abstract": result.summary[:300],
                    "published": result.published.isoformat() if result.published else None,
                    "similarity_score": similarity,
                    "url": result.entry_id,
                    "reason": self._explain_similarity(title, result.title)
                })
            
            # Sort by similarity
            related_papers.sort(key=lambda x: x["similarity_score"], reverse=True)
            
        except Exception as e:
            print(f"Error searching ArXiv: {e}")
        
        return related_papers[:max_results]
    
    def _extract_keywords(self, title: str, abstract: str) -> List[str]:
        """Extract keywords from title and abstract."""
        # Combine title and abstract
        text = f"{title} {abstract}".lower()
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'we', 'our', 'paper', 'study', 'research', 'approach', 'method'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text)
        
        # Count frequency
        word_counts = Counter(w for w in words if w not in stop_words and len(w) > 3)
        
        # Return top keywords
        return [word for word, count in word_counts.most_common(10)]
    
    def _calculate_similarity(self, title1: str, abstract1: str,
                             title2: str, abstract2: str) -> float:
        """Calculate similarity between two papers (simplified)."""
        # Simple keyword overlap similarity
        keywords1 = set(self._extract_keywords(title1, abstract1))
        keywords2 = set(self._extract_keywords(title2, abstract2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        similarity = intersection / union if union > 0 else 0.0
        
        # Boost if titles are very similar
        title_words1 = set(title1.lower().split())
        title_words2 = set(title2.lower().split())
        title_overlap = len(title_words1 & title_words2) / max(len(title_words1), len(title_words2))
        
        return min(similarity + (title_overlap * 0.3), 1.0)
    
    def _explain_similarity(self, title1: str, title2: str) -> str:
        """Explain why papers are similar."""
        # Extract common significant words
        words1 = set(w.lower() for w in title1.split() if len(w) > 4)
        words2 = set(w.lower() for w in title2.split() if len(w) > 4)
        
        common = words1 & words2
        
        if common:
            return f"Shared focus on: {', '.join(list(common)[:3])}"
        else:
            return "Related methodology or domain"
    
    def _extract_topics(self, title: str, abstract: str) -> List[str]:
        """Extract main topics/themes."""
        text = f"{title} {abstract}".lower()
        
        # Domain-specific keyword groups
        topic_keywords = {
            "Machine Learning": ["learning", "neural", "network", "deep", "model", "training"],
            "Computer Vision": ["image", "vision", "visual", "detection", "recognition"],
            "Natural Language": ["language", "text", "nlp", "translation", "semantic"],
            "Reinforcement Learning": ["reinforcement", "agent", "policy", "reward"],
            "Data Science": ["data", "analysis", "mining", "statistics"],
            "Optimization": ["optimization", "algorithm", "convergence", "efficient"]
        }
        
        topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        
        return topics[:3]  # Top 3 topics
    
    def _analyze_citation_context(self, paper_content: Dict[str, Any],
                                  references: List[str]) -> str:
        """Analyze how citations are used in the paper."""
        if len(references) == 0:
            return "No references found in the paper."
        
        context_parts = []
        
        # Analyze reference count
        ref_count = len(references)
        context_parts.append(f"The paper cites {ref_count} references, indicating ")
        
        if ref_count > 40:
            context_parts.append("a comprehensive literature review.")
        elif ref_count > 20:
            context_parts.append("a solid grounding in related work.")
        elif ref_count > 10:
            context_parts.append("moderate engagement with prior research.")
        else:
            context_parts.append("limited reference to prior work.")
        
        # Analyze temporal distribution
        years = []
        for ref in references:
            year_match = re.search(r'\b(19|20)\d{2}\b', ref)
            if year_match:
                years.append(int(year_match.group(0)))
        
        if years:
            recent_refs = sum(1 for y in years if y >= 2020)
            context_parts.append(f" {recent_refs} references are from recent work (2020+), ")
            
            if recent_refs / len(years) > 0.5:
                context_parts.append("showing good awareness of current research.")
            else:
                context_parts.append("with opportunity to include more recent work.")
        
        return "".join(context_parts)
    
    def _build_citation_network(self, references: List[str],
                                related_papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a simplified citation network."""
        return {
            "total_citations": len(references),
            "related_papers_found": len(related_papers),
            "network_density": len(related_papers) / max(len(references), 1),
            "avg_similarity": sum(p["similarity_score"] for p in related_papers) / max(len(related_papers), 1)
        }
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming MCP message."""
        action = message.get("payload", {}).get("action")
        data = message.get("payload", {}).get("data", {})
        
        if action == "analyze_citations":
            paper_content = data.get("paper_content", {})
            max_related = data.get("max_related", 10)
            
            try:
                analysis = self.analyze_citations(paper_content, max_related)
                
                return {
                    "message_id": str(uuid.uuid4()),
                    "sender": self.name,
                    "receiver": message.get("sender"),
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "response",
                    "payload": {
                        "action": "analyze_citations",
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
    agent = CiteAgent()
    
    test_paper = {
        "title": "Deep Learning for Image Classification",
        "abstract": "We present a novel deep learning approach for image classification using convolutional neural networks...",
        "references": ["Smith et al. 2020", "Jones 2021"] * 10
    }
    
    analysis = agent.analyze_citations(test_paper, max_related=5)
    print(f"Found {len(analysis['related_papers'])} related papers")
    print(f"Topics: {analysis['topics']}")