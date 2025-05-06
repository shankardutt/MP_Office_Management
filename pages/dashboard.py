"""
Dashboard page for Office Room Allocation System
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

from utils import create_occupancy_chart, create_capacity_chart


def show_dashboard(occupant_manager, room_manager):
    """Display the dashboard page"""
    st.title("Office Allocation Dashboard")
    
    # Update occupancy data
    room_manager.update_occupancy()
    room_occupancy = room_manager.get_occupancy_data()
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_count = len(occupant_manager.get_current_occupants())
        st.metric("Current Occupants", current_count)
    
    with col2:
        upcoming_count = len(occupant_manager.get_upcoming_occupants())
        st.metric("Upcoming Occupants", upcoming_count)
    
    with col3:
        past_count = len(occupant_manager.get_past_occupants())
        st.metric("Past Occupants", past_count)
    
    with col4:
        # Calculate capacity metrics
        if not room_occupancy.empty:
            total_capacity = room_occupancy['Max_Capacity'].sum()
            current_occupancy = room_occupancy['Occupants'].sum()
            occupancy_percentage = (current_occupancy / total_capacity * 100) if total_capacity > 0 else 0
            st.metric("Occupancy Rate", f"{occupancy_percentage:.1f}%")
        else:
            st.metric("Occupancy Rate", "0.0%")
    
    # Main dashboard sections
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("Room Occupancy by Building and Floor")
        
        if not room_occupancy.empty:
            # Filter by building if needed
            if st.session_state.filter_building != 'All':
                filtered_occupancy = room_occupancy[room_occupancy['Building'] == st.session_state.filter_building]
            else:
                filtered_occupancy = room_occupancy
            
            # Group by building and floor for the visualization
            building_floor_occupancy = filtered_occupancy.groupby(['Building', 'Floor']).agg({
                'Occupants': 'sum',
                'Max_Capacity': 'sum',
                'Office': 'count'
            }).reset_index()
            
            building_floor_occupancy.rename(columns={'Office': 'Room Count'}, inplace=True)
            building_floor_occupancy['Occupancy Rate'] = (building_floor_occupancy['Occupants'] / 
                                                        building_floor_occupancy['Max_Capacity'] * 100).round(1)
            
            # Show the summary table
            st.dataframe(building_floor_occupancy, use_container_width=True)
            
            # Create occupancy chart
            fig = create_occupancy_chart(building_floor_occupancy)
            st.plotly_chart(fig, use_container_width=True)
            
            # Room capacity distribution
            st.subheader("Room Capacity Utilization")
            
            # Create capacity chart
            fig = create_capacity_chart(filtered_occupancy)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No occupancy data available")
    
    with col_right:
        # Status Distribution
        st.subheader("Occupant Status Distribution")
        
        current_df = occupant_manager.get_current_occupants()
        if not current_df.empty and 'Status' in current_df.columns:
            status_counts = current_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            # Consolidate rare statuses
            if len(status_counts) > 5:
                main_statuses = status_counts.head(4)
                other_count = status_counts.tail(len(status_counts) - 4)['Count'].sum()
                main_statuses = pd.concat([
                    main_statuses, 
                    pd.DataFrame([{'Status': 'Other', 'Count': other_count}])
                ])
                status_counts = main_statuses
            
            fig = px.pie(
                status_counts,
                values='Count',
                names='Status',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            
            fig.update_layout(height=300)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")
        
        # Buildings Distribution
        st.subheader("Occupants by Building")
        
        if not current_df.empty and 'Building' in current_df.columns:
            building_counts = current_df['Building'].value_counts().reset_index()
            building_counts.columns = ['Building', 'Count']
            
            fig = px.bar(
                building_counts,
                x='Building',
                y='Count',
                color='Building',
                text='Count',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            
            fig.update_layout(
                xaxis_title='Building Name',
                yaxis_title='Number of Occupants',
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No building data available")
        
        # Position/Role Distribution
        st.subheader("Occupants by Position")
        
        if not current_df.empty and 'Position' in current_df.columns:
            # Define standard academic position categories
            academic_positions = [
                'Undergraduate Student',
                'Honours Student',
                'Visiting Student',
                'PhD Student',
                'Postdoctoral Fellow',
                'Research Fellow',
                'Fellow',
                'Associate Professor',
                'Professor',
                'Emeritus Professor',
                'Distinguished Professor',
                'Technical Officer'
            ]
            
            # Create a function to standardize position names
            def standardize_position(position):
                if pd.isna(position) or position == '':
                    return 'Unknown'
                
                # Convert to string if not already
                position = str(position).strip()
                position_lower = position.lower().strip()
                
                # Check for exact matches first
                for std_position in academic_positions:
                    if std_position.lower() == position_lower:
                        return std_position
                
                # Handle Professor categories with more precision - check for specific modifiers first
                if 'distinguished professor' in position_lower or re.search(r'\bdist\.?\s+prof', position_lower):
                    return 'Distinguished Professor'
                elif 'emeritus professor' in position_lower or re.search(r'\bemer\.?\s+prof', position_lower):
                    return 'Emeritus Professor'
                elif re.search(r'\bassoc\.?\s+prof', position_lower) or 'associate professor' in position_lower:
                    return 'Associate Professor'
                elif re.search(r'\bprof', position_lower):
                    # If it just has 'prof' without the above modifiers, it's a regular professor
                    if not any(x in position_lower for x in ['associate', 'assoc', 'emeritus', 'emer', 'distinguished', 'dist']):
                        return 'Professor'
                
                # Handle student categories
                if ('undergraduate' in position_lower) or ('student' in position_lower and not any(x in position_lower for x in ['phd', 'honour', 'honor', 'visiting', 'graduate'])):
                    return 'Undergraduate Student'
                elif 'honour' in position_lower or 'honor' in position_lower:
                    return 'Honours Student'
                elif 'phd' in position_lower or 'doctoral' in position_lower:
                    return 'PhD Student'
                elif 'visit' in position_lower and 'student' in position_lower:
                    return 'Visiting Student'
                
                # Other academic positions
                if 'postdoc' in position_lower or 'post-doc' in position_lower or 'postdoctoral fellow' in position_lower:
                    return 'Postdoctoral Fellow'
                elif 'research fellow' in position_lower:
                    return 'Research Fellow'
                elif 'fellow' in position_lower:
                    return 'Fellow'
                elif 'technical officer' in position_lower or 'tech officer' in position_lower:
                    return 'Technical Officer'
                
                # If no matching categories, check for partial matches
                for std_position in academic_positions:
                    if std_position.lower() in position_lower:
                        return std_position
                
                # Default to Other if no match found
                return 'Other'
            
            # Apply standardization to positions
            current_df['Standardized_Position'] = current_df['Position'].apply(standardize_position)
            
            # For debugging
            # Debug display of position standardization
            with st.expander("Position Standardization Debug (click to expand)"):
                debug_df = current_df[['Name', 'Position', 'Standardized_Position']].copy()
                debug_df = debug_df[~debug_df['Name'].str.contains('STORAGE', case=False, na=False)]
                debug_df = debug_df[~debug_df['Name'].str.contains('PLACEHOLDER', case=False, na=False)]
                st.dataframe(debug_df, use_container_width=True)
            
            # Filter out STORAGE and PLACEHOLDER entries
            filtered_current = current_df[
                ~current_df['Name'].str.contains('STORAGE', case=False, na=False) & 
                ~current_df['Name'].str.contains('PLACEHOLDER', case=False, na=False)
            ]
            
            # Count standardized positions
            position_counts = filtered_current['Standardized_Position'].value_counts()
            
            # Ensure all academic positions are represented (even with zero count)
            for position in academic_positions:
                if position not in position_counts.index:
                    position_counts[position] = 0
            
            # Sort by academic hierarchy
            position_order = academic_positions + ['Other', 'Unknown']
            position_df = position_counts.reset_index()
            position_df.columns = ['Position', 'Count']
            position_df['Position'] = pd.Categorical(
                position_df['Position'], 
                categories=position_order, 
                ordered=True
            )
            position_df = position_df.sort_values('Position')
            
            # Create horizontal bar chart
            fig = px.bar(
                position_df,
                x='Count',
                y='Position',
                color='Count',
                orientation='h',
                text='Count',
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                xaxis_title='Number of Occupants',
                yaxis_title='Position',
                height=450,  # Increased height to fit all categories
                yaxis={'categoryorder': 'array', 'categoryarray': position_order},
                coloraxis_showscale=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No position data available")
    
    # Quick access to upcoming occupants
    upcoming_df = occupant_manager.get_upcoming_occupants()
    if not upcoming_df.empty:
        st.subheader("Upcoming Occupants")
        upcoming_preview = upcoming_df.head(5)
        st.dataframe(upcoming_preview, use_container_width=True)
        
        if len(upcoming_df) > 5:
            st.caption(f"Showing 5 of {len(upcoming_df)} upcoming occupants. Go to Upcoming Occupants page to see all.")