# """
# Reader Agent: Extracts and structures paper content from PDFs
# """

# import uuid
# from datetime import datetime
# from typing import Dict, Any, List
# import pymupdf as fitz
# import re
# from pathlib import Path


# class ReaderAgent:
#     """
#     Agent responsible for extracting and structuring research paper content.
#     """
    
#     def __init__(self, agent_id: str = None):
#         self.agent_id = agent_id or f"reader-{uuid.uuid4().hex[:8]}"
#         self.name = "ReaderAgent"
        
#     def extract_paper(self, source: str, source_type: str = "pdf") -> Dict[str, Any]:
#         """
#         Extract paper content from various sources.
        
#         Args:
#             source: File path, URL, or ArXiv ID
#             source_type: Type of source ('pdf', 'arxiv_id', 'url')
            
#         Returns:
#             Structured paper content
#         """
#         if source_type == "pdf":
#             return self._extract_from_pdf(source)
#         elif source_type == "arxiv_id":
#             # Download from ArXiv first, then extract
#             pdf_path = self._download_arxiv_paper(source)
#             return self._extract_from_pdf(pdf_path)
#         else:
#             raise ValueError(f"Unsupported source type: {source_type}")
    
#     def _extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
#         """
#         Extract content from PDF file using PyMuPDF.
        
#         Args:
#             pdf_path: Path to PDF file
            
#         Returns:
#             Structured content dictionary
#         """
#         doc = fitz.open(pdf_path)
        
#         # Extract full text
#         full_text = ""
#         for page in doc:
#             full_text += page.get_text()
        
#         # Parse structure
#         title = self._extract_title(full_text)
#         abstract = self._extract_abstract(full_text)
#         authors = self._extract_authors(full_text)
#         sections = self._extract_sections(full_text)
#         references = self._extract_references(full_text)
        
#         doc.close()
        
#         return {
#             "paper_id": self._generate_paper_id(title),
#             "title": title,
#             "authors": authors,
#             "abstract": abstract,
#             "sections": sections,
#             "references": references,
#             "metadata": {
#                 "source": pdf_path,
#                 "page_count": len(doc),
#                 "word_count": len(full_text.split()),
#                 "extracted_at": datetime.now().isoformat()
#             }
#         }
    
#     def _extract_title(self, text: str) -> str:
#         """Extract paper title from text."""
#         lines = text.split('\n')
#         # Title is usually in the first few lines, longer than other text
#         for i, line in enumerate(lines[:10]):
#             line = line.strip()
#             if len(line) > 20 and len(line) < 200:
#                 # Check if next line is not part of title
#                 if i + 1 < len(lines) and len(lines[i + 1].strip()) < 10:
#                     return line
#         return lines[0].strip() if lines else "Unknown Title"
    
#     def _extract_abstract(self, text: str) -> str:
#         """Extract abstract from text."""
#         # Look for "Abstract" keyword
#         abstract_pattern = r'Abstract\s*[:\-]?\s*(.*?)(?=\n\n|\nIntroduction|\n1\.|\nKeywords)'
#         match = re.search(abstract_pattern, text, re.IGNORECASE | re.DOTALL)
#         if match:
#             return match.group(1).strip()
        
#         # Fallback: take first substantial paragraph
#         paragraphs = text.split('\n\n')
#         for para in paragraphs:
#             if len(para) > 100:
#                 return para.strip()
        
#         return "Abstract not found"
    
#     def _extract_authors(self, text: str) -> List[str]:
#         """Extract author names from text."""
#         # Look for author patterns after title
#         lines = text.split('\n')
#         authors = []
        
#         # Simple heuristic: names appear in first 20 lines
#         for line in lines[:20]:
#             line = line.strip()
#             # Check if line contains potential author names
#             if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line):
#                 # Split by commas or 'and'
#                 author_list = re.split(r',|\sand\s', line)
#                 authors.extend([a.strip() for a in author_list if a.strip()])
        
#         return authors[:10]  # Limit to 10 authors
    
#     def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
#         """Extract paper sections with headings and content."""
#         sections = []
        
#         # Common section headings
#         section_patterns = [
#             r'\n(\d+\.?\s+[A-Z][a-zA-Z\s]+)\n',  # Numbered sections
#             r'\n([A-Z][A-Z\s]+)\n',  # ALL CAPS sections
#             r'\n([A-Z][a-zA-Z\s]+)\n(?=[A-Z])'  # Title case sections
#         ]
        
#         for pattern in section_patterns:
#             matches = re.finditer(pattern, text)
#             for match in matches:
#                 heading = match.group(1).strip()
#                 start_pos = match.end()
                
#                 # Find next section or end
#                 next_match = re.search(pattern, text[start_pos:])
#                 end_pos = start_pos + next_match.start() if next_match else len(text)
                
#                 content = text[start_pos:end_pos].strip()
                
#                 sections.append({
#                     "heading": heading,
#                     "level": self._determine_section_level(heading),
#                     "content": content[:1000]  # Limit content length
#                 })
        
