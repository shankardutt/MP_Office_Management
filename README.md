# Office Room Allocation System v3.0

This application helps manage office space allocation, track occupants, and generate reports on room utilization.

## Key Improvements over Previous Version

1. **Modular Code Architecture**: The application has been completely restructured into multiple files for better organization, maintainability, and extensibility.

2. **Room Overfilling Support**: Now allows assigning more occupants than the room capacity, making it easier to manage transitions and temporary arrangements.

3. **Fixed Room Editing**: Room editing and saving now works properly, with clear tracking of changes.

4. **Fixed Reports Section**: Fixed the datetime error and improved the reporting capabilities.

5. **Enhanced Data Management**: Better handling of data loading, saving, and validation.

## File Structure

```
/
├── app.py               # Main application file
├── auth.py              # Authentication functionality
├── config.py            # Configuration settings
├── data_manager.py      # Data loading and saving
├── models.py            # Data models and utility functions
├── utils.py             # Helper functions
├── requirements.txt     # Dependencies
├── data/                # Data storage directory
│   ├── MP_Office_Allocation.xlsx  # Main data file
│   ├── room_capacities.json       # Room capacity settings
│   └── backup/          # Automatic backups
└── pages/               # Page implementations
    ├── dashboard.py     # Dashboard page
    ├── current_occupants.py   # Current occupants page
    ├── upcoming_occupants.py  # Upcoming occupants page
    ├── room_management.py     # Room management functionality
    └── reports.py       # Reports page
```

## Setup and Installation

1. Ensure you have Python 3.8+ installed.

2. Clone the repository or copy all files to your local machine.

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

5. Login with the default password: `kluth2025` (can be changed in config.py)

## Key Features

### 1. Room Management

- **View Room Occupancy**: See all rooms with their current occupancy status.
- **Edit Rooms**: Add, edit, or delete rooms, and change room capacities.
- **Room Status**: View rooms by status (vacant, low, medium, high, full, or overfilled).
- **Room Assignment**: Assign occupants to rooms with an intuitive interface.

### 2. Occupant Management

- **Current Occupants**: Manage current room occupants.
- **Upcoming Occupants**: Plan for future arrivals.
- **Historical Data**: Keep records of past occupants.

### 3. Reports

- **Occupancy Summary**: Get a quick overview of capacity utilization.
- **Building Reports**: Detailed reports for specific buildings.
- **Room Utilization**: Identify rooms that need attention.
- **Occupant Reports**: Analyze occupant distribution by position and building.
- **Export Data**: Export data in CSV or Excel format.

## Room Capacity Management

This version supports:

1. **Setting Capacity**: Each room has a defined maximum capacity.
2. **Overfilling Rooms**: You can now assign more occupants than the room's capacity.
3. **Capacity Warnings**: The system provides visual indicators for room utilization status.
4. **Storage Rooms**: Designate rooms as storage with zero capacity.

## Saving and Backups

- **Automatic Backups**: Every time you save changes, a backup is created.
- **Manual Backups**: Create additional backups as needed.
- **Data Validation**: Checks for missing required fields before saving.

## Troubleshooting

- **Room Changes Not Saving**: Make sure to click "Save Room Changes" and then "Save Changes" in the sidebar.
- **Import/Export Issues**: Check file permissions and format compatibility.
- **Login Issues**: The default password is set in config.py.

## Customization

The system can be customized by editing the config.py file:
- Change default password
- Modify file paths
- Adjust session timeouts
- Customize UI colors and styling

## Known Limitations

- The application is designed for single-user use at a time.
- Very large datasets (1000+ occupants) may cause performance issues.
- The search functionality is basic and does not support complex queries.

## Future Improvements

Potential future enhancements could include:
- Multi-user support with different permission levels
- Calendar integration for room booking
- Email notifications for occupants
- Advanced search and filtering
- Mobile-friendly interface