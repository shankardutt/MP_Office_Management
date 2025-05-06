"""
Utility functions for Office Room Allocation System
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

import config


def apply_custom_css():
    """Apply custom CSS to the Streamlit app"""
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stAlert {
        border-radius: 10px;
    }
    .room-vacant {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #28a745;
    }
    .room-low {
        background-color: #e6f7e1;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #5cb85c;
    }
    .room-medium {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #ffc107;
    }
    .room-high {
        background-color: #ffe5d9;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #fd7e14;
    }
    .room-full {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #dc3545;
    }
    .room-overfilled {
        background-color: #f5c6cb;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #b21f2d;
    }
    .room-storage {
        background-color: #e2e3e5;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 5px solid #6c757d;
    }
    .occupant-tag {
        display: inline-block;
        background-color: #e9ecef;
        padding: 2px 8px;
        border-radius: 12px;
        margin: 2px;
        font-size: 0.8em;
    }
    .status-current {
        background-color: #d4edda;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        color: #155724;
    }
    .status-upcoming {
        background-color: #cce5ff;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        color: #004085;
    }
    .status-past {
        background-color: #f8d7da;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        color: #721c24;
    }
    .floor-heading {
        background-color: #f1f3f5;
        padding: 5px 10px;
        border-radius: 5px;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .dataframe th {
        font-size: 14px;
        font-weight: bold;
        background-color: #f1f3f5;
    }
    .dataframe td {
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)


def format_room_card(building, office, occupants, max_capacity, remaining, percentage, is_storage, status):
    """Format room card HTML based on occupancy status"""
    
    # Determine status text
    if is_storage:
        status_text = "Storage Room"
    elif occupants == 0:
        status_text = f"Vacant ({max_capacity} available)"
    elif remaining < 0:
        status_text = f"Overfilled! ({abs(remaining)} over capacity)"
    elif remaining > 0:
        status_text = f"Has Space ({remaining} available)"
    else:
        status_text = f"Full ({occupants}/{max_capacity})"
    
    # Get status class
    status_class = f"room-{status}"
    
    # Create HTML
    html = f"""
    <div class="{status_class}">
        <h4 style="margin:0;">{building} - {office}</h4>
        <p style="margin:0;">{status_text}</p>
        <p style="margin:0;">Occupancy: {occupants}/{max_capacity} ({percentage:.1f}%)</p>
    </div>
    """
    
    return html


def create_occupancy_chart(building_floor_occupancy):
    """Create a stacked bar chart of occupancy by building and floor"""
    fig = go.Figure()
    
    for building in building_floor_occupancy['Building'].unique():
        building_data = building_floor_occupancy[building_floor_occupancy['Building'] == building]
        
        fig.add_trace(go.Bar(
            x=building_data['Floor'],
            y=building_data['Occupants'],
            name=f"{building} - Occupants",
            marker_color='#4CAF50',
            text=building_data['Occupants'],
            textposition='auto',
            hovertemplate=
            '<b>%{x}</b><br>' +
            'Building: ' + building + '<br>' +
            'Occupants: %{y}<br>' +
            'Capacity: %{customdata[0]}<br>' +
            'Occupancy Rate: %{customdata[1]}%<br>' +
            'Room Count: %{customdata[2]}',
            customdata=pd.DataFrame({
                'Max_Capacity': building_data['Max_Capacity'],
                'Occupancy Rate': building_data['Occupancy Rate'],
                'Room Count': building_data['Room Count']
            }).values
        ))
        
        fig.add_trace(go.Bar(
            x=building_data['Floor'],
            y=building_data['Max_Capacity'] - building_data['Occupants'],
            name=f"{building} - Available",
            marker_color='#FFC107',
            text=building_data['Max_Capacity'] - building_data['Occupants'],
            textposition='auto',
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        barmode='stack',
        title='Occupancy by Building and Floor',
        xaxis_title='Floor',
        yaxis_title='Number of People',
        height=500,
        legend_title='Occupancy Status',
        hovermode='closest'
    )
    
    return fig


def create_capacity_chart(room_occupancy):
    """Create a bar chart of room capacity utilization"""
    
    # Define capacity categories and their order
    status_order = ['vacant', 'low', 'medium', 'high', 'full', 'overfilled', 'storage']
    status_labels = {
        'vacant': 'Vacant', 
        'low': 'Low (1-25%)', 
        'medium': 'Medium (26-50%)', 
        'high': 'High (51-75%)', 
        'full': 'Full (76-100%)',
        'overfilled': 'Overfilled (>100%)', 
        'storage': 'Storage'
    }
    
    # Count rooms by status
    status_counts = room_occupancy['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Map internal status to display labels
    status_counts['Status_Label'] = status_counts['Status'].map(status_labels)
    
    # Create color map
    color_map = {
        status_labels['vacant']: '#d4edda',
        status_labels['low']: '#e6f7e1',
        status_labels['medium']: '#fff3cd',
        status_labels['high']: '#ffe5d9',
        status_labels['full']: '#f8d7da',
        status_labels['overfilled']: '#f5c6cb',
        status_labels['storage']: '#e2e3e5'
    }
    
    # Create ordered categorical type for sorting
    status_counts['Status_Label'] = pd.Categorical(
        status_counts['Status_Label'],
        categories=[status_labels[s] for s in status_order if s in status_labels],
        ordered=True
    )
    status_counts = status_counts.sort_values('Status_Label')
    
    # Create chart
    fig = px.bar(
        status_counts,
        x='Status_Label',
        y='Count',
        color='Status_Label',
        color_discrete_map=color_map,
        text='Count',
        title='Room Capacity Utilization'
    )
    
    fig.update_layout(
        xaxis_title='Capacity Utilization',
        yaxis_title='Number of Rooms',
        height=400,
        showlegend=False
    )
    
    return fig


def style_dataframe(df, column_name):
    """Style a dataframe based on values in a specific column"""
    
    # Define styling functions based on column type
    if column_name == 'Status':
        def style_status(val):
            if val == 'Current':
                return 'background-color: #d4edda; color: #155724'
            elif val == 'Upcoming':
                return 'background-color: #cce5ff; color: #004085'
            elif val == 'Past':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        return df.style.applymap(style_status, subset=[column_name])
    
    elif column_name == 'Percentage' or column_name == 'Occupancy Rate':
        def style_percentage(val):
            if pd.isna(val):
                return ''
            val = float(val)
            if val == 0:
                return 'background-color: #d4edda'
            elif val <= 25:
                return 'background-color: #e6f7e1'
            elif val <= 50:
                return 'background-color: #fff3cd'
            elif val <= 75:
                return 'background-color: #ffe5d9'
            elif val <= 100:
                return 'background-color: #f8d7da'
            else:
                return 'background-color: #f5c6cb'
                
        return df.style.applymap(style_percentage, subset=[column_name])
    
    # No styling defined for this column
    return df


def save_action(occupant_manager, room_manager, file_path, use_github=False):
    """Execute save action with validation"""
    from data_manager import save_data
    
    # Get current dataframes
    current_df = occupant_manager.get_current_occupants()
    upcoming_df = occupant_manager.get_upcoming_occupants()
    past_df = occupant_manager.get_past_occupants()
    
    # Add data validation before saving
    validation_ok = True
    validation_messages = []
    
    # Check for required fields in current occupants
    if not current_df.empty:
        # Check for missing building or office values
        missing_location = current_df[
            (current_df['Building'].isna()) | 
            (current_df['Building'] == "") |
            (current_df['Office'].isna()) | 
            (current_df['Office'] == "")
        ]
        
        if not missing_location.empty and len(missing_location) > 0:
            validation_ok = False
            validation_messages.append(f"⚠️ {len(missing_location)} current occupants are missing Building or Office assignment.")
    
    # Execute save if validation passes or override is checked
    if validation_ok or st.session_state.get('ignore_warnings', False):
        success = save_data(
            current_df, 
            upcoming_df, 
            past_df,
            file_path,
            room_manager.room_capacities,
            use_github=use_github
        )
        
        if success:
            # Update last_save timestamp
            from datetime import datetime
            st.session_state.last_save = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # If GitHub was used, add that to the success message
            if use_github:
                return True, "Data saved successfully to local file and GitHub!"
            else:
                return True, "Data saved successfully to local file!"
        else:
            if use_github:
                return False, "Error saving data to local file or GitHub. Please check the console for details."
            else:
                return False, "Error saving data. Please check the console for details."
    else:
        return False, validation_messages