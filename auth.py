"""
Authentication functionality for the Office Room Allocation System
"""

import datetime
import hashlib
import streamlit as st

import config


def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password):
    """Check if provided password is correct"""
    correct_password_hash = hash_password(config.DEFAULT_PASSWORD)
    password_hash = hash_password(password)
    return password_hash == correct_password_hash


def check_session_timeout():
    """Check if session has timed out"""
    # Get the current time
    current_time = datetime.datetime.now()
    
    # Check if login_time exists in session state
    if 'login_time' in st.session_state:
        # Calculate time difference in minutes
        time_diff = current_time - st.session_state.login_time
        minutes_diff = time_diff.total_seconds() / 60
        
        # If more than configured timeout minutes has passed, session has timed out
        if minutes_diff > config.SESSION_TIMEOUT_MINUTES:
            st.session_state.is_authenticated = False
            st.session_state.pop('login_time', None)
            return True
    
    return False


def show_login_form():
    """Display login form"""
    st.title("Office Room Allocation System - Login")
    st.markdown("Please enter the password to access the system.")
    
    # Create login form
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if check_password(password):
                # Set authentication status and login time
                st.session_state.is_authenticated = True
                st.session_state.login_time = datetime.datetime.now()
                st.success("Login successful!")
                # Add a rerun to refresh the page after successful login
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")


def authenticate():
    """Authenticate user and manage session"""
    # Check if already authenticated and session hasn't timed out
    if 'is_authenticated' in st.session_state and st.session_state.is_authenticated:
        # Check if session has timed out
        if check_session_timeout():
            st.warning("Your session has timed out. Please log in again.")
            # Show login form again
            show_login_form()
            return False
        else:
            # User is authenticated and session is still valid
            return True
    else:
        # User is not authenticated, show login form
        show_login_form()
        return False


def show_session_info():
    """Display session information in sidebar"""
    if 'login_time' in st.session_state:
        current_time = datetime.datetime.now()
        time_diff = current_time - st.session_state.login_time
        remaining_minutes = max(0, config.SESSION_TIMEOUT_MINUTES - (time_diff.total_seconds() / 60))
        
        # Display a message when less than 10 minutes are remaining
        if remaining_minutes < 10:
            st.sidebar.warning(f"⚠️ Session expires in {int(remaining_minutes)} minutes")
        else:
            st.sidebar.info(f"Session time remaining: {int(remaining_minutes)} minutes")


def logout():
    """Log user out"""
    # Clear authentication status
    st.session_state.is_authenticated = False
    if 'login_time' in st.session_state:
        del st.session_state.login_time
    st.sidebar.success("Logged out successfully!")
    # Rerun the app to show login form
    st.rerun()


def add_logout_button():
    """Add logout button to sidebar"""
    if st.sidebar.button("Logout"):
        logout()