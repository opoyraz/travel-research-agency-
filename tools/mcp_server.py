import os
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastmcp import FastMCP
from serpapi import GoogleSearch
import requests

load_dotenv()

mcp = FastMCP(
    name="TravelToolServer",
    host="127.0.0.1",
    port=8001,
)

# ═══════════════════════════════════════════════
#  API KEYS
# ═══════════════════════════════════════════════

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")


def _default_date(days_ahead: int = 30) -> str:
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════
#  FLIGHTS (SerpAPI → Google Flights)
# ═══════════════════════════════════════════════

@mcp.tool
def search_flights(
    departure_city: str,
    arrival_city: str,
    date: str = "",
    max_results: int = 5,
) -> dict:
    """Search for available flights between two cities via Google Flights.

    Args:
        departure_city: City or airport code (e.g., "Austin" or "AUS")
        arrival_city: City or airport code (e.g., "Tokyo" or "NRT")
        date: Travel date YYYY-MM-DD (defaults to 30 days from now)
        max_results: Max results (1-10)
    """
    travel_date = date if date else _default_date(30)

    try:
        search = GoogleSearch({
            "engine": "google_flights",
            "departure_id": departure_city,
            "arrival_id": arrival_city,
            "outbound_date": travel_date,
            "type": "2",  # one-way
            "api_key": SERPAPI_KEY,
        })
        results = search.get_dict()

        all_flights = results.get("best_flights", []) + results.get("other_flights", [])

        flights = []
        for group in all_flights[:max_results]:
            legs = group.get("flights", [])
            if not legs:
                continue

            first = legs[0]
            last = legs[-1]
            dep_airport = first.get("departure_airport", {})
            arr_airport = last.get("arrival_airport", {})

            flights.append({
                "airline": first.get("airline", "Unknown"),
                "flight_number": first.get("flight_number", ""),
                "route": f"{dep_airport.get('id', departure_city)} → {arr_airport.get('id', arrival_city)}",
                "stops": len(legs) - 1,
                "departure": dep_airport.get("time", ""),
                "arrival": arr_airport.get("time", ""),
                "duration": f"{group.get('total_duration', 0)} min",
                "price": group.get("price", None),
                "currency": "USD",
                "airline_logo": first.get("airline_logo", ""),
            })

        return {
            "status": "success",
            "source": "serpapi_google_flights",
            "query": {"from": departure_city, "to": arrival_city, "date": travel_date},
            "results": flights,
            "count": len(flights),
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google_flights", "error": str(e), "results": []}


# ═══════════════════════════════════════════════
#  HOTELS (SerpAPI → Google Hotels)
# ═══════════════════════════════════════════════

@mcp.tool
def search_hotels(
    city: str,
    checkin: str = "",
    checkout: str = "",
    max_results: int = 5,
) -> dict:
    """Search for hotels in a city via Google Hotels.

    Args:
        city: Destination city (e.g., "Tokyo")
        checkin: Check-in date YYYY-MM-DD (defaults to 30 days out)
        checkout: Check-out date YYYY-MM-DD (defaults to checkin + 7)
        max_results: Max results
    """
    check_in = checkin if checkin else _default_date(30)
    check_out = checkout if checkout else _default_date(37)

    try:
        search = GoogleSearch({
            "engine": "google_hotels",
            "q": f"hotels in {city}",
            "check_in_date": check_in,
            "check_out_date": check_out,
            "adults": 1,
            "api_key": SERPAPI_KEY,
        })
        results = search.get_dict()
        properties = results.get("properties", [])

        hotels = []
        for prop in properties[:max_results]:
            rate_info = prop.get("rate_per_night", {})
            total_info = prop.get("total_rate", {})

            hotels.append({
                "name": prop.get("name", "Unknown"),
                "price_per_night": rate_info.get("lowest", None),
                "price_total": total_info.get("lowest", None),
                "currency": "USD",
                "checkin": check_in,
                "checkout": check_out,
                "rating": prop.get("overall_rating", None),
                "stars": prop.get("hotel_class", None),
                "description": prop.get("description", ""),
                "amenities": prop.get("amenities", [])[:5],
                "thumbnail": prop.get("images", [{}])[0].get("thumbnail", "") if prop.get("images") else "",
                "link": prop.get("link", ""),
            })

        return {
            "status": "success",
            "source": "serpapi_google_hotels",
            "query": {"city": city, "checkin": check_in, "checkout": check_out},
            "results": hotels,
            "count": len(hotels),
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google_hotels", "error": str(e), "results": []}


# ═══════════════════════════════════════════════
#  ACTIVITIES / TOURS (SerpAPI → Google Local)
# ═══════════════════════════════════════════════

@mcp.tool
def search_activities(
    city: str,
    category: str = "any",
    max_results: int = 5,
) -> dict:
    """Search for tours and activities in a city via Google.

    Args:
        city: Destination city (e.g., "Tokyo")
        category: Activity type (e.g., "cultural", "outdoor", "food", "any")
        max_results: Max results
    """
    query = f"best {category} tours and activities in {city}" if category != "any" else f"best tours and activities in {city}"

    try:
        search = GoogleSearch({
            "engine": "google_local",
            "q": query,
            "api_key": SERPAPI_KEY,
        })
        results = search.get_dict()
        local_results = results.get("local_results", [])

        activities = []
        for r in local_results[:max_results]:
            activities.append({
                "name": r.get("title", "Unknown"),
                "rating": r.get("rating", None),
                "reviews": r.get("reviews", None),
                "type": r.get("type", ""),
                "address": r.get("address", ""),
                "hours": r.get("hours", ""),
                "description": r.get("description", "")[:200],
                "thumbnail": r.get("thumbnail", ""),
            })

        return {
            "status": "success",
            "source": "serpapi_google_local",
            "query": {"city": city, "category": category},
            "results": activities,
            "count": len(activities),
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google_local", "error": str(e), "results": []}


# ═══════════════════════════════════════════════
#  RESTAURANTS (SerpAPI → Google Local)
# ═══════════════════════════════════════════════

@mcp.tool
def search_restaurants(
    city: str,
    cuisine: str = "any",
    max_results: int = 5,
) -> dict:
    """Search for restaurants in a city via Google Local results.

    Args:
        city: Destination city
        cuisine: Cuisine type (e.g., "japanese", "french", "any")
        max_results: Max results
    """
    query = f"best {cuisine} restaurants in {city}" if cuisine != "any" else f"best restaurants in {city}"

    try:
        search = GoogleSearch({
            "engine": "google_local",
            "q": query,
            "api_key": SERPAPI_KEY,
        })
        results = search.get_dict()
        local_results = results.get("local_results", [])

        restaurants = []
        for r in local_results[:max_results]:
            restaurants.append({
                "name": r.get("title", "Unknown"),
                "rating": r.get("rating", None),
                "reviews": r.get("reviews", None),
                "price": r.get("price", ""),
                "type": r.get("type", ""),
                "address": r.get("address", ""),
                "hours": r.get("hours", ""),
                "thumbnail": r.get("thumbnail", ""),
            })

        return {
            "status": "success",
            "source": "serpapi_google_local",
            "query": {"city": city, "cuisine": cuisine},
            "results": restaurants,
            "count": len(restaurants),
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google_local", "error": str(e), "results": []}


# ═══════════════════════════════════════════════
#  VISA REQUIREMENTS (SerpAPI → Google Search)
# ═══════════════════════════════════════════════

@mcp.tool
def check_visa_requirements(
    destination_country: str,
    passport_country: str = "US",
) -> dict:
    """Check visa requirements for a destination country via Google.

    Args:
        destination_country: Country to visit (e.g., "Japan")
        passport_country: Traveler's passport country (default: "US")
    """
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": f"{destination_country} visa requirements for {passport_country} citizens 2026",
            "api_key": SERPAPI_KEY,
            "num": 3,
        })
        results = search.get_dict()

        answer = results.get("answer_box", {}).get("answer", "")
        snippet = results.get("answer_box", {}).get("snippet", "")
        organic = results.get("organic_results", [])
        top_snippet = organic[0].get("snippet", "") if organic else ""

        visa_info = answer or snippet or top_snippet or "No information found."

        return {
            "status": "success",
            "source": "serpapi_google",
            "destination": destination_country,
            "passport": passport_country,
            "info": visa_info,
            "sources": [r.get("link", "") for r in organic[:2]],
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google", "error": str(e)}


# ═══════════════════════════════════════════════
#  TRAVEL ADVISORY (SerpAPI → Google Search)
# ═══════════════════════════════════════════════

@mcp.tool
def get_travel_advisory(country: str) -> dict:
    """Get the current travel advisory level for a country via Google.

    Args:
        country: Country name (e.g., "Japan")
    """
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": f"{country} travel advisory US State Department 2026",
            "api_key": SERPAPI_KEY,
            "num": 3,
        })
        results = search.get_dict()

        answer = results.get("answer_box", {}).get("answer", "")
        snippet = results.get("answer_box", {}).get("snippet", "")
        organic = results.get("organic_results", [])
        top_snippet = organic[0].get("snippet", "") if organic else ""

        advisory_info = answer or snippet or top_snippet or "No advisory found."

        level_match = re.search(r"Level\s*(\d)", advisory_info)
        level = int(level_match.group(1)) if level_match else None

        return {
            "status": "success",
            "source": "serpapi_google",
            "country": country,
            "level": level,
            "info": advisory_info,
            "sources": [r.get("link", "") for r in organic[:2]],
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google", "error": str(e)}


# ═══════════════════════════════════════════════
#  CURRENCY CONVERSION (SerpAPI → Google Answer Box)
# ═══════════════════════════════════════════════

@mcp.tool
def convert_currency(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "JPY",
) -> dict:
    """Convert between currencies using live Google rates.

    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., "USD")
        to_currency: Target currency code (e.g., "JPY")
    """
    try:
        search = GoogleSearch({
            "engine": "google",
            "q": f"{amount} {from_currency} to {to_currency}",
            "api_key": SERPAPI_KEY,
        })
        results = search.get_dict()

        answer = results.get("answer_box", {})
        converted_text = answer.get("answer", "") or answer.get("result", "")

        numbers = re.findall(r"[\d,]+\.?\d*", converted_text.replace(",", ""))
        converted_amount = float(numbers[0]) if numbers else None

        rate = round(converted_amount / amount, 4) if converted_amount and amount else None

        return {
            "status": "success",
            "source": "serpapi_google",
            "from": {"amount": amount, "currency": from_currency},
            "to": {"amount": converted_amount, "currency": to_currency},
            "rate": rate,
            "raw_answer": converted_text,
        }

    except Exception as e:
        return {"status": "error", "source": "serpapi_google", "error": str(e)}


# ═══════════════════════════════════════════════
#  WEATHER (OpenWeatherMap API)
# ═══════════════════════════════════════════════

@mcp.tool
def get_weather(city: str) -> dict:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Tokyo", "Paris")
    """
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_KEY,
                "units": "metric",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "success",
            "source": "openweathermap",
            "city": city,
            "temp_c": round(data["main"]["temp"], 1),
            "feels_like_c": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"].title(),
            "wind_speed_ms": data["wind"]["speed"],
            "country": data["sys"]["country"],
        }

    except Exception as e:
        return {"status": "error", "source": "openweathermap", "error": str(e)}


# ═══════════════════════════════════════════════
#  MCP RESOURCES
# ═══════════════════════════════════════════════

@mcp.resource("config://travel/api-status")
def get_api_status() -> str:
    """Show which API powers each tool."""
    return json.dumps({
        "serpapi_google_flights": ["search_flights"],
        "serpapi_google_hotels": ["search_hotels"],
        "serpapi_google_local": ["search_activities", "search_restaurants"],
        "serpapi_google_search": ["check_visa_requirements", "get_travel_advisory", "convert_currency"],
        "openweathermap": ["get_weather"],
    }, indent=2)


# ═══════════════════════════════════════════════
#  RUN SERVER
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Travel MCP Server — http://127.0.0.1:8001/mcp")
    print("=" * 60)
    print("\n  SerpAPI → Google Flights:")
    print("    ✈️  search_flights")
    print("\n  SerpAPI → Google Hotels:")
    print("    🏨  search_hotels")
    print("\n  SerpAPI → Google Local:")
    print("    🎯  search_activities")
    print("    🍽️  search_restaurants")
    print("\n  SerpAPI → Google Search:")
    print("    📋  check_visa_requirements")
    print("    ⚠️  get_travel_advisory")
    print("    💱  convert_currency")
    print("\n  OpenWeatherMap:")
    print("    🌤️  get_weather")
    print("=" * 60)
    mcp.run(transport="http")
