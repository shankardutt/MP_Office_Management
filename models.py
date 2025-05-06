"""
Data models and utility functions for Office Room Allocation System
"""

import pandas as pd
import numpy as np


def extract_floor(office):
    """Extract floor number from room number"""
    if isinstance(office, str) and '.' in office:
        try:
            return office.split('.')[0]
        except:
            pass
    return 'Unknown'


class RoomOccupancy:
    """Class to handle room occupancy data and calculations"""
    
    def __init__(self, current_df, room_capacities):
        self.df = current_df
        self.room_capacities = room_capacities
        self.occupancy_data = None
        self.calculate_occupancy()
    
    def calculate_occupancy(self):
        """Calculate room occupancy metrics"""
        if self.df.empty or 'Office' not in self.df.columns or 'Building' not in self.df.columns:
            self.occupancy_data = pd.DataFrame()
            return
        
        # Group by Building and Office to count occupants
        occupancy = self.df.groupby(['Building', 'Office']).size().reset_index(name='Occupants')
        
        # Add floor information
        occupancy['Floor'] = occupancy['Office'].apply(extract_floor)
        
        # Add storage flag
        occupancy['IsStorage'] = occupancy.apply(
            lambda x: True if any(self.df[(self.df['Office'] == x['Office']) & 
                                 (self.df['Building'] == x['Building'])]['Name'].str.contains('STORAGE', case=False, na=False)) 
                           else False,
            axis=1
        )
        
        # Add capacity information
        occupancy['Max_Capacity'] = occupancy.apply(
            lambda row: self.room_capacities.get(f"{row['Building']}:{row['Office']}", 2),  # Default to 2
            axis=1
        )
        
        # Calculate capacity metrics
        occupancy['Remaining'] = occupancy['Max_Capacity'] - occupancy['Occupants']
        occupancy['Percentage'] = (occupancy['Occupants'] / occupancy['Max_Capacity'] * 100).round(1)
        
        # Allow for negative remaining (overfilled rooms)
        occupancy['Status'] = occupancy.apply(self._get_room_status, axis=1)
        
        # Sort by building, floor, and room
        occupancy = occupancy.sort_values(['Building', 'Floor', 'Office'])
        
        self.occupancy_data = occupancy
    
    def _get_room_status(self, row):
        """Determine room status based on occupancy metrics"""
        if row['IsStorage']:
            return 'storage'
        
        if row['Occupants'] == 0:
            return 'vacant'
        
        # Allow for overfilled rooms (negative remaining)
        if row['Remaining'] < 0:
            return 'overfilled'
        
        percentage = row['Percentage']
        if percentage <= 25:
            return 'low'
        elif percentage <= 50:
            return 'medium'
        elif percentage <= 75:
            return 'high'
        else:
            return 'full'
    
    def get_occupancy_data(self):
        """Return the occupancy dataframe"""
        return self.occupancy_data
    
    def get_building_summary(self):
        """Get summary metrics by building"""
        if self.occupancy_data.empty:
            return pd.DataFrame()
        
        summary = self.occupancy_data.groupby('Building').agg({
            'Office': 'count',
            'Occupants': 'sum',
            'Max_Capacity': 'sum',
            'Remaining': 'sum'
        }).reset_index()
        
        summary.rename(columns={'Office': 'Room Count'}, inplace=True)
        summary['Occupancy Rate'] = (summary['Occupants'] / summary['Max_Capacity'] * 100).round(1)
        
        return summary
    
    def get_floor_summary(self, building=None):
        """Get summary metrics by floor (optionally filtered by building)"""
        if self.occupancy_data.empty:
            return pd.DataFrame()
        
        # Filter by building if specified
        data = self.occupancy_data
        if building and building != 'All':
            data = data[data['Building'] == building]
        
        summary = data.groupby(['Building', 'Floor']).agg({
            'Office': 'count',
            'Occupants': 'sum',
            'Max_Capacity': 'sum',
            'Remaining': 'sum'
        }).reset_index()
        
        summary.rename(columns={'Office': 'Room Count'}, inplace=True)
        summary['Occupancy Rate'] = (summary['Occupants'] / summary['Max_Capacity'] * 100).round(1)
        
        return summary
    
    def get_room_by_id(self, building, office):
        """Get a specific room by building and office number"""
        if self.occupancy_data.empty:
            return None
        
        room = self.occupancy_data[
            (self.occupancy_data['Building'] == building) &
            (self.occupancy_data['Office'] == office)
        ]
        
        if room.empty:
            return None
            
        return room.iloc[0]
    
    def get_occupants_for_room(self, building, office):
        """Get all occupants for a specific room"""
        if self.df.empty:
            return pd.DataFrame()
        
        occupants = self.df[
            (self.df['Building'] == building) &
            (self.df['Office'] == office)
        ]
        
        return occupants


