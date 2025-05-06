"""
Reports page for Office Room Allocation System
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

import config


def show_reports(occupant_manager, room_manager):
    """Display the reports page"""
    st.title("Office Allocation Reports")
    
    # Update occupancy data
    room_manager.update_occupancy()
    room_occupancy = room_manager.get_occupancy_data()
    
    # Create tabs for different report types
    report_tabs = st.tabs([
        "Occupancy Summary", 
        "Building Reports", 
        "Room Utilization", 
        "Occupant Reports",
        "Export Data"
    ])
    
    # Tab 1: Occupancy Summary
    with report_tabs[0]:
        show_occupancy_summary(occupant_manager, room_manager, room_occupancy)
    
    # Tab 2: Building Reports
    with report_tabs[1]:
        show_building_reports(occupant_manager, room_manager, room_occupancy)
    
    # Tab 3: Room Utilization
    with report_tabs[2]:
        show_room_utilization(occupant_manager, room_manager, room_occupancy)
    
    # Tab 4: Occupant Reports
    with report_tabs[3]:
        show_occupant_reports(occupant_manager, room_manager)
    
    # Tab 5: Export Data
    with report_tabs[4]:
        show_export_data(occupant_manager, room_manager, room_occupancy)


def show_occupancy_summary(occupant_manager, room_manager, room_occupancy):
    """Show occupancy summary report"""
    st.subheader("Occupancy Summary Report")
    
    # Display date range for the report - using datetime correctly
    col1, col2 = st.columns(2)
    with col1:
        # This fixes the error by using datetime.now() from the datetime module
        report_date = st.date_input("Report Date", datetime.now().date())
    with col2:
        st.metric("Data Last Updated", 
                 st.session_state.last_save if st.session_state.last_save else "Not saved yet")
    
    # Get summary metrics
    summary_metrics = {
        "Total Buildings": len(occupant_manager.get_unique_buildings()),
        "Total Rooms": len(occupant_manager.get_unique_offices()),
        "Current Occupants": len(occupant_manager.get_current_occupants()),
        "Upcoming Occupants": len(occupant_manager.get_upcoming_occupants()),
        "Past Occupants": len(occupant_manager.get_past_occupants())
    }
    
    # Add occupancy metrics if we have room data
    if not room_occupancy.empty:
        total_capacity = room_occupancy['Max_Capacity'].sum()
        total_occupants = room_occupancy['Occupants'].sum()
        summary_metrics.update({
            "Total Capacity": total_capacity,
            "Currently Occupied": total_occupants,
            "Available Spaces": room_occupancy['Remaining'].sum(),
            "Occupancy Rate": f"{(total_occupants / total_capacity * 100):.1f}%" if total_capacity > 0 else "0%"
        })
    
    # Display summary metrics in a nice format
    st.markdown("### Key Metrics")
    
    # Use columns to display metrics in rows of 3
    metrics = list(summary_metrics.items())
    for i in range(0, len(metrics), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(metrics):
                key, value = metrics[i + j]
                cols[j].metric(key, value)
    
    # Display occupancy trends if we have room data
    if not room_occupancy.empty:
        st.markdown("### Occupancy by Building")
        
        # Group by building
        building_occupancy = room_occupancy.groupby('Building').agg({
            'Office': 'count',
            'Occupants': 'sum',
            'Max_Capacity': 'sum',
            'Remaining': 'sum'
        }).reset_index()
        
        building_occupancy.rename(columns={'Office': 'Room Count'}, inplace=True)
        building_occupancy['Occupancy Rate'] = (building_occupancy['Occupants'] / 
                                             building_occupancy['Max_Capacity'] * 100).round(1)
        
        # Create stacked bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=building_occupancy['Building'],
            y=building_occupancy['Occupants'],
            name='Occupied',
            marker_color='#4CAF50',
            text=building_occupancy['Occupants'],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=building_occupancy['Building'],
            y=building_occupancy['Remaining'],
            name='Available',
            marker_color='#FFC107',
            text=building_occupancy['Remaining'],
            textposition='auto'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Building Occupancy',
            xaxis_title='Building',
            yaxis_title='Number of Places',
            legend_title='Status'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Comparison with upcoming occupants
        st.markdown("### Current vs. Upcoming Occupancy")
        
        # Count upcoming occupants by building
        upcoming_df = occupant_manager.get_upcoming_occupants()
        if not upcoming_df.empty and 'Building' in upcoming_df.columns:
            upcoming_by_building = upcoming_df['Building'].value_counts().reset_index()
            upcoming_by_building.columns = ['Building', 'Upcoming']
            
            # Merge with current occupancy
            merged_occupancy = building_occupancy.merge(
                upcoming_by_building, 
                on='Building', 
                how='left'
            ).fillna(0)
            
            # Create side-by-side bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=merged_occupancy['Building'],
                y=merged_occupancy['Occupants'],
                name='Current',
                marker_color='#4CAF50',
                text=merged_occupancy['Occupants'].astype(int),
                textposition='auto'
            ))
            
            fig.add_trace(go.Bar(
                x=merged_occupancy['Building'],
                y=merged_occupancy['Upcoming'],
                name='Upcoming',
                marker_color='#2196F3',
                text=merged_occupancy['Upcoming'].astype(int),
                textposition='auto'
            ))
            
            fig.update_layout(
                barmode='group',
                title='Current vs. Upcoming Occupants by Building',
                xaxis_title='Building',
                yaxis_title='Number of Occupants',
                legend_title='Status'
            )
            
            st.plotly_chart(fig, use_container_width=True)


def show_building_reports(occupant_manager, room_manager, room_occupancy):
    """Show building-specific reports"""
    st.subheader("Building Reports")
    
    # Select building to report on
    buildings = occupant_manager.get_unique_buildings()
    if not buildings:
        st.info("No building data available")
        return
        
    selected_building = st.selectbox(
        "Select Building", 
        buildings,
        key="report_building_select"
    )
    
    if selected_building:
        # Filter room data for this building
        building_rooms = room_occupancy[room_occupancy['Building'] == selected_building].copy() if not room_occupancy.empty else pd.DataFrame()
        
        if not building_rooms.empty:
            # Building summary
            st.markdown(f"### {selected_building} Summary")
            
            # Calculate building metrics
            total_rooms = len(building_rooms)
            total_capacity = building_rooms['Max_Capacity'].sum()
            total_occupants = building_rooms['Occupants'].sum()
            available_spaces = building_rooms['Remaining'].sum()
            occupancy_rate = (total_occupants / total_capacity * 100) if total_capacity > 0 else 0
            
            # Display metrics in a row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Rooms", total_rooms)
            col2.metric("Total Capacity", total_capacity)
            col3.metric("Current Occupants", total_occupants)
            col4.metric("Occupancy Rate", f"{occupancy_rate:.1f}%")
            
            # Show floors in this building
            st.markdown("### Floors Overview")
            
            # Group by floor
            floor_data = building_rooms.groupby('Floor').agg({
                'Office': 'count',
                'Occupants': 'sum',
                'Max_Capacity': 'sum',
                'Remaining': 'sum'
            }).reset_index()
            
            floor_data.rename(columns={'Office': 'Room Count'}, inplace=True)
            floor_data['Occupancy Rate'] = (floor_data['Occupants'] / floor_data['Max_Capacity'] * 100).round(1)
            
            # Sort by floor number
            floor_data['Floor_Num'] = floor_data['Floor'].apply(
                lambda x: float(x) if x.replace('.', '', 1).isdigit() else float('inf')
            )
            floor_data = floor_data.sort_values('Floor_Num').drop('Floor_Num', axis=1)
            
            # Display as a table
            st.dataframe(floor_data, use_container_width=True)
            
            # Create a visualization of rooms by floor
            st.markdown("### Room Occupancy by Floor")
            
            # Create a stacked bar chart of room occupancy by floor
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=floor_data['Floor'],
                y=floor_data['Occupants'],
                name='Occupied',
                marker_color='#4CAF50',
                text=floor_data['Occupants'].astype(int),
                textposition='auto'
            ))
            
            fig.add_trace(go.Bar(
                x=floor_data['Floor'],
                y=floor_data['Remaining'],
                name='Available',
                marker_color='#FFC107',
                text=floor_data['Remaining'].astype(int),
                textposition='auto'
            ))
            
            fig.update_layout(
                barmode='stack',
                title=f'Room Occupancy by Floor in {selected_building}',
                xaxis_title='Floor',
                yaxis_title='Number of Places',
                legend_title='Status'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # List all occupants in this building
            st.markdown("### Current Occupants")
            
            # Filter current occupants for this building
            current_df = occupant_manager.get_current_occupants()
            building_occupants = current_df[current_df['Building'] == selected_building].copy() if not current_df.empty else pd.DataFrame()
            
            if not building_occupants.empty:
                # Sort by Office (Room) for better organization
                building_occupants = building_occupants.sort_values(['Office', 'Name'])
                
                # Filter out STORAGE and PLACEHOLDER entries
                mask = ~(building_occupants['Name'].str.contains('STORAGE', case=False, na=False) | 
                         building_occupants['Name'].str.contains('PLACEHOLDER', case=False, na=False))
                building_occupants = building_occupants[mask]
                
                if not building_occupants.empty:
                    # Display table of occupants
                    st.dataframe(
                        building_occupants[['Name', 'Position', 'Office', 'Email address']],
                        use_container_width=True
                    )
                    
                    # Count occupants by position
                    if 'Position' in building_occupants.columns:
                        position_counts = building_occupants['Position'].value_counts()
                        
                        # Create pie chart of positions
                        if len(position_counts) > 0:
                            st.markdown("### Occupants by Position")
                            fig = px.pie(
                                values=position_counts.values,
                                names=position_counts.index,
                                title=f"Positions in {selected_building}"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No occupants in {selected_building} (only storage or placeholders)")
            else:
                st.info(f"No current occupants in {selected_building}")
        else:
            st.warning(f"No room data available for {selected_building}")


def show_room_utilization(occupant_manager, room_manager, room_occupancy):
    """Show room utilization report"""
    st.subheader("Room Utilization Report")
    
    if not room_occupancy.empty:
        # Show rooms organized by status
        st.markdown("### Rooms by Utilization Status")
        
        # Count rooms by status
        status_counts = room_occupancy['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        # Display counts
        st.dataframe(status_counts, use_container_width=True)
        
        # Create status chart
        fig = px.pie(
            status_counts, 
            values='Count', 
            names='Status',
            title="Room Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
        # List rooms that need attention (high utilization, full, or vacant)
        st.markdown("### Rooms Requiring Attention")
        
        # Create tabs for different categories
        attention_tabs = st.tabs([
            "Overfilled Rooms",
            "Full Rooms", 
            "Vacant Rooms"
        ])
        
        # Tab 1: Overfilled Rooms
        with attention_tabs[0]:
            overfilled_rooms = room_occupancy[room_occupancy['Status'] == 'overfilled'].copy()
            
            if not overfilled_rooms.empty:
                st.error(f"⚠️ There are {len(overfilled_rooms)} rooms that are overfilled (exceeding capacity)")
                
                # Display the overfilled rooms
                st.dataframe(
                    overfilled_rooms[['Building', 'Floor', 'Office', 'Occupants', 'Max_Capacity', 'Remaining']],
                    use_container_width=True
                )
                
                # For each overfilled room, show occupants
                st.markdown("### Occupants of Overfilled Rooms")
                
                for _, room in overfilled_rooms.iterrows():
                    building = room['Building']
                    office = room['Office']
                    
                    # Get occupants for this room
                    current_df = occupant_manager.get_current_occupants()
                    room_occupants = current_df[
                        (current_df['Building'] == building) &
                        (current_df['Office'] == office)
                    ]
                    
                    # Filter out STORAGE and PLACEHOLDER entries
                    mask = ~(room_occupants['Name'].str.contains('STORAGE', case=False, na=False) | 
                             room_occupants['Name'].str.contains('PLACEHOLDER', case=False, na=False))
                    room_occupants = room_occupants[mask]
                    
                    if not room_occupants.empty:
                        st.markdown(f"**{building} - Room {office}**")
                        
                        for _, occupant in room_occupants.iterrows():
                            st.markdown(f"- {occupant['Name']} ({occupant.get('Position', 'No position')})")
            else:
                st.success("No rooms are currently overfilled")
        
        # Tab 2: Full Rooms
        with attention_tabs[1]:
            full_rooms = room_occupancy[room_occupancy['Status'] == 'full'].copy()
            
            if not full_rooms.empty:
                st.warning(f"There are {len(full_rooms)} rooms at full capacity")
                
                # Display the full rooms
                st.dataframe(
                    full_rooms[['Building', 'Floor', 'Office', 'Occupants', 'Max_Capacity']],
                    use_container_width=True
                )
                
                # For each full room, show occupants
                st.markdown("### Occupants of Full Rooms")
                
                for _, room in full_rooms.iterrows():
                    building = room['Building']
                    office = room['Office']
                    
                    # Get occupants for this room
                    current_df = occupant_manager.get_current_occupants()
                    room_occupants = current_df[
                        (current_df['Building'] == building) &
                        (current_df['Office'] == office)
                    ]
                    
                    # Filter out STORAGE and PLACEHOLDER entries
                    mask = ~(room_occupants['Name'].str.contains('STORAGE', case=False, na=False) | 
                             room_occupants['Name'].str.contains('PLACEHOLDER', case=False, na=False))
                    room_occupants = room_occupants[mask]
                    
                    if not room_occupants.empty:
                        st.markdown(f"**{building} - Room {office}**")
                        
                        for _, occupant in room_occupants.iterrows():
                            st.markdown(f"- {occupant['Name']} ({occupant.get('Position', 'No position')})")
            else:
                st.success("No rooms are currently at full capacity")
        
        # Tab 3: Vacant Rooms
        with attention_tabs[2]:
            vacant_rooms = room_occupancy[room_occupancy['Status'] == 'vacant'].copy()
            
            if not vacant_rooms.empty:
                st.info(f"There are {len(vacant_rooms)} vacant rooms that could be utilized")
                
                # Display the vacant rooms
                vacant_rooms = vacant_rooms.sort_values(['Building', 'Floor', 'Office'])
                
                st.dataframe(
                    vacant_rooms[['Building', 'Floor', 'Office', 'Max_Capacity']],
                    use_container_width=True
                )
                
                # Show distribution of vacant rooms by building
                vacant_by_building = vacant_rooms.groupby('Building').size().reset_index(name='Vacant Rooms')
                
                fig = px.bar(
                    vacant_by_building,
                    x='Building',
                    y='Vacant Rooms',
                    title='Vacant Rooms by Building',
                    text='Vacant Rooms'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("All rooms are currently occupied")
        
        # Add a summary table of all rooms
        st.markdown("### Complete Room Utilization Table")
        
        # Create a formatted table with all rooms
        room_table = room_occupancy.sort_values(['Building', 'Floor', 'Office'])
        
        # Display the table
        st.dataframe(
            room_table[['Building', 'Floor', 'Office', 'Occupants', 
                     'Max_Capacity', 'Remaining', 'Percentage', 'Status']],
            use_container_width=True
        )
    else:
        st.info("No room occupancy data available")


def show_occupant_reports(occupant_manager, room_manager):
    """Show occupant reports"""
    st.subheader("Occupant Reports")
    
    # Create tabs for occupant reports
    occupant_tabs = st.tabs([
        "Current Occupants", 
        "Upcoming Occupants", 
        "Past Occupants", 
        "Position Analysis"
    ])
    
    # Tab 1: Current Occupants
    with occupant_tabs[0]:
        current_df = occupant_manager.get_current_occupants()
        if not current_df.empty:
            # Filter out STORAGE and PLACEHOLDER entries
            mask = ~(current_df['Name'].str.contains('STORAGE', case=False, na=False) | 
                     current_df['Name'].str.contains('PLACEHOLDER', case=False, na=False))
            filtered_current = current_df[mask]
            
            if not filtered_current.empty:
                st.markdown(f"### Current Occupants ({len(filtered_current)})")
                
                # Allow filtering
                filter_options = st.multiselect(
                    "Filter by Building", 
                    occupant_manager.get_unique_buildings(),
                    key="curr_occupant_filter"
                )
                
                # Filter data if needed
                if filter_options:
                    filtered_occupants = filtered_current[
                        filtered_current['Building'].isin(filter_options)
                    ]
                else:
                    filtered_occupants = filtered_current
                
                # Sort by building and room for better organization
                filtered_occupants = filtered_occupants.sort_values(['Building', 'Office', 'Name'])
                
                # Display the table
                st.dataframe(
                    filtered_occupants[['Name', 'Position', 'Building', 'Office', 'Email address']],
                    use_container_width=True
                )
                
                # Create a summary chart
                occupants_by_building = filtered_occupants['Building'].value_counts().reset_index()
                occupants_by_building.columns = ['Building', 'Occupants']
                
                fig = px.bar(
                    occupants_by_building,
                    x='Building',
                    y='Occupants',
                    title='Current Occupants by Building',
                    text='Occupants'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No occupants found (only storage or placeholders)")
        else:
            st.info("No current occupants data available")
    
    # Tab 2: Upcoming Occupants
    with occupant_tabs[1]:
        upcoming_df = occupant_manager.get_upcoming_occupants()
        if not upcoming_df.empty:
            st.markdown(f"### Upcoming Occupants ({len(upcoming_df)})")
            
            # Display the table
            st.dataframe(
                upcoming_df[['Name', 'Position', 'Building', 'Office', 'Email address']],
                use_container_width=True
            )
            
            # Create a summary chart if we have building information
            if 'Building' in upcoming_df.columns:
                upcoming_by_building = upcoming_df['Building'].value_counts().reset_index()
                upcoming_by_building.columns = ['Building', 'Upcoming']
                fig = px.bar(
                    upcoming_by_building,
                    x='Building',
                    y='Upcoming',
                    title='Upcoming Occupants by Building',
                    text='Upcoming'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No upcoming occupants data available")
    
    # Tab 3: Past Occupants
    with occupant_tabs[2]:
        past_df = occupant_manager.get_past_occupants()
        if not past_df.empty:
            st.markdown(f"### Past Occupants ({len(past_df)})")
            
            # Add search functionality
            search_term = st.text_input("Search by name, position, or email", key="past_report_search")
            
            filtered_past = past_df
            
            if search_term:
                filtered_past = filtered_past[
                    filtered_past['Name'].str.contains(search_term, case=False, na=False) |
                    filtered_past['Position'].str.contains(search_term, case=False, na=False) |
                    filtered_past['Email address'].str.contains(search_term, case=False, na=False)
                ]
            
            # Display the table
            st.dataframe(
                filtered_past[['Name', 'Position', 'Building', 'Office', 'Email address']],
                use_container_width=True
            )
            
            # Show timeline of departures if we have date information
            if 'End Date' in filtered_past.columns:
                st.markdown("### Departures Timeline")
                
                # Count departures by month
                filtered_past['End_Month'] = pd.to_datetime(filtered_past['End Date']).dt.strftime('%Y-%m')
                departures_by_month = filtered_past['End_Month'].value_counts().sort_index().reset_index()
                departures_by_month.columns = ['Month', 'Departures']
                
                fig = px.line(
                    departures_by_month,
                    x='Month',
                    y='Departures',
                    title='Past Occupants Departure Timeline',
                    markers=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No past occupants data available")
    
    # Tab 4: Position Analysis
    with occupant_tabs[3]:
        current_df = occupant_manager.get_current_occupants()
        if not current_df.empty and 'Position' in current_df.columns:
            # Filter out STORAGE and PLACEHOLDER entries
            mask = ~(current_df['Name'].str.contains('STORAGE', case=False, na=False) | 
                     current_df['Name'].str.contains('PLACEHOLDER', case=False, na=False))
            filtered_current = current_df[mask]
            
            if not filtered_current.empty:
                st.markdown("### Occupant Position Analysis")
                
                # Get position counts
                position_counts = filtered_current['Position'].fillna('Not Specified').value_counts()
                
                # If there are too many positions, group smaller ones
                if len(position_counts) > 8:
                    top_positions = position_counts.head(7)
                    other_count = position_counts.tail(len(position_counts) - 7).sum()
                    position_counts = pd.concat([top_positions, pd.Series([other_count], index=['Other'])])
                
                # Create dataframe for visualization
                position_df = position_counts.reset_index()
                position_df.columns = ['Position', 'Count']
                
                # Create pie chart
                fig = px.pie(
                    position_df,
                    values='Count',
                    names='Position',
                    title='Current Occupants by Position'
                )
                
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Show positions by building
                st.markdown("### Positions by Building")
                
                # Create a crosstab of building vs position
                building_position = pd.crosstab(
                    filtered_current['Building'], 
                    filtered_current['Position'].fillna('Not Specified')
                ).reset_index()
                
                # Display the crosstab
                st.dataframe(building_position, use_container_width=True)
                
                # Create a stacked bar chart
                position_building_data = []
                
                for position in position_df['Position']:
                    if position in building_position.columns:
                        for building in building_position['Building']:
                            position_count = building_position.loc[
                                building_position['Building'] == building, 
                                position
                            ].values[0]
                            
                            position_building_data.append({
                                'Building': building,
                                'Position': position,
                                'Count': position_count
                            })
                
                if position_building_data:
                    position_building_df = pd.DataFrame(position_building_data)
                    
                    fig = px.bar(
                        position_building_df,
                        x='Building',
                        y='Count',
                        color='Position',
                        title='Positions by Building',
                        barmode='stack'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No occupants found (only storage or placeholders)")
        else:
            st.info("No position data available for analysis")


def show_export_data(occupant_manager, room_manager, room_occupancy):
    """Show export data interface"""
    st.subheader("Export Data")
    
    # Create tabs for different export options
    export_tabs = st.tabs([
        "CSV Export", 
        "Excel Reports", 
        "Building Summary"
    ])
    
    # Tab 1: CSV Export
    with export_tabs[0]:
        st.markdown("### Export Data as CSV")
        
        # Create export options
        export_options = st.multiselect(
            "Select data to export",
            ["Current Occupants", "Upcoming Occupants", "Past Occupants", "Room Utilization"],
            default=["Current Occupants"]
        )
        
        if st.button("Generate CSV Files"):
            # Create a temporary directory for exports
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = f"data/export_{timestamp}"
            os.makedirs(export_dir, exist_ok=True)
            
            exported_files = []
            
            # Export selected dataframes
            if "Current Occupants" in export_options:
                current_df = occupant_manager.get_current_occupants()
                if not current_df.empty:
                    current_file = f"{export_dir}/current_occupants.csv"
                    current_df.to_csv(current_file, index=False)
                    exported_files.append(("Current Occupants", current_file))
            
            if "Upcoming Occupants" in export_options:
                upcoming_df = occupant_manager.get_upcoming_occupants()
                if not upcoming_df.empty:
                    upcoming_file = f"{export_dir}/upcoming_occupants.csv"
                    upcoming_df.to_csv(upcoming_file, index=False)
                    exported_files.append(("Upcoming Occupants", upcoming_file))
            
            if "Past Occupants" in export_options:
                past_df = occupant_manager.get_past_occupants()
                if not past_df.empty:
                    past_file = f"{export_dir}/past_occupants.csv"
                    past_df.to_csv(past_file, index=False)
                    exported_files.append(("Past Occupants", past_file))
            
            if "Room Utilization" in export_options and not room_occupancy.empty:
                rooms_file = f"{export_dir}/room_utilization.csv"
                room_occupancy.to_csv(rooms_file, index=False)
                exported_files.append(("Room Utilization", rooms_file))
            
            # Display download links
            if exported_files:
                st.success(f"Generated {len(exported_files)} CSV files")
                
                for name, file_path in exported_files:
                    with open(file_path, "rb") as file:
                        st.download_button(
                            label=f"Download {name} CSV",
                            data=file,
                            file_name=os.path.basename(file_path),
                            mime="text/csv",
                            key=f"dl_{name}"
                        )
            else:
                st.error("No files were exported. Please select data to export.")
    
    # Tab 2: Excel Reports
    with export_tabs[1]:
        st.markdown("### Generate Excel Report")
        
        # Create report options
        report_type = st.radio(
            "Report Type",
            ["Full Office Allocation Report", "Building-Specific Report", "Utilization Summary"]
        )
        
        if report_type == "Building-Specific Report":
            report_building = st.selectbox(
                "Select Building",
                occupant_manager.get_unique_buildings(),
                key="excel_report_building"
            )
        
        if st.button("Generate Excel Report"):
            # Create Excel file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if report_type == "Full Office Allocation Report":
                report_file = f"data/Full_Office_Report_{timestamp}.xlsx"
                
                # Get dataframes
                current_df = occupant_manager.get_current_occupants()
                upcoming_df = occupant_manager.get_upcoming_occupants()
                
                # Create a writer
                with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
                    # Current occupants
                    if not current_df.empty:
                        current_df.to_excel(writer, sheet_name='Current Occupants', index=False)
                    
                    # Upcoming occupants
                    if not upcoming_df.empty:
                        upcoming_df.to_excel(writer, sheet_name='Upcoming Occupants', index=False)
                    
                    # Room data
                    if not room_occupancy.empty:
                        room_occupancy.to_excel(writer, sheet_name='Room Utilization', index=False)
                    
                    # Summary sheet
                    summary_data = [
                        ["Office Allocation Report", "", ""],
                        ["Generated on", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""],
                        ["", "", ""],
                        ["Metric", "Value", ""],
                        ["Total Buildings", len(occupant_manager.get_unique_buildings()), ""],
                        ["Total Rooms", len(occupant_manager.get_unique_offices()), ""],
                        ["Current Occupants", len(current_df), ""],
                        ["Upcoming Occupants", len(upcoming_df), ""],
                        ["Past Occupants", len(occupant_manager.get_past_occupants()), ""]
                    ]
                    
                    # Add occupancy metrics if we have room data
                    if not room_occupancy.empty:
                        occupancy_rate = (room_occupancy['Occupants'].sum() / 
                                         room_occupancy['Max_Capacity'].sum() * 100) if room_occupancy['Max_Capacity'].sum() > 0 else 0
                        
                        summary_data.extend([
                            ["Total Capacity", room_occupancy['Max_Capacity'].sum(), ""],
                            ["Currently Occupied", room_occupancy['Occupants'].sum(), ""],
                            ["Available Spaces", room_occupancy['Remaining'].sum(), ""],
                            ["Occupancy Rate", f"{occupancy_rate:.1f}%", ""]
                        ])
                    
                    # Create summary sheet
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False, header=False)
                
                # Provide download link
                with open(report_file, "rb") as file:
                    st.download_button(
                        label="Download Full Report",
                        data=file,
                        file_name=os.path.basename(report_file),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_full_report"
                    )
            
            elif report_type == "Building-Specific Report" and report_building:
                report_file = f"data/{report_building}_Report_{timestamp}.xlsx"
                
                # Filter data for this building
                current_df = occupant_manager.get_current_occupants()
                current_building = current_df[
                    current_df['Building'] == report_building
                ] if not current_df.empty else pd.DataFrame()
                
                upcoming_df = occupant_manager.get_upcoming_occupants()
                upcoming_building = upcoming_df[
                    upcoming_df['Building'] == report_building
                ] if not upcoming_df.empty else pd.DataFrame()
                
                building_rooms = room_occupancy[
                    room_occupancy['Building'] == report_building
                ] if not room_occupancy.empty else pd.DataFrame()
                
                # Create a writer
                with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
                    # Write sheets
                    if not current_building.empty:
                        current_building.to_excel(writer, sheet_name='Current Occupants', index=False)
                    
                    if not upcoming_building.empty:
                        upcoming_building.to_excel(writer, sheet_name='Upcoming Occupants', index=False)
                    
                    if not building_rooms.empty:
                        building_rooms.to_excel(writer, sheet_name='Rooms', index=False)
                    
                    # Summary sheet
                    total_rooms = len(building_rooms) if not building_rooms.empty else 0
                    total_capacity = building_rooms['Max_Capacity'].sum() if not building_rooms.empty else 0
                    total_occupants = building_rooms['Occupants'].sum() if not building_rooms.empty else 0
                    available_spaces = building_rooms['Remaining'].sum() if not building_rooms.empty else 0
                    occupancy_rate = (total_occupants / total_capacity * 100) if total_capacity > 0 else 0
                    
                    summary_data = [
                        [f"{report_building} Building Report", "", ""],
                        ["Generated on", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""],
                        ["", "", ""],
                        ["Metric", "Value", ""],
                        ["Total Rooms", total_rooms, ""],
                        ["Total Capacity", total_capacity, ""],
                        ["Current Occupants", total_occupants, ""],
                        ["Available Spaces", available_spaces, ""],
                        ["Occupancy Rate", f"{occupancy_rate:.1f}%", ""],
                        ["Upcoming Occupants", len(upcoming_building), ""]
                    ]
                    
                    # Create summary sheet
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False, header=False)
                
                # Provide download link
                with open(report_file, "rb") as file:
                    st.download_button(
                        label=f"Download {report_building} Report",
                        data=file,
                        file_name=os.path.basename(report_file),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_building_report"
                    )
            
            elif report_type == "Utilization Summary":
                report_file = f"data/Utilization_Summary_{timestamp}.xlsx"
                
                if not room_occupancy.empty:
                    # Create a writer
                    with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
                        # All rooms with utilization
                        room_occupancy.to_excel(writer, sheet_name='All Rooms', index=False)
                        
                        # Full rooms
                        full_rooms = room_occupancy[room_occupancy['Status'] == 'full']
                        if not full_rooms.empty:
                            full_rooms.to_excel(writer, sheet_name='Full Rooms', index=False)
                        
                        # Overfilled rooms
                        overfilled_rooms = room_occupancy[room_occupancy['Status'] == 'overfilled']
                        if not overfilled_rooms.empty:
                            overfilled_rooms.to_excel(writer, sheet_name='Overfilled Rooms', index=False)
                        
                        # Vacant rooms
                        vacant_rooms = room_occupancy[room_occupancy['Status'] == 'vacant']
                        if not vacant_rooms.empty:
                            vacant_rooms.to_excel(writer, sheet_name='Vacant Rooms', index=False)
                        
                        # Summary by building
                        building_summary = room_occupancy.groupby('Building').agg({
                            'Office': 'count',
                            'Occupants': 'sum',
                            'Max_Capacity': 'sum',
                            'Remaining': 'sum'
                        }).reset_index()
                        
                        building_summary.rename(columns={'Office': 'Room Count'}, inplace=True)
                        building_summary['Occupancy Rate'] = (building_summary['Occupants'] / 
                                                          building_summary['Max_Capacity'] * 100).round(1)
                        
                        building_summary.to_excel(writer, sheet_name='Building Summary', index=False)
                    
                    # Provide download link
                    with open(report_file, "rb") as file:
                        st.download_button(
                            label="Download Utilization Report",
                            data=file,
                            file_name=os.path.basename(report_file),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_util_report"
                        )
                else:
                    st.error("No room data available to generate utilization report")
    
    # Tab 3: Building Summary
    with export_tabs[2]:
        st.markdown("### Building Summary Report")
        
        # Generate a summary of all buildings
        if not room_occupancy.empty:
            # Create building summary
            building_summary = room_occupancy.groupby('Building').agg({
                'Office': 'count',
                'Occupants': 'sum',
                'Max_Capacity': 'sum',
                'Remaining': 'sum'
            }).reset_index()
            
            building_summary.rename(columns={'Office': 'Room Count'}, inplace=True)
            building_summary['Occupancy Rate'] = (building_summary['Occupants'] / 
                                              building_summary['Max_Capacity'] * 100).round(1)
            
            # Display summary table
            st.dataframe(building_summary, use_container_width=True)
            
            # Create a visualization
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add bars for room count
            fig.add_trace(
                go.Bar(
                    x=building_summary['Building'],
                    y=building_summary['Room Count'],
                    name='Room Count',
                    marker_color='#4CAF50'
                ),
                secondary_y=False
            )
            
            # Add line for occupancy rate
            fig.add_trace(
                go.Scatter(
                    x=building_summary['Building'],
                    y=building_summary['Occupancy Rate'],
                    name='Occupancy Rate (%)',
                    mode='lines+markers',
                    marker_color='#FFC107',
                    line=dict(width=3)
                ),
                secondary_y=True
            )
            
            # Set titles
            fig.update_layout(
                title_text='Building Summary',
                xaxis_title='Building'
            )
            
            fig.update_yaxes(title_text='Room Count', secondary_y=False)
            fig.update_yaxes(title_text='Occupancy Rate (%)', secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Export as CSV
            building_csv = building_summary.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Building Summary CSV",
                data=building_csv,
                file_name=f"building_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No room data available for building summary")