"""
Data loading, saving, and manipulation functions
"""

import os
import json
import shutil
import pandas as pd
import io
from datetime import datetime

import config
from models import OccupantManager, RoomManager

# Import GitHub integration if available
try:
    from github_integration import save_to_github, load_from_github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

def verify_github_setup(occupant_manager, room_manager):
    """
    Verify GitHub setup by checking if we can access and save files.
    This function will check if the essential files exist in the GitHub repository
    and create them if they don't.
    
    Args:
        occupant_manager: The occupant manager instance
        room_manager: The room manager instance
        
    Returns:
        (status, message): A tuple with the status (True for success) and a message
    """
    import streamlit as st
    import pandas as pd
    import io
    import json
    
    try:
        # Check if GitHub integration is available and enabled
        if 'use_github' not in st.session_state or not st.session_state.use_github:
            return False, "GitHub integration is not enabled"
            
        # Import GitHub functions - ensure they're available
        try:
            from github_integration import load_from_github, save_to_github
        except ImportError:
            return False, "GitHub integration module not available"
        
        # Step 1: Try to load the Excel file
        excel_content = load_from_github("MP_Office_Allocation.xlsx")
        excel_exists = excel_content is not None
        
        # Step 2: Try to load the room capacities
        capacities_content = load_from_github("room_capacities.json")
        capacities_exist = capacities_content is not None
        
        # Step 3: Create status message
        status_msgs = []
        
        if excel_exists:
            status_msgs.append("Excel file found in GitHub repository")
        else:
            status_msgs.append("Excel file not found in GitHub repository - will be created on first save")
        
        if capacities_exist:
            status_msgs.append("Room capacities found in GitHub repository")
        else:
            status_msgs.append("Room capacities not found in GitHub repository - will be created on first save")
        
        # Step 4: Create test file to verify write access
        test_content = json.dumps({"test": "This is a test file", "timestamp": str(pd.Timestamp.now())})
        
        success, message = save_to_github(
            "github_test.json",
            test_content,
            "Test file to verify GitHub write access"
        )
        
        if success:
            status_msgs.append("Successfully created test file in GitHub repository")
            overall_status = True
        else:
            status_msgs.append(f"Failed to create test file: {message}")
            overall_status = False
        
        return overall_status, "\n".join(status_msgs)
        
    except Exception as e:
        return False, f"Error verifying GitHub setup: {str(e)}"
    
    
def load_room_capacities(use_github=False):
    """Load room capacities from JSON file or GitHub"""
    try:
        # Try to load from GitHub first if enabled
        if use_github and GITHUB_AVAILABLE:
            content = load_from_github(os.path.basename(config.CAPACITY_CONFIG_PATH))
            if content:
                return json.loads(content.decode('utf-8'))
        
        # Otherwise load from local file
        if os.path.exists(config.CAPACITY_CONFIG_PATH):
            with open(config.CAPACITY_CONFIG_PATH, 'r') as f:
                capacities = json.load(f)
            return capacities
        return {}
    except Exception as e:
        print(f"Error loading room capacities: {e}")
        return {}


