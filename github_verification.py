"""
GitHub verification and setup functions
"""

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