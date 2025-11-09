"""
Streamlit UI for Multi-Agent Research Paper Reviewer
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))                     # Commented out for now

from orchestrator import ResearchReviewOrchestrator
# from agents.orchestrator import ResearchReviewOrchestrator
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json


# Page configuration
st.set_page_config(
    page_title="Research Paper Reviewer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #2E86DE 0%, #54A0FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .score-box {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = ResearchReviewOrchestrator()
if 'review_results' not in st.session_state:
    st.session_state.review_results = None
if 'processing' not in st.session_state:
    st.session_state.processing = False


def create_score_chart(scores: dict):
    """Create radar chart for scores."""
    categories = list(scores.keys())
    values = list(scores.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=[c.title() for c in categories],
        fill='toself',
        name='Scores',
        fillcolor='rgba(46, 134, 222, 0.3)',
        line=dict(color='#2E86DE', width=2)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        height=400,
        margin=dict(t=40, b=40, l=60, r=60)
    )
    
    return fig


def create_metrics_bar(metrics: dict):
    """Create bar chart for paper metrics."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        marker_color='#2E86DE',
        text=list(metrics.values()),
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Paper Metrics",
        xaxis_title="Metric",
        yaxis_title="Count",
        height=300,
        margin=dict(t=60, b=40, l=40, r=40)
    )
    
    return fig