def save_room_capacities(capacities, use_github=False):
    """Save room capacities to JSON file and optionally to GitHub"""
    try:
        # Format JSON with indentation for readability
        json_content = json.dumps(capacities, indent=2)
        
        # Save locally
        with open(config.CAPACITY_CONFIG_PATH, 'w') as f:
            f.write(json_content)
        
        # Save to GitHub if enabled
        if use_github and GITHUB_AVAILABLE:
            success, message = save_to_github(
                os.path.basename(config.CAPACITY_CONFIG_PATH),
                json_content,
                f"Update room capacities - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            if not success:
                print(f"GitHub save warning: {message}")
        
        return True
    except Exception as e:
        print(f"Error saving room capacities: {e}")
        return False


def load_data(file_path=config.DEFAULT_EXCEL_PATH, use_github=False):
    """
    Load data from Excel file or GitHub
    Returns: (current_df, upcoming_df, past_df)
    """
    try:
        # Try to load from GitHub first if enabled
        if use_github and GITHUB_AVAILABLE:
            content = load_from_github(os.path.basename(file_path))
            if content:
                # Use BytesIO to create a file-like object from the content
                excel_data = io.BytesIO(content)
                xls = pd.ExcelFile(excel_data)
            else:
                # Fall back to local file if not found on GitHub
                xls = pd.ExcelFile(file_path)
        else:
            # Load from local file
            xls = pd.ExcelFile(file_path)
            
        sheet_names = xls.sheet_names
        
        # Identify sheets
        current_sheet = next((s for s in sheet_names if 'current' in s.lower()), sheet_names[0] if sheet_names else None)
        upcoming_sheet = next((s for s in sheet_names if 'upcoming' in s.lower()), None)
        past_sheet = next((s for s in sheet_names if 'past' in s.lower()), None)
        
        # Load sheets into dataframes
        if use_github and GITHUB_AVAILABLE and 'excel_data' in locals():
            # If we loaded from GitHub, use the BytesIO object
            current_df = pd.read_excel(excel_data, sheet_name=current_sheet) if current_sheet else pd.DataFrame()
            
            # We need to reset the position in the BytesIO object for each read
            excel_data.seek(0)
            upcoming_df = pd.read_excel(excel_data, sheet_name=upcoming_sheet) if upcoming_sheet else pd.DataFrame()
            
            excel_data.seek(0)
            past_df = pd.read_excel(excel_data, sheet_name=past_sheet) if past_sheet else pd.DataFrame()
        else:
            # Otherwise use the file path
            current_df = pd.read_excel(file_path, sheet_name=current_sheet) if current_sheet else pd.DataFrame()
            upcoming_df = pd.read_excel(file_path, sheet_name=upcoming_sheet) if upcoming_sheet else pd.DataFrame()
            past_df = pd.read_excel(file_path, sheet_name=past_sheet) if past_sheet else pd.DataFrame()
        
        # Clean column names by stripping whitespace
        for df in [current_df, upcoming_df, past_df]:
            if not df.empty:
                df.columns = df.columns.str.strip()
        
        # Standardize column names
        for df in [current_df, upcoming_df, past_df]:
            if not df.empty:
                # Rename only columns that exist
                cols_to_rename = {k: v for k, v in config.COLUMN_MAPPING.items() if k in df.columns}
                df.rename(columns=cols_to_rename, inplace=True)
        
        # Ensure all required columns exist
        for df in [current_df, upcoming_df, past_df]:
            if not df.empty:
                for col in config.REQUIRED_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
        
        # Set proper Status values
        current_df['Status'] = current_df['Status'].fillna('Current')
        upcoming_df['Status'] = upcoming_df['Status'].fillna('Upcoming')
        past_df['Status'] = past_df['Status'].fillna('Past')
        
        # Convert room numbers to strings for consistency and strip whitespace
        for df in [current_df, upcoming_df, past_df]:
            if not df.empty:
                df['Office'] = df['Office'].astype(str).str.strip()
                if 'Building' in df.columns:
                    df['Building'] = df['Building'].fillna('').astype(str).str.strip()
        
        return current_df, upcoming_df, past_df
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def save_data(current_df, upcoming_df, past_df, file_path=config.DEFAULT_EXCEL_PATH, room_capacities=None, use_github=False):
    """Save data to Excel file and optionally to GitHub"""
    try:
        # Create a local backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'{config.BACKUP_DIR}/MP_Office_Allocation_{timestamp}.xlsx'
        
        # Copy the original file to backup if it exists
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, backup_path)
                print(f"Backup created at {backup_path}")
            except Exception as e:
                print(f"Couldn't create backup: {e}")
        
        # Ensure columns are properly formatted before saving
        for df in [current_df, upcoming_df, past_df]:
            if not df.empty:
                # Ensure Building and Office columns exist and are strings
                if 'Building' in df.columns:
                    df['Building'] = df['Building'].astype(str)
                if 'Office' in df.columns:
                    df['Office'] = df['Office'].astype(str)
        
        # Save the modified data locally
        with pd.ExcelWriter(file_path) as writer:
            current_df.to_excel(writer, sheet_name='Current', index=False)
            upcoming_df.to_excel(writer, sheet_name='Upcoming', index=False)
            past_df.to_excel(writer, sheet_name='Past', index=False)
        
        # Save to GitHub if enabled
        if use_github and GITHUB_AVAILABLE:
            # Create Excel in memory
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                current_df.to_excel(writer, sheet_name='Current', index=False)
                upcoming_df.to_excel(writer, sheet_name='Upcoming', index=False)
                past_df.to_excel(writer, sheet_name='Past', index=False)
            
            # Get the binary content
            excel_buffer.seek(0)
            excel_content = excel_buffer.getvalue()
            
            # Save to GitHub
            success, message = save_to_github(
                os.path.basename(file_path),
                excel_content,
                f"Update office allocation data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            if not success:
                print(f"GitHub save warning: {message}")
        
        # Save room capacities if provided
        if room_capacities is not None:
            save_room_capacities(room_capacities, use_github)
        
        return True
    
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def initialize_room_capacities(current_df):
    """Initialize room capacities based on current occupancy"""
    from models import RoomOccupancy
    
    # Create temporary occupancy object
    room_capacities = {}
    temp_occupancy = RoomOccupancy(current_df, room_capacities)
    occupancy_data = temp_occupancy.get_occupancy_data()
    
    if not occupancy_data.empty:
        for _, row in occupancy_data.iterrows():
            building = row['Building']
            office = row['Office']
            key = f"{building}:{office}"
            
            # If storage, set capacity to 0
            if row['IsStorage']:
                room_capacities[key] = 0
            else:
                # Set default max capacity based on current occupancy
                current_occupants = row['Occupants']
                # For rooms with 3+ people, assume that's the capacity
                # For rooms with 0-2 people, set default to 2 unless already occupied by more
                default_capacity = max(current_occupants, 2)
                room_capacities[key] = default_capacity
        
        return room_capacities
    
    return {}


def create_system_manager(file_path=config.DEFAULT_EXCEL_PATH, use_github=False):
    """Create system manager objects from file or GitHub"""
    # Load data
    current_df, upcoming_df, past_df = load_data(file_path, use_github)
    
    # Create occupant manager
    occupant_manager = OccupantManager(current_df, upcoming_df, past_df)
    
    # Load room capacities
    room_capacities = load_room_capacities(use_github)
    
    # Initialize capacities if empty
    if not room_capacities:
        room_capacities = initialize_room_capacities(current_df)
        save_room_capacities(room_capacities, use_github)
    
    # Create room manager
    room_manager = RoomManager(occupant_manager, room_capacities)
    
    return occupant_manager, room_manager


def get_data_as_excel(occupant_manager, room_manager):
    """Get the current data as Excel file content (bytes)"""
    try:
        # Get current dataframes
        current_df = occupant_manager.get_current_occupants()
        upcoming_df = occupant_manager.get_upcoming_occupants()
        past_df = occupant_manager.get_past_occupants()
        
        # Create Excel in memory
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            current_df.to_excel(writer, sheet_name='Current', index=False)
            upcoming_df.to_excel(writer, sheet_name='Upcoming', index=False)
            past_df.to_excel(writer, sheet_name='Past', index=False)
        
        # Get the binary content
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    except Exception as e:
        print(f"Error creating Excel data: {e}")
        return None