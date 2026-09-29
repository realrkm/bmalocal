import ipaddress
import re
import datetime
import requests
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.tz
from anvil import Media


def _is_private_ip(ip_str):
    """Check if an IP is private, loopback, link-local, or invalid to avoid unnecessary external HTTP calls."""
    if not ip_str:
        return True
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return True


@anvil.server.callable
def get_stats(user_agent_string=None):  # Accept user_agent_string from client
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
    ip_geo_coords = "N/A"  # Latitude,Longitude from IP

    if client_ip:
        if _is_private_ip(client_ip):
            ip_geo_country = "Local Network"
            ip_geo_city = "LAN"
            ip_geo_region = "Private Subnet"
        else:
            try:
                # Using ip-api.com (free for non-commercial use, no key) with a strict 2s timeout
                response = requests.get(f"http://ip-api.com/json/{client_ip}", timeout=2.0)
                response.raise_for_status()
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

            except requests.exceptions.Timeout:
                print(f"IP Geolocation timed out for {client_ip}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching IP geolocation for {client_ip}: {e}")
            except ValueError as e:  # For JSON decoding errors
                print(f"Error decoding IP geolocation response for {client_ip}: {e}")

    # --- 4. User-Agent Parsing for OS and Browser ---
    operating_system = "Unknown OS"
    windows_version = "N/A"  # To store the specific Windows version
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

    # --- 5. Safely Resolve User Email ---
    current_user = anvil.users.get_user()
    user_email = current_user["email"] if current_user and "email" in current_user else "Unknown"

    # --- 6. Log to Data Table ---
    app_tables.tbl_stats.add_row(
        AccessedVia=anvil.server.context.client.type,
        BrowserProvidedLocation=browser_location,
        IPAddress=client_ip,
        IPGeoCountry=ip_geo_country,
        IPGeoCity=ip_geo_city,
        IPGeoRegion=ip_geo_region,
        IPGeoCoordinates=ip_geo_coords,
        OperatingSystem=operating_system,
        WindowsVersion=windows_version,
        Browser=browser_name,
        UserAgentString=user_agent_string,
        LoggedDate=(datetime.datetime.now(anvil.tz.tzlocal()) + datetime.timedelta(hours=3)).strftime("%d-%m-%Y %H:%M:%S") + " EAT",
        User=user_email,
    )


@anvil.server.callable()
def fe_keepalive():
    """Zero-query lightweight ping for keeping client session alive."""
    return "ok"

