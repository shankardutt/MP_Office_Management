"""
Main application file for Office Room Allocation System
"""

import os
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import io

# Import configuration and modules
import config
import auth
from data_manager import load_data, save_data, create_system_manager, get_data_as_excel
from utils import apply_custom_css, save_action

# This MUST be the first Streamlit command
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now we can use st.sidebar
debug_container = st.sidebar.empty()

# Import GitHub integration if available
try:
    from github_integration import init_github_integration, show_github_settings
    from github_verification import verify_github_setup
    GITHUB_AVAILABLE = True
    debug_container.success("GitHub modules loaded successfully!")
except ImportError as e:
    GITHUB_AVAILABLE = False
    debug_container.error(f"GitHub modules not available: {str(e)}")

# Hide both the default navigation and the redundant menu items
st.markdown("""
<style>
/* Hide the default Streamlit navigation */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
div.block-container {padding-top: 1rem;}

/* Hide the redundant navigation elements from the sidebar */
[data-testid="stSidebarNavItems"] {
    display: none;
}
ul.css-sbjmkt {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# Apply custom CSS
apply_custom_css()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.file_path = config.DEFAULT_EXCEL_PATH
    st.session_state.filter_building = 'All'
    st.session_state.last_save = None
    st.session_state.ignore_warnings = False
    st.session_state.use_github = False
    
    # Initialize GitHub integration if available
    if GITHUB_AVAILABLE:
        init_github_integration()

# Authentication check
if not auth.authenticate():
    # If not authenticated, stop here
    st.stop()

# Display session info and logout button
auth.show_session_info()
auth.add_logout_button()

# Sidebar - Settings and Filters
with st.sidebar:
    st.image(config.SIDEBAR_ICON, width=100)
    st.title("Room Allocation System")
    
    # GitHub Integration Settings
    if GITHUB_AVAILABLE:
        with st.expander("🔄 GitHub Integration", expanded=True):
            st.write("GitHub integration enables persistent data storage.")
            st.session_state.use_github = st.checkbox(
                "Enable GitHub Storage",
                value=st.session_state.use_github,
                help="Save and load data from GitHub",
                key="use_github_checkbox"
            )
            
            if st.session_state.use_github:
                if st.button("Test GitHub Connection", key="test_github_btn"):
                    st.info("Testing GitHub connection...")
                    # This will be handled by the show_github_settings() function
                    # when it's available
                
                if st.button("🔍 Verify GitHub Setup", key="verify_github_btn"):
                    if 'occupant_manager' in st.session_state and 'room_manager' in st.session_state:
                        with st.spinner("Verifying GitHub setup..."):
                            status, message = verify_github_setup(
                                st.session_state.occupant_manager,
                                st.session_state.room_manager
                            )
                            
                            if status:
                                st.success("✅ GitHub integration verified successfully!")
                                st.info(message)
                            else:
                                st.error(f"❌ GitHub verification failed: {message}")
                    else:
                        st.error("Cannot verify GitHub setup before data is loaded")
                
                if st.button("📤 Save Initial Data to GitHub", key="save_initial_data_btn"):
                    if 'occupant_manager' in st.session_state and 'room_manager' in st.session_state:
                        with st.spinner("Saving initial data to GitHub..."):
                            # Get current dataframes
                            current_df = st.session_state.occupant_manager.get_current_occupants()
                            upcoming_df = st.session_state.occupant_manager.get_upcoming_occupants()
                            past_df = st.session_state.occupant_manager.get_past_occupants()
                            room_capacities = st.session_state.room_manager.room_capacities
                            
                            # Save data to GitHub
                            success = save_data(
                                current_df,
                                upcoming_df,
                                past_df,
                                st.session_state.file_path,
                                room_capacities,
                                use_github=True
                            )
                            
                            if success:
                                st.success("✅ Initial data saved to GitHub successfully!")
                                # Update last_save timestamp
                                st.session_state.last_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                st.error("❌ Failed to save initial data to GitHub")
                    else:
                        st.error("Cannot save to GitHub before data is loaded")
        
        # Now attempt to show GitHub settings separately (outside the expander)
        try:
            show_github_settings()
        except Exception as e:
            st.error(f"Error showing GitHub settings: {str(e)}")
    
    # File Upload/Selection
    st.header("Data Source")
    uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'], key="excel_file_uploader")
    
    if uploaded_file is not None:
        # Save the uploaded file
        os.makedirs('data', exist_ok=True)  # Ensure data directory exists
        with open('data/temp_upload.xlsx', 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        st.session_state.file_path = 'data/temp_upload.xlsx'
        
        # Reset managers with new data
        if 'occupant_manager' in st.session_state:
            del st.session_state.occupant_manager
        if 'room_manager' in st.session_state:
            del st.session_state.room_manager
            
        st.success("File uploaded successfully!")
        st.rerun()
    
    # Create managers if not in session state
    if 'occupant_manager' not in st.session_state or 'room_manager' not in st.session_state:
        try:
            occupant_manager, room_manager = create_system_manager(
                st.session_state.file_path, 
                st.session_state.use_github if GITHUB_AVAILABLE else False
            )
            st.session_state.occupant_manager = occupant_manager
            st.session_state.room_manager = room_manager
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.info("If this is your first time, upload an Excel file to get started")
    
    # Get managers from session state
    if 'occupant_manager' in st.session_state and 'room_manager' in st.session_state:
        occupant_manager = st.session_state.occupant_manager
        room_manager = st.session_state.room_manager
    
        # Filters
        st.header("Filters")
        buildings = ['All'] + occupant_manager.get_unique_buildings()
        st.session_state.filter_building = st.selectbox(
            "Building", 
            buildings, 
            key="sidebar_building_filter"
        )
        
        # Navigation
        st.header("Navigation")
        page = st.radio(
            "Go to", 
            ["Dashboard", "Current Occupants", "Upcoming Occupants", "Room Management", "Reports"],
            key="main_navigation"
        )
        
        # Save button with improved data validation
        st.header("Actions")
        if st.button("💾 Save Changes", key="save_changes_btn"):
            # Add ignore warnings checkbox
            st.session_state.ignore_warnings = st.checkbox(
                "Ignore warnings", 
                value=False, 
                key="ignore_warnings_checkbox"
            )
            
            # Execute save action
            success, message = save_action(
                occupant_manager, 
                room_manager, 
                st.session_state.file_path,
                use_github=st.session_state.use_github if GITHUB_AVAILABLE else False
            )
            
            if success:
                st.success(message)
            else:
                if isinstance(message, list):
                    for msg in message:
                        st.warning(msg)
                    st.error("Please fix the issues above or check 'Ignore warnings' to proceed.")
                else:
                    st.error(message)
        
        # Add data backup and download button
        if st.button("📦 Create Backup", key="create_backup_btn"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f'MP_Office_Allocation_{timestamp}.xlsx'
            
            try:
                # Get Excel data as bytes
                excel_data = get_data_as_excel(occupant_manager, room_manager)
                
                if excel_data:
                    # Offer the file for download
                    st.download_button(
                        label="📥 Download Backup File",
                        data=excel_data,
                        file_name=backup_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_backup_btn"
                    )
                    
                    st.success(f"Backup '{backup_filename}' ready for download")
                else:
                    st.error("Error creating backup")
            except Exception as e:
                st.error(f"Error creating backup: {e}")
        
        # Display last save time
        if st.session_state.last_save:
            st.info(f"Last saved: {st.session_state.last_save}")
    else:
        st.warning("No data loaded. Please upload an Excel file to get started.")
        # Set a default page for when no data is loaded
        page = "Dashboard"
    
    st.markdown("---")
    st.caption(f"Office Room Allocation System v{config.APP_VERSION}")

# Import and display appropriate page based on navigation selection
if 'occupant_manager' in st.session_state and 'room_manager' in st.session_state:
    if page == "Dashboard":
        from pages.dashboard import show_dashboard
        show_dashboard(st.session_state.occupant_manager, st.session_state.room_manager)
        
    elif page == "Current Occupants":
        from pages.current_occupants import show_current_occupants
        show_current_occupants(st.session_state.occupant_manager, st.session_state.room_manager)
        
    elif page == "Upcoming Occupants":
        from pages.upcoming_occupants import show_upcoming_occupants
        show_upcoming_occupants(st.session_state.occupant_manager, st.session_state.room_manager)
        
    elif page == "Room Management":
        from pages.room_management import show_room_management
        show_room_management(st.session_state.occupant_manager, st.session_state.room_manager)
        
    elif page == "Reports":
        from pages.reports import show_reports
        show_reports(st.session_state.occupant_manager, st.session_state.room_manager)
else:
    st.title("Office Room Allocation System")
    st.write("Welcome to the Office Room Allocation System!")
    st.write("Please upload an Excel file to get started, or use the default data if available.")
    
    # Display some initial instructions
    st.info("""
    **Getting Started:**
    1. Use the sidebar to upload your Excel file with occupant data
    2. Navigate through the different sections using the sidebar menu
    3. Make changes and save them using the 'Save Changes' button
    4. Create backups regularly to avoid data loss
    """)
    
    # Show GitHub info if available
    if GITHUB_AVAILABLE:
        st.success("""
        **GitHub Integration Available:**
        GitHub integration allows you to store your data securely in a GitHub repository,
        ensuring it persists between sessions. Enable it in the sidebar to get started.
        """)