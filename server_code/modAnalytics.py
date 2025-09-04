import anvil.secrets
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
#from datetime import datetime, timedelta
import anvil.tz
import anvil.secrets
import requests # Import the requests library
import re # For User-Agent parsing
from anvil import Media
import datetime



@anvil.server.callable
def get_stats(user_agent_string=None): # Accept user_agent_string from client
    # --- 1. Get Client IP Address (provided by Anvil) ---
    client_ip = None
    if anvil.server.context.client and anvil.server.context.client.ip:
        client_ip = anvil.server.context.client.ip

    # --- 2. Get Browser-Provided Location (requires user permission) ---
    browser_location = None
    if anvil.server.context.client and anvil.server.context.client.location:
        browser_location = str(anvil.server.context.client.location)

    # --- 3. IP-based Geolocation (using a third-party API) ---
    ip_geo_country = "Unknown"
    ip_geo_city = "Unknown"
    ip_geo_region = "Unknown"
    ip_geo_coords = "N/A" # Latitude,Longitude from IP

    if client_ip:
        try:
            # Using ip-api.com (free for non-commercial use, no key)
            # You can switch to ipapi.co or another service if you prefer.
            response = requests.get(f"http://ip-api.com/json/{client_ip}")
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            geo_data = response.json()

            if geo_data.get("status") == "success":
                ip_geo_country = geo_data.get("country", "Unknown")
                ip_geo_city = geo_data.get("city", "Unknown")
                ip_geo_region = geo_data.get("regionName", "Unknown")
                lat = geo_data.get("lat")
                lon = geo_data.get("lon")
                if lat is not None and lon is not None:
                    ip_geo_coords = f"{lat},{lon}"
            else:
                print(f"IP Geolocation API error for {client_ip}: {geo_data.get('message', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching IP geolocation for {client_ip}: {e}")
        except ValueError as e: # For JSON decoding errors
            print(f"Error decoding IP geolocation response for {client_ip}: {e}")

    # --- 4. User-Agent Parsing for OS and Browser (from previous discussion) ---
    operating_system = "Unknown OS"
    windows_version = "N/A" # To store the specific Windows version
    browser_name = "Unknown Browser"

    if user_agent_string:
        # Basic OS detection
        if "Windows NT 10.0" in user_agent_string:
            operating_system = "Windows"
            windows_version = "Windows 10/11 (NT 10.0)"
        elif "Windows NT 6.3" in user_agent_string:
            operating_system = "Windows"
            windows_version = "Windows 8.1"
        elif "Windows NT 6.2" in user_agent_string:
            operating_system = "Windows"
            windows_version = "Windows 8"
        elif "Windows NT 6.1" in user_agent_string:
            operating_system = "Windows"
            windows_version = "Windows 7"
        elif "Macintosh" in user_agent_string or "Mac OS X" in user_agent_string:
            operating_system = "macOS"
        elif "Linux" in user_agent_string:
            operating_system = "Linux"
        elif "Android" in user_agent_string:
            operating_system = "Android"
        elif "iOS" in user_agent_string:
            operating_system = "iOS"

        # Basic browser detection
        if "Chrome" in user_agent_string and "Edge" not in user_agent_string:
            browser_name = "Chrome"
        elif "Firefox" in user_agent_string:
            browser_name = "Firefox"
        elif "Safari" in user_agent_string and "Chrome" not in user_agent_string:
            browser_name = "Safari"
        elif "Edge" in user_agent_string:
            browser_name = "Edge"
        elif "Trident" in user_agent_string or "MSIE" in user_agent_string:
            browser_name = "Internet Explorer"

    # --- 5. Log to Data Table ---
    app_tables.tbl_stats.add_row(
        AccessedVia=anvil.server.context.client.type,
        BrowserProvidedLocation=browser_location, # Rename for clarity
        IPAddress=client_ip,
        IPGeoCountry=ip_geo_country,       # New: IP-based country
        IPGeoCity=ip_geo_city,             # New: IP-based city
        IPGeoRegion=ip_geo_region,         # New: IP-based region/state
        IPGeoCoordinates=ip_geo_coords,    # New: IP-based lat/lon
        OperatingSystem=operating_system,
        WindowsVersion=windows_version,
        Browser=browser_name,
        UserAgentString=user_agent_string,
        LoggedDate=(datetime.datetime.now(anvil.tz.tzlocal()) + datetime.timedelta(hours = 3)).strftime("%d-%m-%Y %H:%M:%S") + ' EAT',
        User=anvil.users.get_user()['email']
    )

@anvil.server.callable()
def fe_keepalive():
    if 1 > 0:
        return "ok"
    else:
        return "stop"
        
@anvil.server.callable
def display_result(code):
    # Handle the scanned barcode (e.g., store it, display it, etc.)
    print(f"Scanned barcode: {code}")
    return code

@anvil.server.callable
def show_error(message):
    # Display error messages to the user
    print(f"Error: {message}")
    anvil.js.window.alert(f"Error: {message}")

@anvil.server.callable
def log_copy(text):
    # Log when the user copies the barcode
    print(f"Copied text: {text}")
    return True