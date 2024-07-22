
import os

import pycountry
import requests
from collections import namedtuple

LOCATION_TOKEN = os.getenv("LOCATION_TOKEN")


def degrees_to_microdegrees(degrees: float):
    """Convert degrees to microdegrees.
    :param: degrees (float): Degrees to convert
    :returns: int: Converted value
    """
    return int(degrees * 10**6)


def microdegrees_to_degrees(microdegrees: int):
    """Convert microdegrees to degrees.
    :param: microdegrees (int): Microdegrees to convert
    :returns: float: Converted value
    """
    return microdegrees / 10**6


def convert_coordinates(value: int | float | str):
    """Convert coordinates to/from microdegrees.
    :param: value (float,int, or str):
        Int(microdegrees) value is converted to float degrees.
        Float value is converted to microdegrees.
        String value is converted to a numerical value and is then converted to microdegrees or degrees.
    :returns: float or int: Converted value
    """
    if isinstance(value, str):
        if value.isdigit():
            return microdegrees_to_degrees(int(value))
        elif value.replace(".", "", 1).replace('-', '', 1).isdigit():
            return degrees_to_microdegrees(float(value))
    elif isinstance(value, float):
        return degrees_to_microdegrees(value)
    elif isinstance(value, int):
        return microdegrees_to_degrees(value)
    else:
        return None


STATE_ABBREVIATIONS = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"
}


def parse_input_param(input_param):
    """Parse input parameter into a dictionary of location parts.

    :param: input_param (str):
        Input parameter should be in the format "city, state, country", "city, country" or "city"

    :returns: dict: Dictionary of location parts
    """

    location_parts = input_param.split(", ")
    city = location_parts[0]
    state_code = None
    country_name = None
    if len(location_parts) > 1:
        state_or_country = location_parts[1]
        state_code = STATE_ABBREVIATIONS.get(state_or_country)
        if state_code is None:
            try:
                # Try to convert state/country to state/country code using pycountry
                country = pycountry.countries.search_fuzzy(state_or_country)[0]
                country_name = country.name
                country_code = country.alpha_2
                subdivisions = pycountry.subdivisions.get(country_code=country_code)
                for subdivision in subdivisions:
                    if subdivision.name == state_or_country or subdivision.code == state_or_country or subdivision.code.lower() == state_or_country.lower():
                        state_code = subdivision.code.split("-")[-1]
                        break
            except LookupError:
                # State/country is not a subdivision of a country
                pass
    if state_code is not None:
        return {"city": city, "state": state_code}
    elif country_name is not None:
        return {"city": city, "country": country_name}
    return {"city": city}


def query_location(location_param, lat=None, lon=None):
    """Query location data from location API.

    :param: location_param (str): Location string to get data for
    :param: lat (float): Latitude
    :param: lon (float): Longitude

    :returns: requests.Response: Response object from location API
    """
    headers = {
        "Authorization": f"Bearer {LOCATION_TOKEN}"
    }
    if lat and lon:
        url = f"http://location.app/reverse?lat={lat}&lon={lon}"
    elif location_param:
        url = f"http://location.app/search?q={location_param}"
    else:
        return None
    return requests.get(url, headers=headers, timeout=5)


async def get_location_coord(location: str):
    if location is None:
        return None, None
    location_data = await get_location_data(location)
    if location_data:
        lat = convert_coordinates(getattr(location_data, "lat", None))
        lon = convert_coordinates(getattr(location_data, "lon", None))
        return lat, lon
    return None, None



def get_location_data(location: str = None, lat=None, lon=None):
    """Get location data from Nominatim location API.

    :param: location (str): Location string to get data for
    :param: lat (float): Latitude
    :param: lon (float): Longitude

    :returns: namedtuple: Location data
    """
    location_response = None
    if lat and lon:
        location_response = query_location(f"{lat},{lon}")
    elif location:
        location_response = query_location(location)

    if location_response:
        location_data = location_response.json()["response"]["data"][0]
        Location = namedtuple("Location", location_data.keys())
        return Location(**location_data)
    return None
