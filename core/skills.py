"""Direct skills that bypass LLM for faster responses."""

import re
import requests
from config import WEATHER_TIMEOUT_SECONDS, LOCATION_TIMEOUT_SECONDS


def is_weather_query(query: str) -> bool:
    """Determine if a query is about weather."""
    patterns = (
        r"\bwhat(?:'s| is) the weather\b",
        r"\bweather\b.*\b(?:in|for|at)\b",
        r"\bhow(?:'s| is) the weather\b",
        r"\bwill it rain\b",
        r"\btemperature\b.*\b(?:in|for|at)\b",
    )
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)


def extract_weather_location(query: str) -> str:
    """Extract location from weather query."""
    match = re.search(r"\b(?:in|for|at)\s+(.+)$", query, re.IGNORECASE)
    if not match:
        return ""
    location = match.group(1).strip(" ?!?.,")
    location = re.sub(r"\b(right now|today|now|please)\b$", "", location, flags=re.IGNORECASE).strip(" ,.")
    return location


def get_weather_response(query: str) -> str | None:
    """Get weather response directly from wttr.in API."""
    if not is_weather_query(query):
        return None
    
    location = extract_weather_location(query)
    if location:
        url = f"https://wttr.in/{location}?format=3"
    else:
        url = "https://wttr.in/?format=3"
    
    try:
        response = requests.get(url, timeout=WEATHER_TIMEOUT_SECONDS)
        response.raise_for_status()
        weather_text = response.text.strip()
        # Fix encoding issues
        weather_text = weather_text.replace("°C", " degrees Celsius")
        weather_text = weather_text.replace("°F", " degrees Fahrenheit")
        return f"Weather: {weather_text}"
    except requests.exceptions.Timeout:
        return "Weather service is slow right now. Try again in a moment."
    except Exception as e:
        return f"Couldn't fetch weather: {str(e)}"


def is_location_query(query: str) -> bool:
    """Determine if a query is about location."""
    patterns = (
        r"\bwhere am i\b",
        r"\bwhat(?:'s| is) my location\b",
        r"\bcurrent location\b",
        r"\bmy location\b",
        r"\bwhere are we\b",
    )
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)


def get_location_response(query: str) -> str | None:
    """Get location response directly from ipinfo.io API."""
    if not is_location_query(query):
        return None
    
    try:
        response = requests.get("https://ipinfo.io/json", timeout=LOCATION_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        city = data.get("city", "Unknown")
        region = data.get("region", "Unknown")
        country = data.get("country", "Unknown")
        loc = data.get("loc", "Unknown")
        timezone = data.get("timezone", "Unknown")
        
        # Expand country code
        country_names = {
            "US": "United States", "GB": "United Kingdom", "CA": "Canada",
            "AU": "Australia", "DE": "Germany", "FR": "France", "IT": "Italy",
            "ES": "Spain", "NL": "Netherlands", "BE": "Belgium", "CH": "Switzerland",
            "AT": "Austria", "SE": "Sweden", "NO": "Norway", "DK": "Denmark",
            "FI": "Finland", "PL": "Poland", "CZ": "Czech Republic", "HU": "Hungary",
            "RO": "Romania", "BG": "Bulgaria", "HR": "Croatia", "SI": "Slovenia",
            "SK": "Slovakia", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
            "IE": "Ireland", "PT": "Portugal", "GR": "Greece", "CY": "Cyprus",
            "MT": "Malta", "LU": "Luxembourg", "IS": "Iceland", "LI": "Liechtenstein",
            "MC": "Monaco", "AD": "Andorra", "SM": "San Marino", "VA": "Vatican City",
            "JP": "Japan", "CN": "China", "IN": "India", "BR": "Brazil",
            "RU": "Russia", "ZA": "South Africa", "MX": "Mexico", "AR": "Argentina",
            "CL": "Chile", "CO": "Colombia", "PE": "Peru", "VE": "Venezuela",
            "UY": "Uruguay", "PY": "Paraguay", "BO": "Bolivia", "EC": "Ecuador",
        }
        country = country_names.get(country, country)
        
        return f"Location: {city}, {region}, {country}. Coordinates: {loc}. Timezone: {timezone}"
    except requests.exceptions.Timeout:
        return "Location service is slow right now. Try again in a moment."
    except Exception as e:
        return f"Couldn't determine location: {str(e)}"


def is_music_query(query: str) -> bool:
    """Determine if a query is about playing music."""
    patterns = (
        r"\bplay\b.*\bmusic\b",
        r"\bplay\b.*\bsong\b",
        r"\bplay\b.*\byoutube\b",
        r"\bput on\b.*\bmusic\b",
    )
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)


def get_music_response(query: str) -> str | None:
    """Handle music commands."""
    if not is_music_query(query):
        return None
    
    # This would integrate with a music player or YouTube
    # For now, just acknowledge the command
    return "I can play music for you. What would you like to hear?"


def handle_direct_query(query: str, memory: dict) -> str | None:
    """Handle queries directly without LLM routing.
    
    Returns the response if handled, None if should route to LLM.
    """
    # Try weather first
    weather_response = get_weather_response(query)
    if weather_response is not None:
        return weather_response
    
    # Try location
    location_response = get_location_response(query)
    if location_response is not None:
        return location_response
    
    # Try music
    music_response = get_music_response(query)
    if music_response is not None:
        return music_response
    
    # Not a direct skill, route to LLM
    return None
