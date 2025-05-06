"""
Current Occupants page for Office Room Allocation System
"""

import streamlit as st
import pandas as pd


def show_current_occupants(occupant_manager, room_manager):
    """Display the current occupants page"""
    st.title("Current Occupants")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_name = st.text_input("Filter by Name", key="current_filter_name")
    with col2:
        if st.session_state.filter_building != 'All':
            building_filter = st.session_state.filter_building
        else:
            building_filter = st.selectbox("Filter by Building", 
                                         ['All'] + occupant_manager.get_unique_buildings(),
                                         key="curr_occ_building_filter")
    with col3:
        office_filter = st.selectbox("Filter by Office", 
                                    ['All'] + occupant_manager.get_unique_offices(),
                                    key="curr_occ_office_filter")
    
    # Apply filters
    current_df = occupant_manager.get_current_occupants()
    filtered_df = current_df.copy()
    
    if filter_name:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(filter_name, case=False, na=False)]
    
    if building_filter != 'All':
        filtered_df = filtered_df[filtered_df['Building'] == building_filter]
    
    if office_filter != 'All':
        filtered_df = filtered_df[filtered_df['Office'] == office_filter]
    
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
                    required=False  # Changed from required=True
                ),
                "Email address": st.column_config.TextColumn(
                    "Email address",
                    help="User's email address"
                ),
                "Office": st.column_config.SelectboxColumn(
                    "Office",
                    options=occupant_manager.get_unique_offices(),
                    required=False  # Changed from required=True
                ),
                "Position": st.column_config.TextColumn(
                    "Position",
                    help="Occupant's role or position"
                )
            },
            hide_index=True,
            num_rows="dynamic",
            key="current_occupants_editor"
        )
        
        # Update button to apply changes
        if st.button("Apply Changes", key="apply_current_changes_btn"):
            # Update the dataframe if changes were made
            if not edited_df.equals(filtered_df):
                # Update occupant manager with edited dataframe
                occupant_manager.update_current_occupants(edited_df)
                
                # Update room occupancy
                room_manager.update_occupancy()
                
                st.success("Changes applied! Remember to click 'Save Changes' in the sidebar to save them permanently.")
                st.rerun()
                
        # Add delete functionality after the data editor but before the form
        st.markdown("### Delete Occupants")
        st.write("Select an occupant to delete:")
        
        delete_cols = st.columns(3)
        for i, (_, occupant) in enumerate(filtered_df.iterrows()):
            col_idx = i % 3
            with delete_cols[col_idx]:
                occupant_name = occupant['Name']
                # Skip STORAGE and PLACEHOLDER entries
                if 'STORAGE' in occupant_name or 'PLACEHOLDER' in occupant_name:
                    continue
                    
                if st.button(f"Delete {occupant_name}", key=f"delete_current_{i}"):
                    # Delete the occupant
                    occupant_manager.delete_occupant(occupant_name, 'Current')
                    # Update room occupancy
                    room_manager.update_occupancy()
                    st.success(f"Deleted {occupant_name}. Remember to save changes!")
                    st.rerun()
    else:
        st.info("No current occupants found with the selected filters")
    
    # Add new occupant section
    st.markdown("---")
    st.subheader("Add New Occupant")
    
    with st.form("add_occupant_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Name", placeholder="e.g., Smith, John Dr")
            new_email = st.text_input("Email", placeholder="e.g., john.smith@anu.edu.au")
            new_position = st.text_input("Position", placeholder="e.g., Professor")
            # Define the status here - was missing before
            new_status = "Current"  # Default status for this page
        
        with col2:
            # Get room occupancy for intelligent room assignment
            room_occupancy = room_manager.get_occupancy_data()
            
            # Add an option to leave room unassigned
            assign_room = st.checkbox("Assign to a room now", value=True, key="assign_room_current")
            
            if assign_room and not room_occupancy.empty:
                # Add formatted room labels with capacity info
                room_options = []
                
                for _, room in room_occupancy.iterrows():
                    building = room['Building']
                    office = room['Office']
                    occupants = room['Occupants']
                    max_capacity = room['Max_Capacity']
                    remaining = room['Remaining']
                    percentage = room['Percentage']
                    
                    # Skip storage rooms
                    if room['IsStorage']:
                        continue
                    
                    # Create formatted room label
                    status_label = (f"Vacant" if occupants == 0 else 
                                    f"{occupants}/{max_capacity} occupants ({percentage}%)")
                    
                    room_label = f"{building} - {office} [{status_label}]"
                    room_options.append((room_label, building, office, percentage))
                
                # Sort by occupancy percentage (lowest first)
                room_options.sort(key=lambda x: x[3])
                
                # Create dropdown with room options
                if room_options:
                    selected_room = st.selectbox(
                        "Room (sorted by availability)",
                        [option[0] for option in room_options],
                        key="new_occupant_room_select"
                    )
                    
                    # Extract building and office from selection
                    selected_index = [option[0] for option in room_options].index(selected_room)
                    new_building = room_options[selected_index][1]
                    new_office = room_options[selected_index][2]
                    
                    # Show capacity warning if needed
                    selected_percentage = room_options[selected_index][3]
                    if selected_percentage >= 75 and selected_percentage < 100:
                        st.warning(f"This room is at {selected_percentage}% capacity")
                    elif selected_percentage >= 100:
                        st.error("This room is at or over capacity")
                else:
                    new_office = st.text_input("Office", placeholder="e.g., 3.17")
                    new_building = st.selectbox("Building", 
                                            occupant_manager.get_unique_buildings(),
                                            key="new_occupant_building_select")
            else:
                # Set empty values if not assigning a room
                new_building = ""
                new_office = ""
        
        submitted = st.form_submit_button("Add Occupant")
        
        if submitted:
            # Modified validation - only require name
            if new_name:
                # Create new row
                new_row = {
                    'Name': new_name,
                    'Email address': new_email,
                    'Position': new_position,
                    'Office': new_office,
                    'Building': new_building,
                    'Status': new_status
                }
                
                # Add to appropriate dataframe through occupant manager
                occupant_manager.add_occupant(new_row, new_status)
                
                # Update room occupancy
                room_manager.update_occupancy()
                
                st.success(f"Added {new_name} to {new_status} occupants. Remember to save changes!")
                st.rerun()
            else:
                st.error("Name is required")  # Changed error message to only require Name