#         return sections[:15]  # Limit to 15 sections
    
#     def _extract_references(self, text: str) -> List[str]:
#         """Extract references from text."""
#         references = []
        
#         # Look for references section
#         ref_pattern = r'References\s*\n(.*?)(?=\n\n[A-Z]|$)'
#         match = re.search(ref_pattern, text, re.IGNORECASE | re.DOTALL)
        
#         if match:
#             ref_text = match.group(1)
#             # Split by common reference patterns
#             ref_lines = re.split(r'\n\[\d+\]|\n\d+\.', ref_text)
#             references = [ref.strip() for ref in ref_lines if len(ref.strip()) > 20]
        
#         return references[:50]  # Limit to 50 references
    
#     def _determine_section_level(self, heading: str) -> int:
#         """Determine section hierarchy level."""
#         if re.match(r'^\d+\s', heading):
#             return 1
#         elif re.match(r'^\d+\.\d+\s', heading):
#             return 2
#         elif heading.isupper():
#             return 1
#         else:
#             return 2
    
#     def _generate_paper_id(self, title: str) -> str:
#         """Generate unique paper ID from title."""
#         clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
#         return f"paper-{clean_title[:20]}-{uuid.uuid4().hex[:8]}"
    
#     def _download_arxiv_paper(self, arxiv_id: str) -> str:
#         """Download paper from ArXiv."""
#         import arxiv
        
#         search = arxiv.Search(id_list=[arxiv_id])
#         paper = next(search.results())
        
#         pdf_path = f"data/sample_papers/{arxiv_id}.pdf"
#         Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
        
#         paper.download_pdf(filename=pdf_path)
#         return pdf_path
    
#     def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Process incoming MCP message.
        
#         Args:
#             message: Standardized message format
            
#         Returns:
#             Response message
#         """
#         action = message.get("payload", {}).get("action")
#         data = message.get("payload", {}).get("data", {})
        
#         if action == "extract_paper":
#             source = data.get("source")
#             source_type = data.get("source_type", "pdf")
            
#             try:
#                 paper_content = self.extract_paper(source, source_type)
                
#                 return {
#                     "message_id": str(uuid.uuid4()),
#                     "sender": self.name,
#                     "receiver": message.get("sender"),
#                     "timestamp": datetime.now().isoformat(),
#                     "message_type": "response",
#                     "payload": {
#                         "action": "extract_paper",
#                         "data": paper_content
#                     },
#                     "context": message.get("context", {})
#                 }
#             except Exception as e:
#                 return {
#                     "message_id": str(uuid.uuid4()),
#                     "sender": self.name,
#                     "receiver": message.get("sender"),
#                     "timestamp": datetime.now().isoformat(),
#                     "message_type": "error",
#                     "payload": {
#                         "error": str(e),
#                         "action": action
#                     },
#                     "context": message.get("context", {})
#                 }
        
#         return {
#             "message_type": "error",
#             "payload": {"error": f"Unknown action: {action}"}
#         }


# if __name__ == "__main__":
#     # Test the agent
#     agent = ReaderAgent()
    
#     test_message = {
#         "message_id": str(uuid.uuid4()),
#         "sender": "test_client",
#         "receiver": "ReaderAgent",
#         "timestamp": datetime.now().isoformat(),
#         "message_type": "request",
#         "payload": {
#             "action": "extract_paper",
#             "data": {
#                 "source": "data/sample_papers/sample.pdf",
#                 "source_type": "pdf"
#             }
#         },
#         "context": {
#             "session_id": str(uuid.uuid4())
#         }
#     }
    
#     response = agent.process_message(test_message)
#     print(f"Response: {response}")






















