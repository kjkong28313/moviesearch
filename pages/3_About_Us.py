################################################################################
# FILE: pages/3_About_Us.py
# LOCATION: pages/ directory  
################################################################################

import streamlit as st
from pathlib import Path
import json
import sys

# Import authentication
sys.path.append(str(Path(__file__).resolve().parent.parent))
from auth import require_auth, show_user_info_sidebar, is_admin

# Page configuration
st.set_page_config(
    layout="centered",
    page_title="About - Movie Recommendation System",
    page_icon="ℹ️"
)

# Require authentication
require_auth()

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)


def get_system_stats():
    """Get statistics about the system"""
    stats = {
        "movies_count": 0,
        "db_exists": False,
        "indexes_exist": False
    }
    
    try:
        script_path = Path(__file__).resolve().parent.parent
        data_path = script_path / "data" / "tmdb_movies_full_credits.json"
        
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                movies = json.load(f)
                stats["movies_count"] = len(movies)
        
        # Check for vector DB
        chroma_path = script_path / "data" / "chroma_db"
        stats["db_exists"] = chroma_path.exists()
        
        # Check for indexes
        index_files = ["actor_index.json", "director_index.json", "genre_index.json"]
        index_path = script_path / "data"
        stats["indexes_exist"] = all((index_path / f).exists() for f in index_files)
        
    except Exception:
        pass
    
    return stats


def main():
    # Header
    st.title("ℹ️ About Movie Recommendation System")
    st.markdown("---")
    
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
    ### 🎬 Welcome to the Movie Recommendation System
    
    In today's streaming era, users struggle with two critical pain points: inadequate movie 
    search that doesn't understand descriptive queries and fragmented information about where 
    movies can be watched. Existing platforms force users to use rigid keyword searches that 
    fail to capture the richness of human language, while leaving them to manually hunt 
    across multiple services to find viewing options. Our Movie Recommendation System solves
    both problems through AI-powered semantic search that understands natural descriptions 
    and automated discovery of streaming, rental, and purchase options across all major platforms.            

    Whether you're looking for "a heartwarming story about friendship" or "action movies starring 
    Tom Cruise from 2020," we've got you covered!
    """)
    
    # System Status
    st.markdown("### 📊 System Status")
    stats = get_system_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Movies Loaded", f"{stats['movies_count']:,}")
    with col2:
        status = "✅ Active" if stats['db_exists'] else "❌ Not Setup"
        st.metric("Vector DB", status)
    with col3:
        status = "✅ Built" if stats['indexes_exist'] else "❌ Missing"
        st.metric("Search Indexes", status)
    
    st.markdown("---")
    
    # Features
    st.markdown("### ✨ Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
        <h4>🔍 Semantic Search</h4>
        <p>Search using natural language descriptions of plots, themes, and moods. 
        Our AI understands what you're looking for beyond just keywords.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
        <h4>🎯 Structured Filtering</h4>
        <p>Filter by specific criteria like actors, directors, genres, production companies, 
        and release years for precise results.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
        <h4>🤖 AI Recommendations</h4>
        <p>Get intelligent movie recommendations with explanations of why each movie 
        matches your query using LLM (openAI).</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
        <h4>🎫 Watch Offers</h4>
        <p>Find where to watch your chosen movies online, including rental and purchase 
        options across different platforms powered by Agentic AI.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How to Use
    st.markdown("### 📖 How to Use This App")
    
    with st.expander("🚀 Getting Started", expanded=True):
        if is_admin():
            st.markdown("""
            **Administrator Setup:**
            1. **Extract Movies** - Navigate to "Extract All Movies" page
            2. Set the number of pages to fetch
            3. Click "Start Extraction"
            4. **Load Movies** - Go to "Load All Movies" page
            5. Click "Start Loading" to create the vector database
            6. **Search** - Return to Main and start searching!
            """)
        else:
            st.markdown("""
            **Using the Search:**
            1. Go to the **Main** page
            2. Enter your movie search query
            3. Use natural language or structured criteria
            4. View recommendations and where to watch
            
            **Browse Movies:**
            - Navigate to **View All Movies** to explore the complete database
            - Use filters to narrow down your search
            - Export results as CSV
            """)
    
    with st.expander("🔎 Search Examples"):
        st.markdown("""
        **Semantic Search:**
        - "romantic comedy with happy ending"
        - "dark thriller about revenge"
        - "inspiring story about overcoming adversity"
        
        **Structured Search:**
        - "starring tom hanks"
        - "directed by christopher nolan"
        - "genre is action AND in 2020"
        
        **Combined Search:**
        - "heartwarming family story AND released after 2015"
        - "sci-fi movie starring keanu reeves"
        - "thriller directed by david fincher AND before 2010"
        """)
    
    with st.expander("⚙️ System Requirements"):
        st.markdown("""
        **Required:**
        - Python 3.8+
        - Streamlit
        - ChromaDB for vector storage
        - SentenceTransformer for embeddings
        - openAI with gpt-4o-mini model (for recommendations)
        
        **Optional:**
        - TMDB API key (for extracting movies)
        - SerpAPI key (for finding watch offers)
        """)
    
    st.markdown("---")
    
    # User Role Information
    st.markdown("### 👥 User Roles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **👤 Normal User**
        - Search for movies
        - View all movies database
        - Filter and export data
        - Access documentation
        """)
    
    with col2:
        st.markdown("""
        **🔑 Administrator**
        - All normal user features
        - Extract movies from TMDB
        - Build search indexes
        - Load vector database
        - Full system access
        """)
    
    # Show current role
    if is_admin():
        st.info("✅ You are logged in as **Administrator** with full system access.")
    else:
        st.info("✅ You are logged in as **Normal User**. Contact admin for data management access.")
    
    st.markdown("---")
    
    # Technology Stack
    st.markdown("### 🛠️ Technology Stack")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Frontend**
        - Streamlit
        - Pandas
        - Matplotlib
        """)
    
    with col2:
        st.markdown("""
        **AI/ML**
        - SentenceTransformer
        - ChromaDB
        - openAI (gpt-4o-mini)
        """)
    
    with col3:
        st.markdown("""
        **Data Sources**
        - TMDB API
        - SerpAPI
        """)
    
    st.markdown("---")
    
    # Tips
    st.markdown("### 💡 Tips for Best Results")
    
    tips = [
        "**Be specific** - The more details you provide, the better the results",
        "**Combine searches** - Mix semantic descriptions with specific criteria using 'AND'",
        "**Use natural language** - Write your queries as you would describe a movie to a friend",
        "**Try variations** - If you don't get good results, rephrase your query",
        "**Check filters** - View All Movies page has advanced filtering options"
    ]
    
    for tip in tips:
        st.markdown(f"- {tip}")
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    ### 📧 Support & Feedback
    
    If you encounter any issues or have suggestions:
    - Check the system status above to ensure all components are set up
    - Review the search examples and tips
    - Contact your system administrator for technical issues
    
    **Note:** This is a demonstration application for educational purposes.
    """)
    
    # Quick Links
    st.markdown("### 🔗 Quick Links")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Main", width='stretch'):
            st.switch_page("main.py")
    
    with col2:
        if st.button("🎬 View Movies", width='stretch'):
            st.switch_page("pages/2_View_All_Movies.py")
    
    with col3:
        if st.button("🔍 Search", width='stretch'):
            st.switch_page("main.py")


if __name__ == "__main__":
    main()
