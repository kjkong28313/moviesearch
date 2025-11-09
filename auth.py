################################################################################
# FILE: auth.py
# LOCATION: Root directory
################################################################################

"""
Authentication System for Movie Recommendation App
Handles user login with normal and admin roles
"""

import streamlit as st
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timedelta

# Hard-coded credentials (username: password)
CREDENTIALS = {
    "admin": {
        "password": "admin321",
        "role": "admin",
        "name": "Administrator"
    },
    "user": {
        "password": "user321",
        "role": "normal",
        "name": "User"
    }
}

# Session timeout (in minutes)
SESSION_TIMEOUT = 60


def hash_password(password: str) -> str:
    """
    Hash password using SHA256
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify user credentials
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Tuple of (success, role, name)
    """
    if username in CREDENTIALS:
        user_data = CREDENTIALS[username]
        if password == user_data["password"]:
            return True, user_data["role"], user_data["name"]
    return False, None, None


def initialize_session_state():
    """Initialize authentication-related session state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "login_time" not in st.session_state:
        st.session_state.login_time = None


def check_session_timeout() -> bool:
    """
    Check if session has timed out
    
    Returns:
        True if session is valid, False if timed out
    """
    if st.session_state.login_time:
        elapsed = datetime.now() - st.session_state.login_time
        if elapsed > timedelta(minutes=SESSION_TIMEOUT):
            logout()
            return False
    return True


def login(username: str, password: str) -> bool:
    """
    Attempt to log in user
    
    Args:
        username: Username
        password: Password
        
    Returns:
        True if login successful, False otherwise
    """
    success, role, name = verify_credentials(username, password)
    
    if success:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = role
        st.session_state.user_name = name
        st.session_state.login_time = datetime.now()
        return True
    return False


def logout():
    """Log out current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.user_name = None
    st.session_state.login_time = None


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """Check if current user is admin"""
    return st.session_state.get("role") == "admin"


def is_normal_user() -> bool:
    """Check if current user is normal user"""
    return st.session_state.get("role") == "normal"


def get_current_user() -> Optional[str]:
    """Get current username"""
    return st.session_state.get("username")


def get_user_display_name() -> Optional[str]:
    """Get current user's display name"""
    return st.session_state.get("user_name")


def require_auth():
    """
    Decorator/function to require authentication
    Redirects to login if not authenticated
    """
    initialize_session_state()
    
    if not is_authenticated():
        show_login_page()
        st.stop()
    
    # Check session timeout
    if not check_session_timeout():
        st.warning("⚠️ Your session has expired. Please login again.")
        show_login_page()
        st.stop()


def require_admin():
    """
    Require admin role
    Shows error if not admin
    """
    require_auth()
    
    if not is_admin():
        st.error("🚫 Access Denied: Admin privileges required")
        st.info("This page is only accessible to administrators.")
        st.stop()


def show_login_page():
    """Display login page"""
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-header">🎬 Movie System</div>', unsafe_allow_html=True)
        st.markdown("### 🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                else:
                    if login(username, password):
                        st.success(f"✅ Welcome, {get_user_display_name()}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
        
        # Show demo credentials
        with st.expander("ℹ️ Demo Credentials", expanded=True):
            st.markdown("""
            **Normal User:**
            - Username: `user`
            
            **Administrator:**
            - Username: `admin`
            """)


def show_user_info_sidebar():
    """Display user information in sidebar"""
    if is_authenticated():
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Information")
            
            # User details
            col1, col2 = st.columns([1, 2])
            with col1:
                if is_admin():
                    st.markdown("**Role:**")
                    st.markdown("**User:**")
                else:
                    st.markdown("**Role:**")
                    st.markdown("**User:**")
            
            with col2:
                role_badge = "🔑 Admin" if is_admin() else "👤 Normal"
                st.markdown(f"{role_badge}")
                st.markdown(f"{get_user_display_name()}")
            
            # Session info
            if st.session_state.login_time:
                elapsed = datetime.now() - st.session_state.login_time
                remaining = SESSION_TIMEOUT - int(elapsed.total_seconds() / 60)
                if remaining > 0:
                    st.caption(f"⏱️ Session: {remaining} min remaining")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()


def get_allowed_pages() -> list:
    """
    Get list of pages user can access based on role
    
    Returns:
        List of page names
    """
    if is_admin():
        return [
            "main.py",
            "pages/2_View_All_Movies.py",
            "pages/3_About_Us.py",
            "pages/4_Extract_All_Movies.py",
            "pages/5_Load_All_Movies.py"
        ]
    elif is_normal_user():
        return [
            "main.py",
            "pages/2_View_All_Movies.py",
            "pages/3_About_Us.py"
        ]
    return []


def check_page_access(current_page: str) -> bool:
    """
    Check if user has access to current page
    
    Args:
        current_page: Current page name/path
        
    Returns:
        True if user has access
    """
    if not is_authenticated():
        return False
    
    allowed_pages = get_allowed_pages()
    
    # Check if current page is in allowed pages
    for allowed in allowed_pages:
        if current_page in allowed or allowed in current_page:
            return True
    
    return False


def show_access_denied():
    """Show access denied page"""
    st.error("🚫 Access Denied")
    st.warning("You don't have permission to access this page.")
    
    st.info(f"""
    **Your Role:** {st.session_state.role.title()}
    
    **Available Pages:**
    - 🏠 Home (Main Search)
    - 🎬 View All Movies
    - ℹ️ About Us
    {'- 🔧 Extract All Movies (Admin Only)\n- 🗄️ Load All Movies (Admin Only)' if not is_admin() else ''}
    """)
    
    if st.button("🏠 Go to Home"):
        st.switch_page("main.py")

