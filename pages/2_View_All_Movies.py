################################################################################
# FILE: pages/2_View_All_Movies.py
# LOCATION: pages/ directory
################################################################################

import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Import authentication
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from auth import require_auth, show_user_info_sidebar

# Page config
st.set_page_config(
    page_title="View All Movies",
    page_icon="🎬",
    layout="wide"
)

# Require authentication
require_auth()

@st.cache_data
def load_movies():
    """Load movies from JSON file with caching"""
    script_path = Path(__file__).resolve().parent.parent
    filepath = script_path / "data" / "tmdb_movies_full_credits.json"
    
    try:
        with open(filepath, 'r', encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"❌ Movie data file not found at: {filepath}")
        st.info("Please contact administrator to generate the data.")
        return []
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format in movie data file.")
        return []


def main():
    st.title("🎬 All Movies Database")
    st.markdown("Browse all movies in the database")
    
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
    
    # Load data
    with st.spinner("Loading movie data..."):
        list_of_movies = load_movies()
    
    if not list_of_movies:
        st.stop()
    
    df = pd.DataFrame(list_of_movies)
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Movies", len(df))
    with col2:
        if 'genres' in df.columns:
            unique_genres = set()
            for genres in df['genres']:
                if isinstance(genres, list):
                    unique_genres.update(genres)
            st.metric("Unique Genres", len(unique_genres))
    with col3:
        if 'director' in df.columns:
            st.metric("Unique Directors", df['director'].nunique())
    with col4:
        if 'release_date' in df.columns:
            years = df['release_date'].str[:4]
            st.metric("Year Range", f"{years.min()}-{years.max()}")
    
    st.divider()
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'genres' in df.columns:
            all_genres = set()
            for genres in df['genres']:
                if isinstance(genres, list):
                    all_genres.update(genres)
            selected_genres = st.multiselect("Filter by Genre", sorted(all_genres))
    
    with col2:
        if 'release_date' in df.columns:
            years = df['release_date'].str[:4].astype(str)
            year_range = st.slider(
                "Release Year Range",
                min_value=int(years.min()) if years.min().isdigit() else 1900,
                max_value=int(years.max()) if years.max().isdigit() else 2025,
                value=(int(years.min()) if years.min().isdigit() else 1900, 
                       int(years.max()) if years.max().isdigit() else 2025)
            )
    
    with col3:
        if 'rating' in df.columns:
            min_rating = st.slider("Minimum Rating", 0.0, 10.0, 0.0, 0.5)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_genres:
        filtered_df = filtered_df[filtered_df['genres'].apply(
            lambda x: any(g in selected_genres for g in x) if isinstance(x, list) else False
        )]
    
    if 'release_date' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['release_date'].str[:4].astype(int) >= year_range[0]) &
            (filtered_df['release_date'].str[:4].astype(int) <= year_range[1])
        ]
    
    if 'rating' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['rating'] >= min_rating]
    
    # Search box
    search_term = st.text_input("🔎 Search by title, director, or actor:")
    if search_term:
        mask = (
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['director'].str.contains(search_term, case=False, na=False) |
            filtered_df['actors'].apply(
                lambda x: search_term.lower() in str(x).lower() if x else False
            )
        )
        filtered_df = filtered_df[mask]
    
    st.divider()
    
    # Display results
    st.subheader(f"📊 Results ({len(filtered_df)} movies)")
    
    if len(filtered_df) > 0:
        # Configure column display
        column_config = {
            "title": st.column_config.TextColumn("Title", width="medium"),
            "release_date": st.column_config.TextColumn("Release Date", width="small"),
            "rating": st.column_config.NumberColumn("Rating", format="⭐ %.1f", width="small"),
            "genres": st.column_config.ListColumn("Genres", width="medium"),
            "director": st.column_config.TextColumn("Director", width="medium"),
            "actors": st.column_config.ListColumn("Actors", width="large"),
            "overview": st.column_config.TextColumn("Overview", width="large"),
        }
        
        # Select columns to display
        display_columns = st.multiselect(
            "Select columns to display:",
            options=filtered_df.columns.tolist(),
            default=['title', 'release_date', 'rating', 'genres', 'director']
        )
        
        if display_columns:
            st.dataframe(
                filtered_df[display_columns],
                width='stretch',
                hide_index=True,
                column_config=column_config
            )
        
        # Download option
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download filtered data as CSV",
            data=csv,
            file_name="filtered_movies.csv",
            mime="text/csv"
        )
    else:
        st.info("No movies match your filters. Try adjusting the criteria.")


if __name__ == "__main__":
    main()


