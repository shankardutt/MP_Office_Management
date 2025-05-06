"""
Main application file for Office Room Allocation System
"""

import os
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Import configuration and modules
import config
import auth
from data_manager import load_data, save_data, create_system_manager
from utils import apply_custom_css


# Set page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # File Upload/Selection
    st.header("Data Source")
    uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])
    
    if uploaded_file is not None:
        # Save the uploaded file
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
        occupant_manager, room_manager = create_system_manager(st.session_state.file_path)
        st.session_state.occupant_manager = occupant_manager
        st.session_state.room_manager = room_manager
    
    # Get managers from session state
    occupant_manager = st.session_state.occupant_manager
    room_manager = st.session_state.room_manager
    
    # Filters
    st.header("Filters")
    buildings = ['All'] + occupant_manager.get_unique_buildings()
    st.session_state.filter_building = st.selectbox("Building", buildings, key="sidebar_building_filter")
    
    # Navigation
    st.header("Navigation")
    page = st.radio("Go to", [
        "Dashboard", 
        "Current Occupants", 
        "Upcoming Occupants",
        "Room Management", 
        "Reports"
    ], key="main_navigation")
    
    # Save button with improved data validation
    st.header("Actions")
    if st.button("💾 Save Changes", key="save_changes_btn"):
        # Add ignore warnings checkbox
        st.session_state.ignore_warnings = st.checkbox("Ignore warnings", value=False, key="ignore_warnings_checkbox")
        
        # Execute save action
        from utils import save_action
        success, message = save_action(occupant_manager, room_manager, st.session_state.file_path)
        
        if success:
            st.success(message)
        else:
            if isinstance(message, list):
                for msg in message:
                    st.warning(msg)
                st.error("Please fix the issues above or check 'Ignore warnings' to proceed.")
            else:
                st.error(message)
    
    # Add data backup button
    if st.button("📦 Create Backup", key="create_backup_btn"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'{config.BACKUP_DIR}/MP_Office_Allocation_{timestamp}.xlsx'
        
        current_df = occupant_manager.get_current_occupants()
        upcoming_df = occupant_manager.get_upcoming_occupants()
        past_df = occupant_manager.get_past_occupants()
        
        try:
            with pd.ExcelWriter(backup_path) as writer:
                current_df.to_excel(writer, sheet_name='Current', index=False)
                upcoming_df.to_excel(writer, sheet_name='Upcoming', index=False)
                past_df.to_excel(writer, sheet_name='Past', index=False)
            
            st.success(f"Backup created: {backup_path}")
        except Exception as e:
            st.error(f"Error creating backup: {e}")
    
    # Display last save time
    if st.session_state.last_save:
        st.info(f"Last saved: {st.session_state.last_save}")
    
    st.markdown("---")
    st.caption(f"Office Room Allocation System v{config.APP_VERSION}")


# Import and display appropriate page based on navigation selection
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