"""
Reader Agent: Extracts and structures paper content from PDFs
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
import pymupdf as fitz
import re
from pathlib import Path


class ReaderAgent:
    """
    Agent responsible for extracting and structuring research paper content.
    """
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"reader-{uuid.uuid4().hex[:8]}"
        self.name = "ReaderAgent"
        
    def extract_paper(self, source: str, source_type: str = "pdf") -> Dict[str, Any]:
        """
        Extract paper content from various sources.
        
        Args:
            source: File path, URL, or ArXiv ID
            source_type: Type of source ('pdf', 'arxiv_id', 'url')
            
        Returns:
            Structured paper content
        """
        if source_type == "pdf":
            return self._extract_from_pdf(source)
        elif source_type == "arxiv_id":
            # Download from ArXiv first, then extract
            pdf_path = self._download_arxiv_paper(source)
            return self._extract_from_pdf(pdf_path)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract content from PDF file using PyMuPDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Structured content dictionary
        """
        doc = fitz.open(pdf_path)
        
        # --- FIX: Get the page count while the doc is still open ---
        page_count = len(doc) 
        
        # Extract full text
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Parse structure
        title = self._extract_title(full_text)
        abstract = self._extract_abstract(full_text)
        authors = self._extract_authors(full_text)
        sections = self._extract_sections(full_text)
        references = self._extract_references(full_text)
        
        doc.close() # Now it's safe to close
        
        return {
            "paper_id": self._generate_paper_id(title),
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "sections": sections,
            "references": references,
            "metadata": {
                "source": pdf_path,
                # --- FIX: Use the variable here ---
                "page_count": page_count, 
                "word_count": len(full_text.split()),
                "extracted_at": datetime.now().isoformat()
            }
        }
    
    def _extract_title(self, text: str) -> str:
        """Extract paper title from text."""
        lines = text.split('\n')
        # Title is usually in the first few lines, longer than other text
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if len(line) > 20 and len(line) < 200:
                # Check if next line is not part of title
                if i + 1 < len(lines) and len(lines[i + 1].strip()) < 10:
                    return line
        return lines[0].strip() if lines else "Unknown Title"
    
    def _extract_abstract(self, text: str) -> str:
        """Extract abstract from text."""
        # Look for "Abstract" keyword
        abstract_pattern = r'Abstract\s*[:\-]?\s*(.*?)(?=\n\n|\nIntroduction|\n1\.|\nKeywords)'
        match = re.search(abstract_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: take first substantial paragraph
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if len(para) > 100:
                return para.strip()
        
        return "Abstract not found"
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract author names from text."""
        # Look for author patterns after title
        lines = text.split('\n')
        authors = []
        
        # Simple heuristic: names appear in first 20 lines
        for line in lines[:20]:
            line = line.strip()
            # Check if line contains potential author names
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line):
                # Split by commas or 'and'
                author_list = re.split(r',|\sand\s', line)
                authors.extend([a.strip() for a in author_list if a.strip()])
        
        return authors[:10]  # Limit to 10 authors
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract paper sections with headings and content."""
        sections = []
        
        # Common section headings
        section_patterns = [
            r'\n(\d+\.?\s+[A-Z][a-zA-Z\s]+)\n',  # Numbered sections
            r'\n([A-Z][A-Z\s]+)\n',  # ALL CAPS sections
            r'\n([A-Z][a-zA-Z\s]+)\n(?=[A-Z])'  # Title case sections
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                heading = match.group(1).strip()
                start_pos = match.end()
                
                # Find next section or end
                next_match = re.search(pattern, text[start_pos:])
                end_pos = start_pos + next_match.start() if next_match else len(text)
                
                content = text[start_pos:end_pos].strip()
                
                sections.append({
                    "heading": heading,
                    "level": self._determine_section_level(heading),
                    "content": content[:1000]  # Limit content length
                })
        
        return sections[:15]  # Limit to 15 sections
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract references from text."""
        references = []
        
        # Look for references section
        ref_pattern = r'References\s*\n(.*?)(?=\n\n[A-Z]|$)'
        match = re.search(ref_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            ref_text = match.group(1)
            # Split by common reference patterns
            ref_lines = re.split(r'\n\[\d+\]|\n\d+\.', ref_text)
            references = [ref.strip() for ref in ref_lines if len(ref.strip()) > 20]
        
        return references[:50]  # Limit to 50 references
    
    def _determine_section_level(self, heading: str) -> int:
        """Determine section hierarchy level."""
        if re.match(r'^\d+\s', heading):
            return 1
        elif re.match(r'^\d+\.\d+\s', heading):
            return 2
        elif heading.isupper():
            return 1
        else:
            return 2
    
    def _generate_paper_id(self, title: str) -> str:
        """Generate unique paper ID from title."""
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
        return f"paper-{clean_title[:20]}-{uuid.uuid4().hex[:8]}"
    
    def _download_arxiv_paper(self, arxiv_id: str) -> str:
        """Download paper from ArXiv."""
        import arxiv
        
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        pdf_path = f"data/sample_papers/{arxiv_id}.pdf"
        Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
        
        paper.download_pdf(filename=pdf_path)
        return pdf_path
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming MCP message.
        
        Args:
            message: Standardized message format
            
        Returns:
            Response message
        """
        action = message.get("payload", {}).get("action")
        data = message.get("payload", {}).get("data", {})
        
        if action == "extract_paper":
            source = data.get("source")
            source_type = data.get("source_type", "pdf")
            
            try:
                paper_content = self.extract_paper(source, source_type)
                
                return {
                    "message_id": str(uuid.uuid4()),
                    "sender": self.name,
                    "receiver": message.get("sender"),
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "response",
                    "payload": {
                        "action": "extract_paper",
                        "data": paper_content
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
    agent = ReaderAgent()
    
    test_message = {
        "message_id": str(uuid.uuid4()),
        "sender": "test_client",
        "receiver": "ReaderAgent",
        "timestamp": datetime.now().isoformat(),
        "message_type": "request",
        "payload": {
            "action": "extract_paper",
            "data": {
                "source": "data/sample_papers/sample.pdf",
                "source_type": "pdf"
            }
        },
        "context": {
            "session_id": str(uuid.uuid4())
        }
    }
    
    response = agent.process_message(test_message)
    print(f"Response: {response}")