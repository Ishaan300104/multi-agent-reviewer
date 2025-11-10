# Multi-Agent Research Paper Reviewer System

A sophisticated LLM-based multi-agent system for reviewing, analyzing, and summarizing academic research papers using MCP (Model Context Protocol) architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (MCP Client)                 │
│                  (Paper Upload & Visualization)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agent Orchestrator                          │
│              (LangGraph Workflow Manager)                    │
└─────┬──────────┬──────────┬──────────┬─────────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Reader  │ │  Critic  │ │   Meta   │ │   Cite   │
│  Agent   │ │  Agent   │ │ Reviewer │ │  Agent   │
│          │ │          │ │  Agent   │ │          │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   PDF    │ │   Text   │ │ Summary  │ │  ArXiv   │
│ Extract  │ │ Analysis │ │ Synth.   │ │   API    │
│   Tool   │ │   Tool   │ │   Tool   │ │   Tool   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## Agent Roles

### 1. **Reader Agent** (MCP Server: Port 5001)
- **Role**: Extracts and parses paper content
- **Tools**: PDF extraction, text parsing
- **Output**: Structured paper content (title, abstract, sections, references)

### 2. **Critic Agent** (MCP Server: Port 5002)
- **Role**: Analyzes methodology, identifies weaknesses
- **Tools**: Text analysis, quality assessment
- **Output**: Critical review with strengths/weaknesses

### 3. **MetaReviewer Agent** (MCP Server: Port 5003)
- **Role**: Synthesizes reviews, generates student-friendly summary
- **Tools**: Summary generation, complexity simplification
- **Output**: Comprehensive review + ELI5 summary

### 4. **CiteAgent** (MCP Server: Port 5004)
- **Role**: Finds related papers, validates citations
- **Tools**: ArXiv API, citation extraction
- **Output**: Related papers, citation context

## Project Structure

```
research-paper-reviewer/
├── agents/
│   ├── __init__.py              # I added this to make agent folder run as a module
|   ├── llm_client.py            # For LLM Integration
│   ├── reader_agent.py          # PDF extraction & parsing
│   ├── critic_agent.py          # Critical analysis
│   ├── meta_reviewer_agent.py   # Review synthesis
│   ├── cite_agent.py            # Citation & related papers
│   └── orchestrator.py          # LangGraph workflow
├── mcp_server/
│   ├── __init__.py              # I added this to make mcp_server folder run as a module
│   ├── base_server.py           # Base MCP server implementation
│   ├── reader_server.py         # Reader agent MCP server
│   ├── critic_server.py         # Critic agent MCP server
│   ├── meta_reviewer_server.py  # MetaReviewer MCP server
│   ├── cite_server.py           # CiteAgent MCP server
│   └── client.py                # MCP client for orchestration
├── data/
│   ├── sample_papers/           # Sample PDF papers (papers get saved when you run it locally)
│   ├── arxiv_metadata.json      # ArXiv metadata cache
│   └── processed/               # Processed results
├── eval/
│   ├── test_cases.json          # 6+ test scenarios
│   ├── run_eval.py              # Evaluation harness
│   ├── metrics.py               # Metric calculations
│   └── results/                 # Test results
├── ui/
│   └── streamlit_app.py         # Main Streamlit interface
├── requirements.txt
├── config.yaml                   
├── README.md
└── setup.py
```

## Installation

### Prerequisites
- Python 3.9+
- pip
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd research-paper-reviewer
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download sample data** (optional)
```bash
# Download sample ArXiv papers
python scripts/download_samples.py
```

## Usage

### Starting MCP Servers

Start each agent's MCP server in separate terminals:

```bash
# Terminal 1: Reader Agent
python mcp-server/reader_server.py

# Terminal 2: Critic Agent
python mcp-server/critic_server.py

# Terminal 3: MetaReviewer Agent
python mcp-server/meta_reviewer_server.py

# Terminal 4: CiteAgent
python mcp-server/cite_server.py
```

### Running the Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Access at: `http://localhost:8501`

### Running Evaluation Harness

```bash
# Run all test cases
python eval/run_eval.py

# Run specific test case
python eval/run_eval.py --test-id test_1

# Generate metrics report
python eval/run_eval.py --report
```

## API Contracts

### Message Schema

All agents communicate using standardized JSON messages:

```json
{
  "message_id": "unique-uuid",
  "sender": "agent_name",
  "receiver": "agent_name",
  "timestamp": "2025-11-09T10:30:00Z",
  "message_type": "request|response|error",
  "payload": {
    "action": "extract|analyze|review|cite",
    "data": {},
    "metadata": {}
  },
  "context": {
    "paper_id": "arxiv-id",
    "session_id": "session-uuid"
  }
}
```

### Agent Input/Output Contracts

#### Reader Agent
**Input:**
```json
{
  "action": "extract",
  "data": {
    "pdf_path": "path/to/paper.pdf",
    "extract_references": true
  }
}
```

**Output:**
```json
{
  "paper_content": {
    "title": "Paper Title",
    "abstract": "Abstract text...",
    "sections": [{"heading": "Introduction", "content": "..."}],
    "references": ["ref1", "ref2"]
  }
}
```

#### Critic Agent
**Input:**
```json
{
  "action": "analyze",
  "data": {
    "paper_content": {},
    "focus_areas": ["methodology", "results"]
  }
}
```

**Output:**
```json
{
  "critique": {
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "methodology_score": 7.5,
    "clarity_score": 8.0
  }
}
```

## Key Assumptions

1. **PDF Format**: Papers are assumed to be in standard academic PDF format
2. **ArXiv Papers**: Primary focus on ArXiv papers (API integration)
3. **English Language**: All papers processed are in English
4. **MCP Local Deployment**: All MCP servers run on localhost (ports 5001-5004)
5. **LLM Model**: Uses OpenAI GPT-4 or compatible API (configurable)
6. **Internet Required**: For ArXiv API access and citation validation

## Configuration

Edit `config.yaml` to customize:

```yaml
agents:
  reader:
    port: 5001
    max_tokens: 4000
  critic:
    port: 5002
    max_tokens: 2000
  meta_reviewer:
    port: 5003
    max_tokens: 3000
  cite_agent:
    port: 5004
    max_tokens: 1500

llm:
  provider: "openai"  # or "anthropic", "cohere"
  model: "gpt-4"
  temperature: 0.3
  api_key: "${OPENAI_API_KEY}"

arxiv:
  max_results: 10
  sort_by: "relevance"
  cache_enabled: true
```

## Evaluation Metrics

The system tracks:
- **Success Rate**: % of successfully processed papers
- **Average Latency**: Time per paper (end-to-end)
- **Tool Call Count**: Number of tool invocations per agent
- **Constraint Violations**: Protocol/schema violations
- **Review Quality Score**: Manual evaluation of review quality
- **Citation Accuracy**: Correctness of related paper suggestions

## Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
python eval/run_eval.py --mode e2e
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-agent`)
3. Commit changes (`git commit -am 'Add new agent'`)
4. Push to branch (`git push origin feature/new-agent`)
5. Create Pull Request

## License

MIT License - see LICENSE file for details

## Contact

For questions or issues, please open a GitHub issue or contact the maintainers.

## Acknowledgments

- ArXiv for providing open access to research papers
- MCP Protocol specification
- LangGraph framework
- Streamlit for rapid UI development