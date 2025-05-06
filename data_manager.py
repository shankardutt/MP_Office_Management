"""
Data loading, saving, and manipulation functions
"""

import os
import json
import shutil
import pandas as pd
from datetime import datetime

import config
from models import OccupantManager, RoomManager


def load_room_capacities():
    """Load room capacities from JSON file"""
    try:
        if os.path.exists(config.CAPACITY_CONFIG_PATH):
            with open(config.CAPACITY_CONFIG_PATH, 'r') as f:
                capacities = json.load(f)
            return capacities
        return {}
    except Exception as e:
        print(f"Error loading room capacities: {e}")
        return {}


def save_room_capacities(capacities):
    """Save room capacities to JSON file"""
    try:
        with open(config.CAPACITY_CONFIG_PATH, 'w') as f:
            json.dump(capacities, f)
        return True
    except Exception as e:
        print(f"Error saving room capacities: {e}")
        return False


def load_data(file_path=config.DEFAULT_EXCEL_PATH):
    """
    Load data from Excel file
    Returns: (current_df, upcoming_df, past_df)
    """
    try:
        # Load all sheets
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        
        # Identify sheets
        current_sheet = next((s for s in sheet_names if 'current' in s.lower()), sheet_names[0] if sheet_names else None)
        upcoming_sheet = next((s for s in sheet_names if 'upcoming' in s.lower()), None)
        past_sheet = next((s for s in sheet_names if 'past' in s.lower()), None)
        
        # Load sheets into dataframes
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


def save_data(current_df, upcoming_df, past_df, file_path=config.DEFAULT_EXCEL_PATH, room_capacities=None):
    """Save data to Excel file and optionally save room capacities"""
    try:
        # Create backup
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
        
        # Save the modified data
        with pd.ExcelWriter(file_path) as writer:
            current_df.to_excel(writer, sheet_name='Current', index=False)
            upcoming_df.to_excel(writer, sheet_name='Upcoming', index=False)
            past_df.to_excel(writer, sheet_name='Past', index=False)
        
        # Save room capacities if provided
        if room_capacities is not None:
            save_room_capacities(room_capacities)
        
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


def create_system_manager(file_path=config.DEFAULT_EXCEL_PATH):
    """Create system manager objects from file"""
    # Load data
    current_df, upcoming_df, past_df = load_data(file_path)
    
    # Create occupant manager
    occupant_manager = OccupantManager(current_df, upcoming_df, past_df)
    
    # Load room capacities
    room_capacities = load_room_capacities()
    
    # Initialize capacities if empty
    if not room_capacities:
        room_capacities = initialize_room_capacities(current_df)
        save_room_capacities(room_capacities)
    
    # Create room manager
    room_manager = RoomManager(occupant_manager, room_capacities)
    
    return occupant_manager, room_manager