def display_review_results(results: dict):
    """Display complete review results."""
    if not results or "final_review" not in results:
        st.error("No review results available")
        return
    
    paper = results.get("paper_content", {})
    critique = results.get("critic_analysis", {})
    review = results.get("final_review", {})
    citations = results.get("citation_data", {})
    
    # Main title
    st.markdown(f"<h1 class='main-header'>📄 {paper.get('title', 'Paper Review')}</h1>", 
                unsafe_allow_html=True)
    
    # Tabs for different views
    tabs = st.tabs(["📊 Overview", "📝 Detailed Review", "🎯 ELI5 Summary", 
                    "📚 Related Papers", "📈 Metrics"])
    
    # Tab 1: Overview
    with tabs[0]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_score = critique.get("overall_score", 0)
            color = "#10ac84" if overall_score >= 7 else "#ee5a6f" if overall_score < 5 else "#f39c12"
            st.markdown(f"""
                <div class='score-box' style='background-color: {color}; color: white;'>
                    {overall_score:.1f}/10
                </div>
                <p style='text-align: center; font-size: 1.2rem; margin-top: 0.5rem;'>
                    Overall Score
                </p>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>📅 Authors</h3>
                    <p>{', '.join(paper.get('authors', ['Unknown'])[:3])}</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            recommendation = review.get("recommendation", "N/A")
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>✅ Recommendation</h3>
                    <p><strong>{recommendation}</strong></p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Executive Summary
        st.subheader("Executive Summary")
        st.markdown(review.get("executive_summary", "No summary available"))
        
        st.markdown("---")
        
        # Key Takeaways
        st.subheader("🎯 Key Takeaways")
        takeaways = review.get("key_takeaways", [])
        for i, takeaway in enumerate(takeaways, 1):
            st.markdown(f"{i}. {takeaway}")
        
        st.markdown("---")
        
        # Score Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Quality Scores")
            scores = critique.get("detailed_scores", {})
            if scores:
                fig = create_score_chart(scores)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Strengths & Weaknesses")
            strengths = critique.get("strengths", [])
            st.markdown("**✅ Strengths:**")
            for strength in strengths[:3]:
                st.markdown(f"- {strength}")
            
            st.markdown("**⚠️ Weaknesses:**")
            weaknesses = critique.get("weaknesses", [])
            for weakness in weaknesses[:3]:
                st.markdown(f"- {weakness}")
    
    # Tab 2: Detailed Review
    with tabs[1]:
        st.markdown(review.get("detailed_review", "No detailed review available"))
    
    # Tab 3: ELI5 Summary
    with tabs[2]:
        st.markdown("## Explain Like I'm 5 👶")
        st.info(review.get("eli5_summary", "No simplified summary available"))
        
        # Show abstract comparison
        with st.expander("📖 Original Abstract"):
            st.write(paper.get("abstract", "No abstract available"))
    
    # Tab 4: Related Papers
    with tabs[3]:
        related_papers = citations.get("related_papers", [])
        
        if related_papers:
            st.subheader(f"Found {len(related_papers)} Related Papers")
            
            for i, paper_info in enumerate(related_papers[:5], 1):
                with st.expander(f"{i}. {paper_info.get('title', 'Unknown')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Authors:** {', '.join(paper_info.get('authors', []))}")
                        st.write(f"**Published:** {paper_info.get('published', 'Unknown')}")
                        st.write(f"**Reason:** {paper_info.get('reason', 'Related work')}")
                        st.write(paper_info.get('abstract', ''))
                    
                    with col2:
                        similarity = paper_info.get('similarity_score', 0)
                        st.metric("Similarity", f"{similarity:.2%}")
                        st.markdown(f"[View on ArXiv]({paper_info.get('url', '#')})")
        else:
            st.warning("No related papers found")
        
        # Citation Statistics
        st.markdown("---")
        st.subheader("Citation Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Citations", citations.get("citation_count", 0))
        with col2:
            topics = citations.get("topics", [])
            st.metric("Topics Identified", len(topics))
        with col3:
            network = citations.get("citation_network", {})
            st.metric("Network Density", f"{network.get('network_density', 0):.2%}")
    
    # Tab 5: Metrics
    with tabs[4]:
        st.subheader("Processing Metrics")
        
        metadata = results.get("metadata", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Processing Time", f"{metadata.get('processing_time_seconds', 0):.2f}s")
        with col2:
            st.metric("Tool Calls", metadata.get('tool_calls', 0))
        with col3:
            st.metric("Errors", len(metadata.get('errors', [])))
        with col4:
            confidence = review.get('confidence', 0)
            st.metric("Confidence", f"{confidence:.1%}")
        
        st.markdown("---")
        
        # Paper Metrics
        visual_elements = review.get("visual_elements", {})
        metrics_data = visual_elements.get("metrics", {})
        
        if metrics_data:
            fig = create_metrics_bar(metrics_data)
            st.plotly_chart(fig, use_container_width=True)
        
        # Errors (if any)
        errors = metadata.get('errors', [])
        if errors:
            with st.expander("⚠️ View Errors"):
                for error in errors:
                    st.error(error)


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown("<h1 class='main-header'>🤖 Multi-Agent Research Paper Reviewer</h1>", 
                unsafe_allow_html=True)
    
    st.markdown("""
    <p style='text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;'>
        AI-powered paper review with multiple specialized agents
    </p>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📤 Upload Paper")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Upload PDF", "ArXiv ID"],
            index=0
        )
        
        paper_source = None
        source_type = None
        
        if input_method == "Upload PDF":
            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type=["pdf"],
                help="Upload a research paper in PDF format"
            )
            
            if uploaded_file:
                # Save uploaded file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    paper_source = tmp_file.name
                    source_type = "pdf"
                
                st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        else:  # ArXiv ID
            arxiv_id = st.text_input(
                "Enter ArXiv ID",
                placeholder="e.g., 2301.12345",
                help="Enter the ArXiv ID of the paper"
            )
            
            if arxiv_id:
                paper_source = arxiv_id
                source_type = "arxiv_id"
                st.success(f"✅ ArXiv ID: {arxiv_id}")
        
        st.markdown("---")
        
        # Review button
        review_button = st.button(
            "🚀 Start Review",
            disabled=not paper_source or st.session_state.processing,
            use_container_width=True,
            type="primary"
        )
        
        if review_button and paper_source:
            st.session_state.processing = True
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 Extracting paper content...")
                progress_bar.progress(25)
                
                # Run orchestrator
                results = st.session_state.orchestrator.review_paper(
                    paper_source=paper_source,
                    source_type=source_type
                )
                
                progress_bar.progress(100)
                status_text.text("✅ Review complete!")
                
                st.session_state.review_results = results
                st.session_state.processing = False
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.processing = False
                progress_bar.empty()
                status_text.empty()
        
        # Agent Status
        st.markdown("---")
        st.header("🤖 Agent Status")
        
        agents = [
            ("Reader", "5001", "📖"),
            ("Critic", "5002", "🔍"),
            ("MetaReviewer", "5003", "📝"),
            ("CiteAgent", "5004", "📚")
        ]
        
        for name, port, icon in agents:
            st.markdown(f"{icon} **{name}** - Port {port}")
        
        # Download results
        if st.session_state.review_results:
            st.markdown("---")
            st.header("💾 Export")
            
            # JSON export
            json_data = json.dumps(st.session_state.review_results, indent=2)
            st.download_button(
                "Download JSON",
                data=json_data,
                file_name=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Main content
    if st.session_state.review_results:
        display_review_results(st.session_state.review_results)
    else:
        # Welcome message
        st.info("""
        👋 **Welcome!** Upload a research paper or enter an ArXiv ID to get started.
        
        This system uses multiple AI agents to:
        - 📖 Extract and parse paper content
        - 🔍 Critically analyze methodology and quality
        - 📚 Find related papers and citations
        - 📝 Generate comprehensive reviews and ELI5 summaries
        """)
        
        # Feature showcase
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            ### 📖 Reader Agent
            Extracts paper structure, sections, and references
            """)
        
        with col2:
            st.markdown("""
            ### 🔍 Critic Agent
            Analyzes quality, identifies strengths/weaknesses
            """)
        
        with col3:
            st.markdown("""
            ### 📝 MetaReviewer
            Synthesizes reviews, creates ELI5 summaries
            """)
        
        with col4:
            st.markdown("""
            ### 📚 CiteAgent
            Finds related papers using ArXiv API
            """)


if __name__ == "__main__":
    main()