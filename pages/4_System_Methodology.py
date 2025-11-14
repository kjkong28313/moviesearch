import streamlit as st
from pathlib import Path
import sys

# Import authentication
sys.path.append(str(Path(__file__).resolve().parent.parent))
from auth import require_auth, show_user_info_sidebar

# Page configuration
st.set_page_config(
    layout="wide",
    page_title="Methodology - Movie Recommendation System",
    page_icon="📊"
)

# Require authentication
require_auth()

# Custom CSS
st.markdown("""
    <style>
    .methodology-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .tip-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .best-practice {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<div class="methodology-header">📊 System Methodology</div>', unsafe_allow_html=True)
    st.markdown("### Understanding the Movie Recommendation System Flow")
    
    with st.sidebar:
        #st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This app helps you find movies based on:
        - Semantic search (themes, plots)
        - Criteria search (actors, directors, year)
        - Combined searches
        """)


    # Show user info in sidebar
    show_user_info_sidebar()
    
    # Introduction
    st.markdown("""
    This page explains the **methodology and workflow** of our movie recommendation system. 
    The flowcharts below demonstrate how each component works together to deliver accurate 
    movie recommendations using a combination of RAG, agentic AI, semantic search, and structured filtering.
    """)
    
    st.divider()
    
    # Main sections in tabs
    tab1, tab2 = st.tabs([
        "📋 Methodology Overview",
        "🔄 Process Flowcharts", 
    ])
    
    with tab1:
        st.markdown("## 🎯 System Methodology Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🔍 Search Methodology
            
            Our system employs a **hybrid search approach** combining:
            
            **1. Semantic Search**
            - Uses AI embeddings (SentenceTransformer)
            - Understands natural language queries
            - Finds movies by meaning, not just keywords
            - 384-dimensional vector space
            
            **2. Structured Search**
            - Index-based filtering
            - Exact matching on metadata
            - Fast lookup by actor, director, genre, year
            - Supports complex AND queries
            
            **3. Hybrid Approach**
            - Combines both methods
            - Intersection of results (AND logic)
            - Best of both worlds
            """)
        
        with col2:
            st.markdown("""
            ### 🤖 Recommendation Methodology
            
            Our recommendation pipeline includes:
            
            **1. Query Analysis**
            - Parse user input into clauses
            - Identify semantic vs structured patterns
            - Extract search parameters
            
            **2. Candidate Retrieval**
            - Search popular movie source
            - Rank by relevance
            - Apply filters and intersections
            
            **3. AI Enhancement**
            - LLM analyzes candidates
            - Generates explanations
            - Ranks final recommendations
            
            **4. Result Enrichment**
            - Add full metadata
            - Find watch offers
            - Present with context
            """)
        
        st.divider()
        
        st.markdown("### 📈 Data Processing Methodology")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📥 Data Extraction**
            - Source: TMDB API
            - Pagination handling
            - Rate limiting (0.25s)
            - Error recovery
            - Data validation
            - Deduplication
            """)
        
        with col2:
            st.markdown("""
            **🏗️ Index Building**
            - 5 inverted indexes
            - O(1) lookup time
            - Memory-efficient
            - JSON persistence
            - Case-insensitive keys
            - Batch processing
            """)
        
        with col3:
            st.markdown("""
            **🧠 Vector Embedding**
            - Model: all-MiniLM-L6-v2
            - 384 dimensions
            - ChromaDB storage
            - Cosine similarity
            - Real-time querying
            - Incremental updates
            """)
    
    with tab2:
        st.markdown("## 🔄 Detailed Process Flowcharts")

        png_path = Path(__file__).resolve().parent.parent / "pages" / "flowchart.png"

        if png_path.exists():
            st.image(str(png_path), caption="Process Flowchart", width='stretch')
        else:
            st.warning(f"PNG file not found at: {png_path}")
        
    

if __name__ == "__main__":
    main()
