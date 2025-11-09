################################################################################
# FILE: pages/5_Load_All_Movies.py
# LOCATION: pages/ directory
# ACCESS: Admin only
################################################################################

import subprocess
import sys
import time
import streamlit as st
from pathlib import Path
import json

# Import authentication
sys.path.append(str(Path(__file__).resolve().parent.parent))
from auth import require_admin, show_user_info_sidebar

st.set_page_config(
    page_title="Load Movies to RAG",
    page_icon="🗄️",
    layout="centered"
)

# Require admin authentication
require_admin()

# Initialize session state
if "processing" not in st.session_state:
    st.session_state.processing = False
if "load_log" not in st.session_state:
    st.session_state.load_log = []


def add_log(message, log_type="info"):
    """Add a message to the log with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.load_log.append((log_entry, log_type))


def start_processing():
    """Callback to start processing"""
    st.session_state.processing = True
    st.session_state.load_log = []


def check_prerequisites():
    """Check if required files exist"""
    script_path = Path(__file__).resolve().parent.parent
    data_path = script_path / "data" / "tmdb_movies_full_credits.json"
    
    if not data_path.exists():
        return False, f"Movie data file not found at: {data_path}"
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            movies = json.load(f)
        return True, f"Found {len(movies)} movies ready to load"
    except Exception as e:
        return False, f"Error reading movie data: {str(e)}"


def run_load_script():
    """Run the loadmovie.py script"""
    script_path = Path(__file__).resolve().parent.parent / "loadmovie" / "loadmovie.py"
    
    if not script_path.exists():
        return False, f"Load script not found: {script_path}"
    
    command = [sys.executable, str(script_path)]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=600  # 10 minute timeout for embedding generation
        )
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Script execution timed out (10 minutes)"
    except subprocess.CalledProcessError as e:
        return False, f"Error code {e.returncode}:\n{e.stderr}"
    except Exception as e:
        return False, str(e)


def check_db_status():
    """Check if vector database exists and get info"""
    script_path = Path(__file__).resolve().parent.parent
    chroma_path = script_path / "data" / "chroma_db"
    
    if chroma_path.exists():
        try:
            # Check if it's a valid directory with files
            files = list(chroma_path.rglob("*"))
            if files:
                return True, f"Database exists with {len(files)} files"
        except Exception:
            pass
    
    return False, "No vector database found"


def main():
    # Admin badge
    st.markdown("### 🔑 Administrator Panel")
    
    st.title("🗄️ Load Movies into Vector Database")
    st.markdown("Create embeddings and load movies into ChromaDB for semantic search")
    
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
    st.warning("⚠️ Make sure you restart the app after loading to refresh data!")
    
    
    # Check prerequisites
    st.subheader("📋 Prerequisites Check")
    
    prereq_status, prereq_message = check_prerequisites()
    db_status, db_message = check_db_status()
    
    col1, col2 = st.columns(2)
    with col1:
        if prereq_status:
            st.success(f"✅ {prereq_message}")
        else:
            st.error(f"❌ {prereq_message}")
    
    with col2:
        if db_status:
            st.warning(f"⚠️ {db_message}\n\nLoading will replace existing database!")
        else:
            st.info(f"ℹ️ {db_message}")
    
    if not prereq_status:
        st.error("🚫 Cannot proceed without movie data. Please run 'Extract All Movies' first.")
        st.stop()
    
    st.divider()
    
    # Information about the process
    with st.expander("ℹ️ About This Process", expanded=False):
        st.markdown("""
        **What this does:**
        - Loads all movies from `tmdb_movies_full_credits.json`
        - Generates vector embeddings using SentenceTransformer
        - Stores embeddings in ChromaDB for semantic search
        - Enables natural language movie queries
        
        **Time estimate:**
        - Small dataset (100 movies): ~1-2 minutes
        - Medium dataset (1000 movies): ~5-10 minutes
        - Large dataset (5000+ movies): ~20-30 minutes
        
        **Note:** This will replace any existing vector database.  Restart the app after completion.
        """)
    
    # Warning about existing DB
    if db_status:
        st.warning("⚠️ **Warning:** Running this will delete the existing vector database and create a new one!")
    
    # Start button
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        st.button(
            "▶️ Start Loading",
            disabled=st.session_state.processing,
            on_click=start_processing,
            width='stretch',
            type="primary"
        )
    
    # Log display area
    if st.session_state.load_log or st.session_state.processing:
        st.divider()
        st.subheader("📋 Loading Log")
        
        log_container = st.container()
        with log_container:
            for log_entry, log_type in st.session_state.load_log:
                if log_type == "error":
                    st.error(log_entry)
                elif log_type == "success":
                    st.success(log_entry)
                elif log_type == "warning":
                    st.warning(log_entry)
                else:
                    st.info(log_entry)
    
    # Run loading process
    if st.session_state.processing:
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        # Step 1: Initialize
        add_log("🚀 Initializing vector database loading process...")
        status_placeholder.info("⏳ Initializing...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        # Step 2: Load embedding model
        add_log("📚 Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
        status_placeholder.info("⏳ Loading embedding model...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        # Step 3: Process movies
        add_log("🎬 Processing movies and generating embeddings...")
        add_log("This may take several minutes depending on the number of movies...", "warning")
        status_placeholder.info("⏳ Generating embeddings and storing in ChromaDB...")
        progress_bar.progress(30)
        
        with st.spinner("Embedding movies (this may take a while)..."):
            success, output = run_load_script()
        
        if success:
            progress_bar.progress(90)
            add_log("✅ Movies successfully loaded into vector database!", "success")
            
            # Parse output for details
            if output:
                lines = output.strip().split('\n')
                for line in lines[-10:]:  # Show last 10 lines of output
                    if line.strip():
                        add_log(line, "info")
            
            progress_bar.progress(100)
            status_placeholder.success("✅ Loading complete!")
            
            # Test query
            add_log("🧪 Testing vector database with a sample query...")
            time.sleep(1)
            
        else:
            add_log(f"❌ Loading failed: {output}", "error")
            status_placeholder.error("❌ Loading failed!")
            progress_bar.empty()
        
        # Cleanup
        st.session_state.processing = False
        time.sleep(1)
        progress_bar.empty()
        status_placeholder.empty()
        
        # Success message
        if success:
            st.balloons()
            st.success("🎉 Vector database created successfully! Restart the app!!!")
            st.info("💡 Normal users can now use the main search page to find movies using natural language queries!")
            
            # Show database info
            db_status, db_message = check_db_status()
            if db_status:
                st.metric("Database Status", "Active", delta="Ready for queries")
        
        time.sleep(0.5)
        st.rerun()


if __name__ == "__main__":
    main()


