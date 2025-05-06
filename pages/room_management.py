"""
Room Management page for Office Room Allocation System
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from utils import format_room_card


def show_room_management(occupant_manager, room_manager):
    """Display the room management page"""
    st.title("Room Management")
    
    # Update occupancy data
    room_manager.update_occupancy()
    
    # Create tabs for different management views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Room Occupancy", 
        "Edit Rooms",
        "Room Status", 
        "Room Assignment"
    ])
    
    # Tab 1: Room Occupancy Overview
    with tab1:
        show_room_occupancy(occupant_manager, room_manager)
    
    # Tab 2: Edit Rooms
    with tab2:
        show_room_editor(occupant_manager, room_manager)
    
    # Tab 3: Room Status
    with tab3:
        show_room_status(occupant_manager, room_manager)
    
    # Tab 4: Room Assignment
    with tab4:
        show_room_assignment(occupant_manager, room_manager)


def show_room_occupancy(occupant_manager, room_manager):
    """Show room occupancy overview"""
    st.subheader("Room Occupancy Overview")
    
    # Filter by building
    building_filter = st.selectbox(
        "Select Building", 
        ['All'] + occupant_manager.get_unique_buildings(), 
        key='room_occupancy_building_filter'  # Added unique key
    )
    
    # Get room occupancy data
    room_occupancy = room_manager.get_occupancy_data()
    
    if not room_occupancy.empty:
        # Filter by building if needed
        if building_filter != 'All':
            room_occupancy = room_occupancy[room_occupancy['Building'] == building_filter]
        
        # Show occupancy data with capacity information
        st.write("**Room Occupancy Table**")
        
        # Create a formatted dataframe for display
        display_df = room_occupancy[['Building', 'Floor', 'Office', 'Occupants', 
                                    'Max_Capacity', 'Remaining', 'Percentage', 'Status']]
        
        # Sort by building, floor, and room number
        display_df = display_df.sort_values(['Building', 'Floor', 'Office'])
        
        # Function to color cells based on occupancy percentage
        def color_occupancy_percentage(val):
            """Color cells based on occupancy percentage."""
            try:
                percentage = float(val)
                if percentage == 0:
                    return 'background-color: #d4edda'  # Vacant - green
                elif percentage <= 25:
                    return 'background-color: #e6f7e1'  # Low - light green
                elif percentage <= 50:
                    return 'background-color: #fff3cd'  # Medium - yellow
                elif percentage <= 75:
                    return 'background-color: #ffe5d9'  # High - light orange
                elif percentage <= 100:
                    return 'background-color: #f8d7da'  # Full - red
                else:
                    return 'background-color: #f5c6cb'  # Overfilled - dark red
            except (ValueError, TypeError):
                return ''

        # Style the dataframe
        styled_df = display_df.style.applymap(
            lambda x: color_occupancy_percentage(x) if isinstance(x, (int, float)) else '',
            subset=['Percentage']
        )

        # Format percentage column
        styled_df = styled_df.format({'Percentage': '{:.1f}%'})
        styled_df = styled_df.set_table_attributes('class="dataframe"')

        st.dataframe(styled_df, use_container_width=True)
        
        # Show rooms organized by floor
        st.write("**Rooms by Floor**")
        
        for building in room_occupancy['Building'].unique():
            if building_filter != 'All' and building != building_filter:
                continue
            
            st.markdown(f"### {building}")
            
            building_rooms = room_occupancy[room_occupancy['Building'] == building]
            
            # Get all floors in this building
            floors = sorted(building_rooms['Floor'].unique(), 
                           key=lambda x: float(x) if x.isdigit() or x.replace('.', '', 1).isdigit() else float('inf'))
            
            for floor in floors:
                st.markdown(f"<div class='floor-heading'>Floor {floor}</div>", unsafe_allow_html=True)
                
                # Get rooms on this floor
                floor_rooms = building_rooms[building_rooms['Floor'] == floor]
                
                # Create a grid of rooms
                cols = st.columns(4)  # 4 rooms per row
                
                for i, (_, room) in enumerate(floor_rooms.iterrows()):
                    col_idx = i % 4
                    
                    # Get occupancy information
                    building = room['Building']
                    office = room['Office']
                    occupants = room['Occupants']
                    max_capacity = room['Max_Capacity']
                    remaining = room['Remaining']
                    percentage = room['Percentage']
                    is_storage = room['IsStorage']
                    status = room['Status']
                    
                    # Create room card
                    with cols[col_idx]:
                        st.markdown(
                            format_room_card(
                                building, office, occupants, max_capacity, 
                                remaining, percentage, is_storage, status
                            ), 
                            unsafe_allow_html=True
                        )
                        
                        # Show occupants if any
                        if occupants > 0 and not is_storage:
                            room_occupants = occupant_manager.get_current_occupants()
                            room_occupants = room_occupants[
                                (room_occupants['Building'] == room['Building']) & 
                                (room_occupants['Office'] == room['Office'])
                            ]
                            
                            for _, occupant in room_occupants.iterrows():
                                st.markdown(
                                    f"<span class='occupant-tag'>{occupant['Name']}</span>",
                                    unsafe_allow_html=True
                                )
    else:
        st.info("No room data available")


def show_room_editor(occupant_manager, room_manager):
    """Show room editor interface"""
    st.subheader("Edit Room Information")
    
    # Get room occupancy data
    room_occupancy = room_manager.get_occupancy_data()
    
    if not room_occupancy.empty:
        # Create a more comprehensive dataframe for editing that includes all needed fields
        edit_df = room_occupancy.copy()
        
        # Add room type column
        edit_df['Room Type'] = edit_df['IsStorage'].apply(lambda x: 'Storage' if x else 'Regular')
        
        # Create a fully editable version with better column names and ordering
        editable_df = edit_df[[
            'Building', 'Office', 'Floor', 'Occupants', 'Max_Capacity', 
            'Remaining', 'Percentage', 'Room Type'
        ]].copy()
        
        # Rename columns for clarity
        editable_df = editable_df.rename(columns={
            'Max_Capacity': 'Capacity',
            'Percentage': 'Occupancy %'
        })
        
        # Allow building filtering for easier management
        building_filter = st.selectbox(
            "Filter by Building", 
            ['All'] + sorted(editable_df['Building'].unique().tolist()),
            key='edit_room_building_filter'  # Added unique key
        )
        
        if building_filter != 'All':
            filtered_df = editable_df[editable_df['Building'] == building_filter].copy()
        else:
            filtered_df = editable_df.copy()
        
        # Sort for easier viewing
        filtered_df = filtered_df.sort_values(['Building', 'Floor', 'Office'])
        
        # Show current data in an editable table
        st.write("Edit the table directly by clicking on cells. All fields are editable except Occupants, Remaining, and Occupancy %.")
        st.write("To add a new room, add a new row. To delete a room, remove all text from that row.")
        
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "Building": st.column_config.TextColumn(
                    "Building",
                    help="Building name - edit directly to rename"
                ),
                "Office": st.column_config.TextColumn(
                    "Office",
                    help="Room number"
                ),
                "Floor": st.column_config.TextColumn(
                    "Floor",
                    help="Floor number (derived from room number)"
                ),
                "Capacity": st.column_config.NumberColumn(
                    "Capacity",
                    min_value=0,
                    max_value=20,
                    help="Maximum number of people allowed in this room"
                ),
                "Occupants": st.column_config.NumberColumn(
                    "Occupants",
                    disabled=True,
                    help="Current number of occupants (read-only)"
                ),
                "Remaining": st.column_config.NumberColumn(
                    "Remaining",
                    disabled=True,
                    help="Available space in the room (read-only)"
                ),
                "Occupancy %": st.column_config.ProgressColumn(
                    "Occupancy %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                    help="Percentage of capacity used (read-only)"
                ),
                "Room Type": st.column_config.SelectboxColumn(
                    "Room Type",
                    options=["Regular", "Storage"],
                    help="Type of room"
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="room_editor"
        )
        
        # Add a save button for the edited data
        if st.button("Save Room Changes", type="primary"):
            try:
                # Track changes to process
                changes_made = False
                changes_summary = []
                deleted_rooms = []
                added_rooms = []
                updated_rooms = []
                
                # Get original keys from room_capacities for comparison
                original_keys = set(room_manager.room_capacities.keys())
                existing_rooms = {f"{row['Building']}:{row['Office']}": row for _, row in edit_df.iterrows()}
                
                # Process added and updated rooms
                for _, row in edited_df.iterrows():
                    # Skip empty rows (these are considered deleted)
                    if pd.isna(row['Building']) or pd.isna(row['Office']) or row['Building'] == '' or row['Office'] == '':
                        continue
                        
                    building = str(row['Building']).strip()
                    office = str(row['Office']).strip()
                    capacity = int(row['Capacity']) if not pd.isna(row['Capacity']) else 0
                    room_type = row['Room Type']
                    is_storage = room_type == 'Storage'
                    
                    # Generate the room key
                    room_key = f"{building}:{office}"
                    
                    # Check if this is a new room
                    if room_key not in existing_rooms:
                        changes_made = True
                        added_rooms.append((building, office, capacity, is_storage))
                        changes_summary.append(f"Added new room: {building} - {office}")
                    else:
                        # Check for updates to existing room
                        orig_building, orig_office = room_key.split(':')
                        orig_capacity = room_manager.get_capacity(orig_building, orig_office)
                        orig_is_storage = existing_rooms[room_key]['IsStorage']
                        
                        # Check if any properties changed
                        if (capacity != orig_capacity or is_storage != orig_is_storage):
                            changes_made = True
                            changes_summary.append(f"Updated room: {building} - {office}")
                            updated_rooms.append((building, office, capacity, is_storage))
                
                # Find deleted rooms
                for key in original_keys:
                    building, office = key.split(':')
                    room_key = f"{building}:{office}"
                    
                    found = False
                    for _, row in edited_df.iterrows():
                        if pd.isna(row['Building']) or pd.isna(row['Office']) or row['Building'] == '' or row['Office'] == '':
                            continue
                        
                        edit_building = str(row['Building']).strip()
                        edit_office = str(row['Office']).strip()
                        edit_key = f"{edit_building}:{edit_office}"
                        
                        if edit_key == room_key:
                            found = True
                            break
                    
                    if not found:
                        changes_made = True
                        deleted_rooms.append((building, office))
                        changes_summary.append(f"Deleted room: {building} - {office}")
                
                # Apply changes
                if changes_made:
                    # Process deleted rooms first
                    for building, office in deleted_rooms:
                        room_manager.delete_room(building, office)
                    
                    # Process added rooms
                    for building, office, capacity, is_storage in added_rooms:
                        room_manager.add_room(building, office, capacity, is_storage)
                    
                    # Process updated rooms
                    for building, office, capacity, is_storage in updated_rooms:
                        room_manager.set_capacity(building, office, capacity)
                        
                        # Update room type if needed
                        room_key = f"{building}:{office}"
                        orig_is_storage = existing_rooms.get(room_key, {}).get('IsStorage', False) if room_key in existing_rooms else False
                        
                        if orig_is_storage != is_storage:
                            # Complex update: need to update room and occupants
                            room_manager.update_room(building, office, building, office, capacity, "Storage" if is_storage else "Regular")
                    
                    # Show success message with summary of changes
                    st.success("Room information updated successfully!")
                    
                    if changes_summary:
                        with st.expander("View changes summary", expanded=True):
                            for change in changes_summary:
                                st.write(f"- {change}")
                            
                            st.info("Remember to click 'Save Changes' in the sidebar to save all changes permanently.")
                    
                    # Refresh the page to show updated data
                    st.rerun()
                else:
                    st.info("No changes detected in room information.")
                    
            except Exception as e:
                st.error(f"Error updating room information: {e}")
                st.exception(e)
    else:
        st.info("No room data available for editing")
        
        # Allow adding initial rooms if none exist
        with st.form("add_initial_room"):
            st.write("No rooms found. Add your first room:")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_building = st.text_input("Building Name", placeholder="e.g., Cockcroft")
            
            with col2:
                new_office = st.text_input("Room Number", placeholder="e.g., 3.17")
            
            with col3:
                new_capacity = st.number_input("Maximum Capacity", min_value=1, max_value=20, value=2)
            
            submitted = st.form_submit_button("Add First Room")
            
            if submitted:
                if new_building and new_office:
                    # Add room using room manager
                    room_manager.add_room(new_building, new_office, new_capacity, False)
                    
                    st.success(f"Added new room {new_office} in {new_building} with capacity {new_capacity}")
                    st.rerun()
                else:
                    st.error("Building and Room Number are required")


def show_room_status(occupant_manager, room_manager):
    """Show room status overview"""
    st.subheader("Room Status")
    
    # Create a view of all rooms and their current status with capacity information
    room_occupancy = room_manager.get_occupancy_data()
    
    if not room_occupancy.empty:
        # Allow filtering
        building_filter = st.selectbox(
            "Filter by Building", 
            ['All'] + room_occupancy['Building'].unique().tolist(), 
            key='status_building_filter'  # Added unique key
        )
        
        if building_filter != 'All':
            filtered_rooms = room_occupancy[room_occupancy['Building'] == building_filter]
        else:
            filtered_rooms = room_occupancy
        
        # Create status labels with occupancy info
        filtered_rooms['Status_Label'] = filtered_rooms.apply(
            lambda row: f"Storage" if row['IsStorage'] else
                       f"Vacant (0/{row['Max_Capacity']})" if row['Occupants'] == 0 else
                       f"Overfilled ({row['Occupants']}/{row['Max_Capacity']} - {row['Percentage']:.1f}%)" if row['Remaining'] < 0 else
                       f"Occupied ({row['Occupants']}/{row['Max_Capacity']} - {row['Percentage']:.1f}%)",
            axis=1
        )
        
        # Create display dataframe
        status_df = filtered_rooms[['Building', 'Floor', 'Office', 'Status', 'Status_Label', 
                                    'Occupants', 'Max_Capacity', 'Remaining']]
        
        # Create a color mapping function for status
        def color_status(val):
            """Color cells based on status text."""
            color_map = {
                'vacant': 'background-color: #d4edda',  # Green for vacant
                'low': 'background-color: #e6f7e1',  # Light green
                'medium': 'background-color: #fff3cd',  # Yellow
                'high': 'background-color: #ffe5d9',  # Orange
                'full': 'background-color: #f8d7da',  # Red
                'overfilled': 'background-color: #f5c6cb',  # Dark red
                'storage': 'background-color: #e2e3e5'  # Gray for storage
            }
            return color_map.get(val, '')

        # Use applymap to style the Status column
        styled_status = status_df.style.applymap(
            lambda x: color_status(x) if isinstance(x, str) else '',
            subset=['Status']
        )

        st.dataframe(styled_status, use_container_width=True)
        
        # Show status distribution
        status_counts = filtered_rooms['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        # Create a pie chart of room status
        fig = px.pie(
            status_counts, 
            values='Count', 
            names='Status',
            title="Room Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
        # Room availability by building
        st.subheader("Room Availability by Building")
        
        # Group by building and calculate availability metrics
        building_availability = filtered_rooms.groupby('Building').agg({
            'Office': 'count',
            'Occupants': 'sum',
            'Max_Capacity': 'sum',
            'Remaining': 'sum'
        }).reset_index()
        
        building_availability.rename(columns={'Office': 'Total Rooms'}, inplace=True)
        building_availability['Occupancy Rate'] = (building_availability['Occupants'] / 
                                                  building_availability['Max_Capacity'] * 100).round(1)
        
        st.dataframe(building_availability, use_container_width=True)
    else:
        st.info("No room status data available")


def show_room_assignment(occupant_manager, room_manager):
    """Show room assignment interface"""
    st.subheader("Room Assignment Interface")
    
    # Add debug information in a collapsible section
    with st.expander("Debug Information", expanded=False):
        st.write("**Current Occupants Data:**")
        st.dataframe(occupant_manager.get_current_occupants())
        st.write("**Upcoming Occupants Data:**")
        st.dataframe(occupant_manager.get_upcoming_occupants())
    
    # Get data for room occupancy
    room_occupancy = room_manager.get_occupancy_data()
    
    if not room_occupancy.empty:
        # Create a two-column layout
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.write("**Select Person**")
            
            # Option to show current or upcoming people
            person_category = st.radio("Show", ["Current Occupants", "Upcoming Occupants"], key="room_assignment_category")
            
            if person_category == "Current Occupants":
                people_df = occupant_manager.get_current_occupants()
                status_label = "Current"
            else:
                people_df = occupant_manager.get_upcoming_occupants()
                status_label = "Upcoming"
            
            # Filter to show people with and without room assignments
            if not people_df.empty:
                # Consider someone unassigned if Office or Building is missing or empty
                unassigned_mask = (
                    people_df['Office'].isna() | 
                    people_df['Building'].isna() |
                    (people_df['Office'] == '') | 
                    (people_df['Building'] == '')
                )
                
                # Also exclude STORAGE records
                not_storage_mask = ~people_df['Name'].str.contains('STORAGE', case=False, na=False)
                not_placeholder_mask = ~people_df['Name'].str.contains('PLACEHOLDER', case=False, na=False)
                eligible_mask = not_storage_mask & not_placeholder_mask
                
                # Filter for assignment-eligible people
                eligible_people = people_df[eligible_mask].copy()

                # Now add assignment status
                eligible_people.loc[unassigned_mask & eligible_mask, 'Assignment'] = "Unassigned"
                eligible_people.loc[~unassigned_mask & eligible_mask, 'Assignment'] = "Assigned"

                # Create a selectbox for people, grouping by assignment status
                assignment_filter = st.radio(
                    "Filter by", 
                    ["All", "Unassigned", "Assigned"], 
                    key="room_assignment_filter"
                )
                
                if assignment_filter != "All":
                    people_to_show = eligible_people[eligible_people['Assignment'] == assignment_filter]
                else:
                    people_to_show = eligible_people
                
                if not people_to_show.empty:
                    # Sort people alphabetically by name
                    people_to_show = people_to_show.sort_values('Name')
                    
                    # Format names to show assignment status
                    people_options = []
                    for _, person in people_to_show.iterrows():
                        name = person['Name']
                        assignment = person['Assignment']
                        display_name = f"{name} [{assignment}]"
                        people_options.append((display_name, name))
                    
                    # Create selectbox with formatted names
                    selected_display = st.selectbox(
                        "Select Person", 
                        [option[0] for option in people_options],
                        key="room_assignment_person"
                    )
                    
                    # Extract actual name
                    selected_index = [option[0] for option in people_options].index(selected_display)
                    selected_person = people_options[selected_index][1]
                    
                    # Show current assignment if any
                    person_data = people_to_show[people_to_show['Name'] == selected_person].iloc[0]
                    if person_data['Assignment'] == "Assigned":
                        st.info(f"Currently assigned to: {person_data['Building']} - Room {person_data['Office']}")
                    else:
                        st.warning("Currently unassigned")
                    
                    # Show person details
                    details = {
                        "Name": person_data['Name'],
                        "Position": person_data.get('Position', 'Not specified'),
                        "Email": person_data.get('Email address', 'Not specified')
                    }
                    
                    for label, value in details.items():
                        if pd.notna(value) and value:
                            st.write(f"**{label}:** {value}")
                else:
                    st.info(f"No {assignment_filter.lower()} {person_category.lower()} found")
                    selected_person = None
            else:
                st.info(f"No {person_category.lower()} data available")
                selected_person = None
        
        with col2:
            st.write("**Available Rooms**")
            
            # Filter controls for rooms
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                building_filter = st.selectbox(
                    "Building", 
                    ['All'] + room_occupancy['Building'].unique().tolist(),
                    key="room_assignment_building"
                )
            with col_b:
                floor_filter = st.selectbox(
                    "Floor", 
                    ['All'] + sorted(room_occupancy['Floor'].unique()),
                    key="room_assignment_floor"
                )
            with col_c:
                capacity_filter = st.multiselect(
                    "Show Rooms", 
                    ["Vacant", "Has Space", "Full", "Overfilled", "Storage"],
                    default=["Vacant", "Has Space"],
                    key="room_assignment_capacity"
                )
            
            # Apply filters
            filtered_rooms = room_occupancy.copy()
            if building_filter != 'All':
                filtered_rooms = filtered_rooms[filtered_rooms['Building'] == building_filter]
            
            if floor_filter != 'All':
                filtered_rooms = filtered_rooms[filtered_rooms['Floor'] == floor_filter]
            
            # Apply capacity filters
            capacity_conditions = []
            if "Vacant" in capacity_filter:
                capacity_conditions.append(filtered_rooms['Occupants'] == 0)
            if "Has Space" in capacity_filter:
                capacity_conditions.append((filtered_rooms['Occupants'] > 0) & (filtered_rooms['Remaining'] > 0))
            if "Full" in capacity_filter:
                capacity_conditions.append((filtered_rooms['Remaining'] == 0))
            if "Overfilled" in capacity_filter:
                capacity_conditions.append(filtered_rooms['Remaining'] < 0)
            if "Storage" in capacity_filter:
                capacity_conditions.append(filtered_rooms['IsStorage'])
            
            if capacity_conditions:
                combined_condition = capacity_conditions[0]
                for condition in capacity_conditions[1:]:
                    combined_condition = combined_condition | condition
                filtered_rooms = filtered_rooms[combined_condition]
            
            # Order by remaining capacity (most available first)
            filtered_rooms = filtered_rooms.sort_values(['Building', 'Floor', 'Remaining'], ascending=[True, True, False])
            
            if not filtered_rooms.empty:
                st.write(f"Showing {len(filtered_rooms)} rooms matching your filters")
                
                # Create a grid layout of room cards
                rooms_per_row = 3
                num_rooms = len(filtered_rooms)
                num_rows = (num_rooms + rooms_per_row - 1) // rooms_per_row
                
                for row in range(num_rows):
                    cols = st.columns(rooms_per_row)
                    for col in range(rooms_per_row):
                        idx = row * rooms_per_row + col
                        if idx < num_rooms:
                            room = filtered_rooms.iloc[idx]
                            
                            # Get room details
                            building = room['Building']
                            office = room['Office']
                            occupants = room['Occupants']
                            max_capacity = room['Max_Capacity']
                            remaining = room['Remaining']
                            percentage = room['Percentage']
                            is_storage = room['IsStorage']
                            status = room['Status']
                            
                            # Get ALL occupants for this room (both current and upcoming)
                            room_occupants = []
                            
                            # Add current occupants
                            current_df = occupant_manager.get_current_occupants()
                            current_occupants = current_df[
                                (current_df['Building'] == building) & 
                                (current_df['Office'] == office)
                            ]
                            for _, occupant in current_occupants.iterrows():
                                if "STORAGE" not in occupant['Name'] and "PLACEHOLDER" not in occupant['Name']:
                                    room_occupants.append((occupant['Name'], "Current"))
                            
                            # Add upcoming occupants
                            upcoming_df = occupant_manager.get_upcoming_occupants()
                            upcoming_occupants = upcoming_df[
                                (upcoming_df['Building'] == building) & 
                                (upcoming_df['Office'] == office)
                            ]
                            for _, occupant in upcoming_occupants.iterrows():
                                if "STORAGE" not in occupant['Name'] and "PLACEHOLDER" not in occupant['Name']:
                                    room_occupants.append((occupant['Name'], "Upcoming"))
                            
                            with cols[col]:
                                # Create room card
                                st.markdown(
                                    format_room_card(
                                        building, office, occupants, max_capacity, 
                                        remaining, percentage, is_storage, status
                                    ),
                                    unsafe_allow_html=True
                                )
                                
                                # Show room occupants (both current and upcoming)
                                if room_occupants:
                                    st.markdown("**Current occupants:**")
                                    for occupant_name, occupant_status in room_occupants:
                                        if occupant_status == "Current":
                                            st.markdown(f"- {occupant_name}")
                                    
                                    # Show upcoming occupants if any
                                    upcoming_in_room = [name for name, status in room_occupants if status == "Upcoming"]
                                    if upcoming_in_room:
                                        st.markdown("**Upcoming occupants:**")
                                        for name in upcoming_in_room:
                                            st.markdown(f"- {name}")
                                
                                # Show assign button
                                if selected_person and not is_storage:
                                    # Add a unique key for each button based on room and person
                                    btn_key = f"assign_{building}_{office}_{selected_person.replace(' ', '_')}"
                                    if st.button(f"Assign to Room {office}", key=btn_key):
                                        # Pass the status label
                                        success = occupant_manager.assign_occupant_to_room(
                                            selected_person, building, office, status_label
                                        )
                                        
                                        if success:
                                            # Update room occupancy
                                            room_manager.update_occupancy()
                                            
                                            st.success(f"✅ Assigned {selected_person} to {building} - Room {office}. Remember to save changes!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to assign {selected_person} to {building} - Room {office}.")
            else:
                st.info("No rooms match the selected filters")
    else:
        st.info("No room data available for assignment")