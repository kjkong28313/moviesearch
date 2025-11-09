################################################################################
# FILE: pages/4_Extract_All_Movies.py
# LOCATION: pages/ directory
# ACCESS: Admin only
################################################################################

import subprocess
import sys
import time
import streamlit as st
from pathlib import Path

# Log area
log_area = st.empty()
def log(msg):
    log_area.text(msg)


# Import authentication
sys.path.append(str(Path(__file__).resolve().parent.parent))
from auth import require_admin, show_user_info_sidebar

st.set_page_config(
    page_title="Extract Movies",
    page_icon="🎬",
    layout="centered"
)

# Require admin authentication
require_admin()

# Initialize session state
if "processing" not in st.session_state:
    st.session_state.processing = False
if "extraction_log" not in st.session_state:
    st.session_state.extraction_log = []


def add_log(message, log_type="info"):
    """Add a message to the log with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.extraction_log.append((log_entry, log_type))


def start_processing():
    """Callback to start processing"""
    st.session_state.processing = True
    st.session_state.extraction_log = []


def run_script(script_name, args=None):
    """Run a Python script and return the result"""
    script_path = Path(__file__).resolve().parent.parent / "extractmovie" / script_name
    
    if not script_path.exists():
        return False, f"Script not found: {script_path}"
    #add_log(str(script_path))    
    command = [sys.executable, str(script_path)]
    if args:
        command.extend([str(arg) for arg in args])
    
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=3000  # 5 minute timeout
        )
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Script execution timed out (5 minutes)"
    except subprocess.CalledProcessError as e:
        return False, f"Error code {e.returncode}:\n{e.stderr}"
    except Exception as e:
        return False, str(e)


def main():
    # Admin badge
    st.markdown("### 🔑 Administrator Panel")
    
    st.title("🎬 Extract Movies from TMDB")
    st.markdown("Fetch movie data from The Movie Database API and build search indexes")
    
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
    
    # Warning about API usage
    #st.warning("⚠️ Make sure you restart the app after extraction to refresh data!")
    
    # Configuration
    st.subheader("⚙️ Configuration")
    max_pages = st.number_input(
        "Maximum pages per genre to fetch:",
        min_value=1,
        max_value=100,
        value=1,
        step=1,
        help="Each page contains ~20 movies. Total movies = pages × number of genres × 20"
    )
    
    # Estimated movies
    estimated_movies = max_pages * 19 * 20  # 19 genres, ~20 movies per page
    st.info(f"📊 Estimated movies to fetch: ~{estimated_movies:,}")
    
    # Start button
    col1, col2 = st.columns([1, 3])
    with col1:
        st.button(
            "▶️ Start Extraction",
            disabled=st.session_state.processing,
            on_click=start_processing,
            width='stretch'
        )
    
    # Log display area
    if st.session_state.extraction_log or st.session_state.processing:
        st.divider()
        st.subheader("📋 Extraction Log")
        
        log_container = st.container()
        with log_container:
            for log_entry, log_type in st.session_state.extraction_log:
                if log_type == "error":
                    st.error(log_entry)
                elif log_type == "success":
                    st.success(log_entry)
                elif log_type == "warning":
                    st.warning(log_entry)
                else:
                    st.info(log_entry)
    
    # Run extraction process
    if st.session_state.processing:
        progress_bar = st.progress(0)
        
        # Step 1: Extract movies
        add_log("🎬 Starting movie extraction from TMDB...")
        progress_bar.progress(10)
        
        with st.spinner("Fetching movies from TMDB API..."):
            success, output = run_script("extractmovie.py", [max_pages])
        
        if success:
            add_log("✅ Movie extraction completed successfully!", "success")
            if output:
                add_log(f"Output: {output[:500]}...", "info")
            progress_bar.progress(50)
        else:
            add_log(f"❌ Movie extraction failed: {output}", "error")
            st.session_state.processing = False
            progress_bar.empty()
            st.stop()
        
        time.sleep(1)
        
        # Step 2: Build indexes
        add_log("🔨 Building search indexes...")
        progress_bar.progress(60)
        
        with st.spinner("Creating actor, director, genre, and year indexes..."):
            success, output = run_script("createindexes.py")
        
        if success:
            add_log("✅ Index building completed successfully!", "success")
            if output:
                add_log(f"Output: {output[:500]}...", "info")
            progress_bar.progress(100)
        else:
            add_log(f"❌ Index building failed: {output}", "error")
        
        # Cleanup
        st.session_state.processing = False
        progress_bar.empty()
        
        # Success message
        if success:
            st.balloons()
            st.success("🎉 All tasks completed successfully!")
            st.info("💡 Next step: Go to 'Load All Movies' page to create the vector database for semantic search.")
        
        time.sleep(0.5)
        st.rerun()


if __name__ == "__main__":
    main()

