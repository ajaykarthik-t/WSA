import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
import time
from datetime import datetime

# Set page title and configuration
st.set_page_config(
    page_title="Simple GPS Location Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("📍 Simple GPS Location Tracker")
st.markdown("A basic application to track your GPS location")

# Initialize session state to store location history
if 'locations' not in st.session_state:
    st.session_state.locations = []

# Function to get current location
def get_location():
    # In a real app, you would use device GPS
    # For this demo, we'll use browser geolocation JavaScript
    loc_js = """
    <script>
    navigator.geolocation.getCurrentPosition(
        (position) => {
            document.getElementById('lat').value = position.coords.latitude;
            document.getElementById('lon').value = position.coords.longitude;
            document.getElementById('acc').value = position.coords.accuracy;
            document.getElementById('submit_loc').click();
        },
        (error) => {
            document.getElementById('error').value = error.message;
            document.getElementById('submit_loc').click();
        }
    );
    </script>
    <input type="hidden" id="lat">
    <input type="hidden" id="lon">
    <input type="hidden" id="acc">
    <input type="hidden" id="error">
    <button id="submit_loc" style="display:none;">Submit</button>
    """
    st.components.v1.html(loc_js, height=0)
    
    # Get the values from the components
    lat = st.session_state.get('lat', None)
    lon = st.session_state.get('lon', None)
    acc = st.session_state.get('acc', None)
    error = st.session_state.get('error', None)
    
    if error:
        st.error(f"Error getting location: {error}")
        return None
    
    if lat and lon:
        # Get address from coordinates
        geolocator = Nominatim(user_agent="streamlit_gps_tracker")
        try:
            location = geolocator.reverse(f"{lat}, {lon}")
            address = location.address
        except:
            address = "Unknown location"
        
        return {
            'latitude': lat,
            'longitude': lon,
            'accuracy': acc,
            'address': address,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    return None

# Sidebar for controls
with st.sidebar:
    st.header("Tracking Controls")
    
    # Manual location input option
    st.subheader("Manual Location Input")
    manual_lat = st.number_input("Latitude", value=0.0, format="%.6f")
    manual_lon = st.number_input("Longitude", value=0.0, format="%.6f")
    
    if st.button("Add Manual Location"):
        geolocator = Nominatim(user_agent="streamlit_gps_tracker")
        try:
            location = geolocator.reverse(f"{manual_lat}, {manual_lon}")
            address = location.address
        except:
            address = "Unknown location"
            
        loc_data = {
            'latitude': manual_lat,
            'longitude': manual_lon,
            'accuracy': 0,
            'address': address,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.locations.append(loc_data)
        st.success("Manual location added!")
    
    # Auto-tracking toggles
    st.subheader("Automatic Tracking")
    auto_track = st.checkbox("Enable Auto Tracking")
    update_interval = st.slider("Update Interval (seconds)", 5, 60, 10)
    
    # Clear history button
    if st.button("Clear Location History"):
        st.session_state.locations = []
        st.success("Location history cleared!")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Location Map")
    
    # Get current location on button click or auto-track
    if st.button("Get Current Location") or (auto_track and time.time() % update_interval < 1):
        location = get_location()
        if location:
            st.session_state.locations.append(location)
            st.success(f"Location updated: {location['address']}")
    
    # Create and display the map
    if st.session_state.locations:
        # Get the most recent location
        last_loc = st.session_state.locations[-1]
        
        # Create map centered at the most recent location
        m = folium.Map(location=[last_loc['latitude'], last_loc['longitude']], zoom_start=15)
        
        # Add markers for all locations in history
        for i, loc in enumerate(st.session_state.locations):
            popup_text = f"""
            Time: {loc['timestamp']}<br>
            Coordinates: {loc['latitude']}, {loc['longitude']}<br>
            Address: {loc['address']}
            """
            
            # Use different color for the latest location
            if i == len(st.session_state.locations) - 1:
                folium.Marker(
                    [loc['latitude'], loc['longitude']], 
                    popup=popup_text,
                    icon=folium.Icon(color='red', icon='location-arrow')
                ).add_to(m)
            else:
                folium.Marker(
                    [loc['latitude'], loc['longitude']], 
                    popup=popup_text,
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        
        # Add lines connecting the locations in chronological order
        if len(st.session_state.locations) > 1:
            points = [[loc['latitude'], loc['longitude']] for loc in st.session_state.locations]
            folium.PolyLine(points, color='green', weight=2.5, opacity=1).add_to(m)
        
        # Display the map
        folium_static(m, width=700, height=500)
    else:
        st.info("No location data available. Click 'Get Current Location' to start tracking.")

with col2:
    st.subheader("Location History")
    
    if st.session_state.locations:
        # Convert to DataFrame for display
        df = pd.DataFrame(st.session_state.locations)
        
        # Display latest location details
        st.write("Latest Location:")
        latest = st.session_state.locations[-1]
        st.write(f"📅 **Time:** {latest['timestamp']}")
        st.write(f"🌐 **Coordinates:** {latest['latitude']}, {latest['longitude']}")
        st.write(f"📍 **Address:** {latest['address']}")
        if latest['accuracy']:
            st.write(f"🎯 **Accuracy:** ±{latest['accuracy']} meters")
        
        # Display history table
        st.write("All Locations:")
        df_display = df[['timestamp', 'latitude', 'longitude']].copy()
        df_display.columns = ['Time', 'Latitude', 'Longitude']
        st.dataframe(df_display)
        
        # Export option
        if st.button("Export Data (CSV)"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download CSV File",
                csv,
                "location_history.csv",
                "text/csv",
                key='download-csv'
            )
    else:
        st.info("No location history available.")

# Footer
st.markdown("---")
st.markdown("""
**Note:** This application uses browser geolocation which requires:
1. Permission from your browser
2. A secure connection (HTTPS) in production environments
3. Location services enabled on your device
""")
