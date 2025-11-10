"""
LLM Client for interacting with OpenAI API
"""

import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
import json


class LLMClient:
    """
    Wrapper for OpenAI API to provide LLM capabilities to agents.
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Model to use (gpt-4o-mini is cheapest, gpt-4o for best quality)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        print(f"[LLM] Initialized with model: {model}")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = 0.3,
                       max_tokens: int = 2000,
                       response_format: Optional[Dict[str, str]] = None) -> str:
        """
        Get completion from OpenAI chat API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            response_format: Optional format spec (e.g., {"type": "json_object"})
            
        Returns:
            Response text from the model
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[LLM] Error: {str(e)}")
            raise
    
    def analyze_paper_content(self, paper_content: Dict[str, Any]) -> str:
        """
        Analyze paper content and provide insights.
        
        Args:
            paper_content: Structured paper content
            
        Returns:
            Analysis from LLM
        """
        title = paper_content.get("title", "Unknown")
        abstract = paper_content.get("abstract", "")
        sections = paper_content.get("sections", [])
        
        # Build context
        context = f"Title: {title}\n\nAbstract: {abstract}\n\n"
        
        if sections:
            context += "Sections:\n"
            for section in sections[:5]:  # First 5 sections
                heading = section.get("heading", "")
                content = section.get("content", "")[:500]  # First 500 chars
                context += f"- {heading}: {content}\n"
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert research paper reviewer with deep knowledge across multiple scientific domains."
            },
            {
                "role": "user",
                "content": f"Analyze this research paper:\n\n{context}\n\nProvide a brief analysis covering novelty, methodology, and potential impact."
            }
        ]
        
        return self.chat_completion(messages, temperature=0.3, max_tokens=500)
    
    def critique_methodology(self, paper_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get LLM critique of paper methodology.
        
        Args:
            paper_content: Structured paper content
            
        Returns:
            Structured critique with scores
        """
        title = paper_content.get("title", "Unknown")
        abstract = paper_content.get("abstract", "")
        
        # Find methodology section
        sections = paper_content.get("sections", [])
        method_content = ""
        for section in sections:
            heading = section.get("heading", "").lower()
            if any(word in heading for word in ["method", "approach", "experiment"]):
                method_content = section.get("content", "")[:2000]
                break
        
        prompt = f"""Analyze this research paper's methodology:

Title: {title}

Abstract: {abstract}

Methodology: {method_content if method_content else "Not explicitly stated"}

Please provide a structured critique in JSON format with:
- novelty_score: 0-10 rating
- methodology_score: 0-10 rating
- clarity_score: 0-10 rating
- reproducibility_score: 0-10 rating
- strengths: list of 2-3 key strengths
- weaknesses: list of 2-3 key weaknesses
- recommendations: list of 2-3 improvement suggestions

Respond ONLY with valid JSON."""

        messages = [
            {
                "role": "system",
                "content": "You are a critical research paper reviewer. Provide honest, constructive feedback."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.chat_completion(
                messages, 
                temperature=0.2, 
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "novelty_score": 6.0,
                "methodology_score": 6.0,
                "clarity_score": 6.0,
                "reproducibility_score": 6.0,
                "strengths": ["Analysis completed"],
                "weaknesses": ["Unable to parse detailed analysis"],
                "recommendations": ["Review methodology section"]
            }
    
    def generate_eli5_summary(self, paper_content: Dict[str, Any]) -> str:
        """
        Generate "Explain Like I'm 5" summary.
        
        Args:
            paper_content: Structured paper content
            
        Returns:
            Simple, accessible summary
        """
        title = paper_content.get("title", "Unknown")
        abstract = paper_content.get("abstract", "")
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at explaining complex scientific concepts in simple, accessible language suitable for beginners or students."
            },
            {
                "role": "user",
                "content": f"""Explain this research paper in simple terms that a non-expert can understand:

Title: {title}

Abstract: {abstract}

Create an ELI5 (Explain Like I'm 5) summary that:
1. Explains what problem the paper solves
2. Describes what the researchers did (in simple terms)
3. Explains why it matters
4. Uses analogies and everyday examples
5. Avoids technical jargon

Keep it under 200 words and make it engaging!"""
            }
        ]
        
        return self.chat_completion(messages, temperature=0.5, max_tokens=400)
    
    def generate_review_synthesis(self, 
                                  paper_content: Dict[str, Any],
                                  critic_analysis: Dict[str, Any]) -> str:
        """
        Synthesize comprehensive review from paper and critique.
        
        Args:
            paper_content: Paper content
            critic_analysis: Critique from Critic Agent
            
        Returns:
            Comprehensive review text
        """
        title = paper_content.get("title", "Unknown")
        abstract = paper_content.get("abstract", "")
        overall_score = critic_analysis.get("overall_score", 0)
        strengths = critic_analysis.get("strengths", [])
        weaknesses = critic_analysis.get("weaknesses", [])
        
        prompt = f"""Generate a comprehensive academic review for this paper:

Title: {title}
Abstract: {abstract}

Analysis Summary:
- Overall Score: {overall_score}/10
- Strengths: {', '.join(strengths)}
- Weaknesses: {', '.join(weaknesses)}

Write a professional review (300-400 words) that:
1. Summarizes the paper's contribution
2. Evaluates the methodology and results
3. Discusses strengths and limitations
4. Provides constructive recommendations
5. Concludes with an overall assessment

Use formal academic tone."""

        messages = [
            {
                "role": "system",
                "content": "You are a senior academic reviewer writing a comprehensive paper review."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        return self.chat_completion(messages, temperature=0.4, max_tokens=800)
    
    def extract_key_insights(self, paper_content: Dict[str, Any]) -> List[str]:
        """
        Extract key insights and takeaways from paper.
        
        Args:
            paper_content: Paper content
            
        Returns:
            List of key insights
        """
        title = paper_content.get("title", "Unknown")
        abstract = paper_content.get("abstract", "")
        
        prompt = f"""Extract 4-5 key insights from this research paper:

Title: {title}
Abstract: {abstract}

Provide the insights as a JSON list of strings. Each insight should be:
- One clear, concise sentence
- Highlight an important finding or contribution
- Be accessible to researchers in the field

Format: {{"insights": ["insight 1", "insight 2", ...]}}"""

        messages = [
            {
                "role": "system",
                "content": "You are a research analyst extracting key insights from papers."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.chat_completion(
                messages,
                temperature=0.3,
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            data = json.loads(response)
            return data.get("insights", [])
        except:
            return [
                "Main contribution identified",
                "Methodology documented",
                "Results presented",
                "Further research suggested"
            ]


# Singleton instance
_llm_client = None

def get_llm_client(api_key: str = None, model: str = "gpt-4o-mini") -> LLMClient:
    """
    Get or create LLM client singleton.
    
    Args:
        api_key: OpenAI API key
        model: Model to use (gpt-4o-mini is cheapest)
        
    Returns:
        LLM client instance
    """
    global _llm_client
    
    if _llm_client is None:
        _llm_client = LLMClient(api_key=api_key, model=model)
    
    return _llm_client


if __name__ == "__main__":
    # Test the LLM client
    import os
    
    # Make sure to set your API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    client = get_llm_client()
    
    # Test paper
    test_paper = {
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        "sections": [
            {"heading": "Introduction", "content": "Recurrent neural networks have been the standard..."},
            {"heading": "Model Architecture", "content": "The Transformer follows this overall architecture..."}
        ]
    }
    
    print("Testing LLM Client...")
    print("\n1. Analysis:")
    print(client.analyze_paper_content(test_paper))
    
    print("\n2. ELI5 Summary:")
    print(client.generate_eli5_summary(test_paper))
    
    print("\n3. Key Insights:")
    insights = client.extract_key_insights(test_paper)
    for i, insight in enumerate(insights, 1):
        print(f"   {i}. {insight}")