class OccupantManager:
    """Class to manage occupant data and operations"""
    
    def __init__(self, current_df, upcoming_df, past_df):
        self.current_df = current_df.copy() if not current_df.empty else pd.DataFrame(columns=['Name', 'Status', 'Email address', 'Position', 'Office', 'Building'])
        self.upcoming_df = upcoming_df.copy() if not upcoming_df.empty else pd.DataFrame(columns=['Name', 'Status', 'Email address', 'Position', 'Office', 'Building'])
        self.past_df = past_df.copy() if not past_df.empty else pd.DataFrame(columns=['Name', 'Status', 'Email address', 'Position', 'Office', 'Building'])
    
    def get_current_occupants(self):
        """Get current occupants dataframe sorted alphabetically by name"""
        if not self.current_df.empty:
            return self.current_df.sort_values('Name')
        return self.current_df

    def get_upcoming_occupants(self):
        """Get upcoming occupants dataframe sorted alphabetically by name"""
        if not self.upcoming_df.empty:
            return self.upcoming_df.sort_values('Name')
        return self.upcoming_df

    def get_past_occupants(self):
        """Get past occupants dataframe sorted alphabetically by name"""
        if not self.past_df.empty:
            return self.past_df.sort_values('Name')
        return self.past_df
    
    def add_occupant(self, occupant_data, status='Current'):
        """Add a new occupant to the appropriate dataframe"""
        new_row = pd.DataFrame([occupant_data])
        
        if status == 'Current':
            self.current_df = pd.concat([self.current_df, new_row], ignore_index=True)
        elif status == 'Upcoming':
            self.upcoming_df = pd.concat([self.upcoming_df, new_row], ignore_index=True)
        elif status == 'Past':
            self.past_df = pd.concat([self.past_df, new_row], ignore_index=True)
            
        return True
    
    def update_current_occupants(self, updated_df):
        """Update the current occupants dataframe and handle status changes"""
        # Track which occupants need to be moved between dataframes
        to_upcoming = []
        to_past = []
        
        # Identify occupants that need to be moved
        for idx, row in updated_df.iterrows():
            if 'Status' in row:
                if row['Status'] == 'Upcoming':
                    to_upcoming.append(row)
                elif row['Status'] == 'Past':
                    to_past.append(row)
        
        # Remove those occupants from the updated dataframe
        for occupant in to_upcoming + to_past:
            updated_df = updated_df[updated_df['Name'] != occupant['Name']]
        
        # Update the current dataframe
        self.current_df = updated_df
        
        # Add occupants to their new dataframes
        for occupant in to_upcoming:
            self.upcoming_df = pd.concat([self.upcoming_df, pd.DataFrame([occupant])], ignore_index=True)
        
        for occupant in to_past:
            self.past_df = pd.concat([self.past_df, pd.DataFrame([occupant])], ignore_index=True)
        
        return True
    
    def update_upcoming_occupants(self, updated_df):
        """Update the upcoming occupants dataframe and handle status changes"""
        # Track which occupants need to be moved between dataframes
        to_current = []
        to_past = []
        
        # Identify occupants that need to be moved
        for idx, row in updated_df.iterrows():
            if 'Status' in row:
                if row['Status'] == 'Current':
                    to_current.append(row)
                elif row['Status'] == 'Past':
                    to_past.append(row)
        
        # Remove those occupants from the updated dataframe
        for occupant in to_current + to_past:
            updated_df = updated_df[updated_df['Name'] != occupant['Name']]
        
        # Update the upcoming dataframe
        self.upcoming_df = updated_df
        
        # Add occupants to their new dataframes
        for occupant in to_current:
            self.current_df = pd.concat([self.current_df, pd.DataFrame([occupant])], ignore_index=True)
        
        for occupant in to_past:
            self.past_df = pd.concat([self.past_df, pd.DataFrame([occupant])], ignore_index=True)
        
        return True
    
    def update_past_occupants(self, updated_df):
        """Update the past occupants dataframe and handle status changes"""
        # Track which occupants need to be moved between dataframes
        to_current = []
        to_upcoming = []
        
        # Identify occupants that need to be moved
        for idx, row in updated_df.iterrows():
            if 'Status' in row:
                if row['Status'] == 'Current':
                    to_current.append(row)
                elif row['Status'] == 'Upcoming':
                    to_upcoming.append(row)
        
        # Remove those occupants from the updated dataframe
        for occupant in to_current + to_upcoming:
            updated_df = updated_df[updated_df['Name'] != occupant['Name']]
        
        # Update the past dataframe
        self.past_df = updated_df
        
        # Add occupants to their new dataframes
        for occupant in to_current:
            self.current_df = pd.concat([self.current_df, pd.DataFrame([occupant])], ignore_index=True)
        
        for occupant in to_upcoming:
            self.upcoming_df = pd.concat([self.upcoming_df, pd.DataFrame([occupant])], ignore_index=True)
        
        return True

    def assign_occupant_to_room(self, name, building, office, status='Current'):
        """Assign an occupant to a specific room"""
        # Convert status from UI format to internal format if needed
        if status == 'Current Occupants':
            status = 'Current'
        elif status == 'Upcoming Occupants':
            status = 'Upcoming'
            
        # Select the appropriate dataframe based on status
        if status == 'Current':
            df = self.current_df
        elif status == 'Upcoming':
            df = self.upcoming_df
        else:
            return False
        
        # Find the exact occupant by matching the full name
        # This is the critical fix - we need to do an exact match on the name
        occupant_mask = df['Name'] == name
        occupant_idx = df[occupant_mask].index
        
        if len(occupant_idx) == 0:
            return False
        
        # If multiple matches (shouldn't happen with exact matching), use first one
        idx = occupant_idx[0]
        
        # Update room assignment for this specific occupant
        df.loc[idx, 'Building'] = building
        df.loc[idx, 'Office'] = office
        
        # Update the appropriate dataframe
        if status == 'Current':
            self.current_df = df
        elif status == 'Upcoming':
            self.upcoming_df = df
                
        return True
        
    def update_occupancy(self):
        """Update room occupancy data"""
        self.room_occupancy = RoomOccupancy(
            self.occupant_manager.get_current_occupants(), 
            self.room_capacities
        )
        return self.room_occupancy
    
    def get_unique_buildings(self):
        """Get a list of all unique buildings across all dataframes"""
        buildings = set()
        for df in [self.current_df, self.upcoming_df, self.past_df]:
            if not df.empty and 'Building' in df.columns:
                buildings.update(df['Building'].dropna().unique())
        return sorted(list(buildings))
    
    def get_unique_offices(self):
        """Get a list of all unique offices across all dataframes"""
        offices = set()
        for df in [self.current_df, self.upcoming_df, self.past_df]:
            if not df.empty and 'Office' in df.columns:
                offices.update(df['Office'].dropna().unique())
        return sorted(list(offices))


