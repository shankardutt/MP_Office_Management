"""
Upcoming Occupants page for Office Room Allocation System
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def show_upcoming_occupants(occupant_manager, room_manager):
    """Display the upcoming occupants page"""
    st.title("Upcoming Occupants")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        filter_name = st.text_input("Filter by Name", key="upcoming_filter_name")
    with col2:
        building_filter = st.selectbox("Filter by Building", 
                                      ['All'] + occupant_manager.get_unique_buildings(),
                                      key="upcoming_building_filter")
    
    # Apply filters
    upcoming_df = occupant_manager.get_upcoming_occupants()
    filtered_df = upcoming_df.copy()
    
    if filter_name:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(filter_name, case=False, na=False)]
    
    if building_filter != 'All':
        if 'Building' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Building'] == building_filter]
    
    # Sort alphabetically by Name
    filtered_df = filtered_df.sort_values('Name')
    
    # Display data and allow editing
    if not filtered_df.empty:
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Current", "Upcoming", "Past"],
                    required=True
                ),
                "Building": st.column_config.SelectboxColumn(
                    "Building",
                    options=occupant_manager.get_unique_buildings(),
                    required=True
                ),
                "Office": st.column_config.SelectboxColumn(
                    "Office",
                    options=occupant_manager.get_unique_offices(),
                    required=True
                ),
                "Planned Arrival": st.column_config.DateColumn(
                    "Planned Arrival",
                    format="YYYY-MM-DD",
                    help="Planned arrival date"
                )
            },
            hide_index=True,
            num_rows="dynamic",
            key="upcoming_occupants_editor"
        )
        
        # Update button to apply changes
        if st.button("Apply Changes", key="apply_upcoming_changes_btn"):
            # Update the dataframe if changes were made
            if not edited_df.equals(filtered_df):
                # Update occupant manager with edited dataframe
                occupant_manager.update_upcoming_occupants(edited_df)
                
                # Update room occupancy
                room_manager.update_occupancy()
                
                st.success("Changes applied! Remember to click 'Save Changes' in the sidebar to save them permanently.")
                st.rerun()
    else:
        st.info("No upcoming occupants found with the selected filters")
    
    # Add new upcoming occupant section
    st.markdown("---")
    st.subheader("Add New Upcoming Occupant")
    
    with st.form("add_upcoming_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Name", placeholder="e.g., Smith, John Dr")
            new_email = st.text_input("Email", placeholder="e.g., john.smith@anu.edu.au")
            new_position = st.text_input("Position", placeholder="e.g., Professor")
            planned_arrival = st.date_input("Planned Arrival Date", key="upcoming_planned_arrival")
        
        with col2:
            # Get room occupancy data for intelligent room suggestion
            room_occupancy = room_manager.get_occupancy_data()
            
            if not room_occupancy.empty:
                # Add rooms with availability info
                room_options = []
                
                for _, room in room_occupancy.iterrows():
                    building = room['Building']
                    office = room['Office']
                    occupants = room['Occupants']
                    max_capacity = room['Max_Capacity']
                    remaining = room['Remaining']
                    
                    # Skip storage rooms
                    if room['IsStorage']:
                        continue
                    
                    # Allow assignment to all rooms regardless of current occupancy
                    status_label = (f"Vacant (0/{max_capacity})" if occupants == 0 else 
                                   f"Occupied ({occupants}/{max_capacity}, {remaining} available)")
                    
                    if remaining < 0:
                        status_label = f"Overfilled ({occupants}/{max_capacity}, {abs(remaining)} over capacity)"
                    
                    room_label = f"{building} - {office} [{status_label}]"
                    
                    # Include all rooms but sort by availability
                    room_options.append((room_label, building, office, remaining))
                
                # Sort by most available space
                room_options.sort(key=lambda x: x[3], reverse=True)
                
                # Create dropdown with room options
                if room_options:
                    selected_room = st.selectbox(
                        "Recommended Room (sorted by availability)",
                        [option[0] for option in room_options],
                        key="upcoming_new_room_select"
                    )
                    
                    # Extract building and office from selection
                    selected_index = [option[0] for option in room_options].index(selected_room)
                    new_building = room_options[selected_index][1]
                    new_office = room_options[selected_index][2]
                    
                    # Show warning if room is at capacity or overfilled
                    remaining = room_options[selected_index][3]
                    if remaining == 0:
                        st.warning("This room is currently at full capacity.")
                    elif remaining < 0:
                        st.error(f"⚠️ Warning: This room is already overfilled by {abs(remaining)} occupants.")
                    
                else:
                    new_office = st.text_input("Office", placeholder="e.g., 3.17", key="upcoming_new_office_input")
                    new_building = st.selectbox("Building", 
                                              occupant_manager.get_unique_buildings(),
                                              key="upcoming_new_building_select")
            else:
                new_office = st.text_input("Office", placeholder="e.g., 3.17", key="upcoming_new_office_input_fallback") 
                new_building = st.selectbox("Building", 
                                          occupant_manager.get_unique_buildings(),
                                          key="upcoming_new_building_select_fallback")
        
        submitted = st.form_submit_button("Add Upcoming Occupant")
        
        if submitted:
            if new_name:
                # Create new row
                new_row = {
                    'Name': new_name,
                    'Email address': new_email,
                    'Position': new_position,
                    'Office': new_office,
                    'Building': new_building,
                    'Status': 'Upcoming',
                    'Planned Arrival': planned_arrival
                }
                
                # Add to upcoming dataframe through occupant manager
                occupant_manager.add_occupant(new_row, 'Upcoming')
                
                # Update room occupancy
                room_manager.update_occupancy()
                
                st.success(f"Added {new_name} to upcoming occupants. Remember to save changes!")
                st.rerun()
            else:
                st.error("Name is required")