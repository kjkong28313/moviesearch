################################################################################
# FILE: main.py
# LOCATION: Root directory
################################################################################

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from contextlib import contextmanager

# Import authentication
from auth import require_auth, show_user_info_sidebar, is_authenticated

from agent.agent import (
    MovieSearchAgent, 
    MovieRecommenderAgent, 
    MovieOrchestrator, 
    parse_json_recommendations, 
    MovieOfferAgent
)

# Suppress transformer warnings
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
from transformers import logging
logging.set_verbosity_error()

# Page configuration
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Require authentication
require_auth()

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
    }
    .search-instructions {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_orchestrator():
    """Initialize and cache the orchestrator to avoid reloading models"""
    with st.spinner("🎬 Loading movie recommendation system..."):
        search_agent = MovieSearchAgent()
        recommender_agent = MovieRecommenderAgent(model="llama3.2:latest")
        return MovieOrchestrator(search_agent, recommender_agent)


@contextmanager
def st_loading(message):
    """Context manager for loading states"""
    placeholder = st.empty()
    with placeholder:
        with st.spinner(message):
            yield
    placeholder.empty()


def display_movie_recommendations(recommendations):
    """Display movie recommendations in a formatted way"""
    if not recommendations:
        st.warning("⚠️ No valid recommendations found.")
        return []
    
    enriched_rows = []
    for idx, rec in enumerate(recommendations, start=1):
        title = rec.get("title", "").strip()
        if not title:
            continue
            
        enriched_rows.append({
            "#": idx,
            "Title": title,
            "Genres": rec.get("genres", "N/A"),
            "Director": rec.get("director", "N/A"),
            "Cast": rec.get("actors", "N/A"),
            "Release Date": rec.get("release_date", "N/A"),
            "Rating": rec.get("rating", "N/A"),
            "Overview": rec.get("overview", "")[:300] + "..." if len(rec.get("overview", "")) > 300 else rec.get("overview", ""),
            "Reason": rec.get("reason", "No reason provided")
        })
    
    if enriched_rows:
        st.markdown("### 🎬 Recommended Movies")
        df_meta = pd.DataFrame(enriched_rows)
        st.dataframe(
            df_meta,
            width='stretch',
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn("Rank", width="small"),
                "Rating": st.column_config.NumberColumn("Rating", format="⭐ %.1f"),
                "Overview": st.column_config.TextColumn("Overview", width="large"),
            }
        )
    
    return enriched_rows


def display_movie_offers(recommendations, serpapi_key):
    """Display available offers for each movie"""
    if not recommendations or not serpapi_key:
        return
    
    offer_agent = MovieOfferAgent(serpapi_key=serpapi_key)
    
    st.markdown("### 🎯 Where to Watch")
    
    for idx, rec in enumerate(recommendations, start=1):
        title = rec.get("title", "").strip()
        reason = rec.get("reason", "No reason provided")
        
        if not title:
            continue
        
        with st.expander(f"🎬 {title}", expanded=(idx == 1)):
            st.markdown(f"**Why recommended:** {reason}")
            
            with st_loading(f"Searching offers for '{title}'..."):
                offers = offer_agent.search_offers(title)
            
            valid_offers = [o for o in (offers or []) if isinstance(o, dict) and any(o.values())]
            
            if valid_offers:
                for offer in valid_offers:
                    url = offer.get("URL", "")
                    if url:
                        offer["URL"] = f"[Watch here]({url})"
                
                df_offer = pd.DataFrame(valid_offers)
                cols_to_display = ["Platform", "Format", "Rent", "Buy", "Costs", "URL"]
                df_offer = df_offer[[col for col in cols_to_display if col in df_offer.columns]]
                st.markdown(df_offer.to_markdown(index=False), unsafe_allow_html=True)
            else:
                st.info("No offers found for this movie.")


def main():

    if load_dotenv('.env'):
    # for local development
        serpapi_key = os.getenv('SERAPI_KEY')
    else:
        serpapi_key = os.environ['SERAPI_KEY']

    # Header
    st.markdown('<h1 class="main-header">🎬 Movie Recommendation System</h1>', unsafe_allow_html=True)
    
    # Initialize orchestrator
    orchestrator = initialize_orchestrator()
    
    # Sidebar for settings and user info
    with st.sidebar:
        st.markdown("### ℹ️ About")
        st.markdown("""
        This app helps you find movies based on:
        - Semantic search (themes, plots)
        - Criteria search (actors, directors, year)
        - Combined searches
        """)
    
    # Show user info in sidebar
    show_user_info_sidebar()
    
    # Search instructions
    with st.expander("📖 How to Search", expanded=False):
        st.markdown("""
        **Search Syntax:**
        
        **Structured Criteria:**
        - `acted by <actor>` | `starring <actor>` | `featuring <actor>`
        - `directed by <director>` | `by director <director>`
        - `produced by <company>` | `production <company>` | `distributed by <company>`
        - `genre is <genre>` | `genre in <genre>` | `type is <genre>`
        - `after <year>` | `before <year>` | `in <year>`
        
        **Examples:**
        - Semantic: `"story about family love"`
        - Criteria: `"starring tom cruise AND in 2025"`
        - Combined: `"story about family love AND in 2025"`
        """)
    
    # Search form
    with st.form(key="search_form", clear_on_submit=False):
        user_prompt = st.text_area(
            "Enter your movie search query:",
            height=100,
            placeholder="Example: story about family love AND starring tom hanks",
            help="Combine semantic descriptions with structured criteria using AND"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            submitted = st.form_submit_button("🔍 Search", width="stretch")
        with col2:
            cleared = st.form_submit_button("🗑️ Clear", width="stretch")
    
    if cleared:
        st.rerun()
    
    if submitted and user_prompt.strip():
        st.toast(f"🎬 Searching for: {user_prompt}")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Search phase
            status_text.text("🔍 Searching movies...")
            progress_bar.progress(30)
            
            response = orchestrator.run(user_prompt)
            progress_bar.progress(60)
            
            # Parse recommendations
            status_text.text("📊 Processing recommendations...")
            recommendations = []
            if response:
                recommendations = parse_json_recommendations(response)
            progress_bar.progress(80)
            
            # Clear progress indicators
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()
            
            # Display results
            st.divider()
            
            if not recommendations:
                st.warning("⚠️ No movies found matching your criteria. Try adjusting your search.")
            else:
                # Display recommendations
                enriched_rows = display_movie_recommendations(recommendations)
                
                # Display offers if API key is provided
                if serpapi_key:
                    display_movie_offers(recommendations, serpapi_key)
                else:
                    st.info("💡 Add your SerpAPI key in the sidebar to see where to watch these movies!")
                    
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.exception(e)
    
    elif submitted:
        st.warning("⚠️ Please enter a search query.")


if __name__ == "__main__":
    main()