class RoomManager:
    """Class to manage room data and operations"""
    
    def __init__(self, occupant_manager, room_capacities):
        self.occupant_manager = occupant_manager
        self.room_capacities = room_capacities
        self.room_occupancy = None
        self.update_occupancy()
    
    def update_occupancy(self):
        """Update room occupancy data"""
        self.room_occupancy = RoomOccupancy(
            self.occupant_manager.get_current_occupants(), 
            self.room_capacities
        )
        return self.room_occupancy
    
    def get_occupancy_data(self):
        """Get room occupancy data"""
        return self.room_occupancy.get_occupancy_data()
    
    def get_capacity(self, building, office):
        """Get the capacity for a specific room"""
        room_key = f"{building}:{office}"
        return self.room_capacities.get(room_key, 2)  # Default to 2
    
    def set_capacity(self, building, office, capacity):
        """Set the capacity for a specific room"""
        room_key = f"{building}:{office}"
        self.room_capacities[room_key] = capacity
        self.update_occupancy()
        return True
    
    def add_room(self, building, office, capacity, is_storage=False):
        """Add a new room"""
        room_key = f"{building}:{office}"
        self.room_capacities[room_key] = capacity
        
        # Add a placeholder or storage record
        if is_storage:
            placeholder = {
                'Name': 'STORAGE',
                'Status': 'Current',
                'Email address': '',
                'Position': '',
                'Office': office,
                'Building': building
            }
        else:
            placeholder = {
                'Name': 'PLACEHOLDER',
                'Status': 'Current',
                'Email address': '',
                'Position': '',
                'Office': office,
                'Building': building
            }
        
        # Add to current occupants
        self.occupant_manager.add_occupant(placeholder, 'Current')
        self.update_occupancy()
        
        return True
    
    def delete_room(self, building, office):
        """Delete a room and its occupants"""
        room_key = f"{building}:{office}"
        
        # Remove from capacity dictionary
        if room_key in self.room_capacities:
            del self.room_capacities[room_key]
        
        # Remove occupants from all dataframes
        dfs = [
            self.occupant_manager.current_df,
            self.occupant_manager.upcoming_df,
            self.occupant_manager.past_df
        ]
        
        for i, df in enumerate(dfs):
            if not df.empty:
                mask = (df['Building'] == building) & (df['Office'] == office)
                if mask.any():
                    # Create a new dataframe without these occupants
                    new_df = df[~mask].copy()
                    
                    # Update the appropriate dataframe
                    if i == 0:
                        self.occupant_manager.current_df = new_df
                    elif i == 1:
                        self.occupant_manager.upcoming_df = new_df
                    else:
                        self.occupant_manager.past_df = new_df
        
        self.update_occupancy()
        return True
    
    def update_room(self, building, office, new_building, new_office, new_capacity, new_type):
        """Update room properties and move occupants if needed"""
        old_key = f"{building}:{office}"
        new_key = f"{new_building}:{new_office}"
        
        # Handle change in storage type
        is_storage = new_type == 'Storage'
        was_storage = False
        
        # Check current occupants for STORAGE designation
        current_df = self.occupant_manager.current_df
        if not current_df.empty:
            storage_mask = (
                (current_df['Building'] == building) & 
                (current_df['Office'] == office) & 
                (current_df['Name'].fillna('').str.contains('STORAGE', case=False))
            )
            was_storage = storage_mask.any()
        
        # Remove old room capacity
        if old_key in self.room_capacities:
            del self.room_capacities[old_key]
        
        # Add new room capacity
        self.room_capacities[new_key] = new_capacity
        
        # Update occupant records (all dataframes)
        dfs = [
            self.occupant_manager.current_df,
            self.occupant_manager.upcoming_df,
            self.occupant_manager.past_df
        ]
        
        changes_current = []
        
        for i, df in enumerate(dfs):
            if not df.empty:
                # Find occupants in this room
                room_mask = (df['Building'] == building) & (df['Office'] == office)
                room_occupants = df[room_mask].copy()
                
                if not room_occupants.empty:
                    # Update to new building/office
                    room_occupants['Building'] = new_building
                    room_occupants['Office'] = new_office
                    
                    # Remove old occupants
                    df = df[~room_mask]
                    
                    # Add updated occupants
                    df = pd.concat([df, room_occupants], ignore_index=True)
                    
                    # Update the dataframe
                    if i == 0:
                        self.occupant_manager.current_df = df
                        # Save changes for storage handling
                        changes_current = room_occupants
                    elif i == 1:
                        self.occupant_manager.upcoming_df = df
                    else:
                        self.occupant_manager.past_df = df
        
        # Handle storage flag changes
        if was_storage != is_storage and not changes_current.empty:
            current_df = self.occupant_manager.current_df
            
            if is_storage and not was_storage:
                # Convert to storage - remove existing occupants and add STORAGE
                # Remove all occupants from this room
                room_mask = (current_df['Building'] == new_building) & (current_df['Office'] == new_office)
                current_df = current_df[~room_mask]
                
                # Add STORAGE record
                storage_record = {
                    'Name': 'STORAGE',
                    'Status': 'Current',
                    'Email address': '',
                    'Position': '',
                    'Office': new_office,
                    'Building': new_building
                }
                current_df = pd.concat([current_df, pd.DataFrame([storage_record])], ignore_index=True)
                
                self.occupant_manager.current_df = current_df
                
            elif not is_storage and was_storage:
                # Convert from storage to regular - remove STORAGE and add PLACEHOLDER
                # Remove STORAGE records
                storage_mask = (
                    (current_df['Building'] == new_building) & 
                    (current_df['Office'] == new_office) & 
                    (current_df['Name'].fillna('').str.contains('STORAGE', case=False))
                )
                current_df = current_df[~storage_mask]
                
                # Check if there are any occupants left
                room_mask = (current_df['Building'] == new_building) & (current_df['Office'] == new_office)
                if not room_mask.any():
                    # Add PLACEHOLDER record
                    placeholder = {
                        'Name': 'PLACEHOLDER',
                        'Status': 'Current',
                        'Email address': '',
                        'Position': '',
                        'Office': new_office,
                        'Building': new_building
                    }
                    current_df = pd.concat([current_df, pd.DataFrame([placeholder])], ignore_index=True)
                
                self.occupant_manager.current_df = current_df
        
        self.update_occupancy()
        return True