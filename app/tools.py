import os
import json
import time
import base64
import urllib.request
import urllib.parse
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from google.cloud import firestore, storage

# Hardcode project ID as requested to prevent Agent Platform project-number resolution issues
PROJECT_ID = "qwiklabs-gcp-02-877388a9a06c"

# Lazy initialization of Firestore Client
_db = None

def get_firestore_client() -> firestore.Client:
    global _db
    if _db is None:
        key_file = "/config/Desktop/Session1/sa-key.json"
        if os.path.exists(key_file) and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def search_destinations(city: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for destinations, hotels, or activities in the Firestore database.

    Args:
        city: Optional city name to filter by (e.g. 'San Francisco', 'New York', 'Kyoto').
        category: Optional category filter (e.g. 'Attraction', 'Hotel', 'Activity').

    Returns:
        A list of matching destination items with details like name, city, category, price, and description.
    """
    db = get_firestore_client()
    collection_ref = db.collection("destinations")
    docs = collection_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        
        # Apply optional filters case-insensitively
        if city and city.lower() not in data.get("city", "").lower():
            continue
        if category and category.lower() not in data.get("category", "").lower():
            continue

        results.append(data)

    return results


def add_destination(
    name: str,
    city: str,
    category: str,
    description: str,
    price_per_day: float,
    rating: float = 4.5,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Add a new destination, hotel, or activity to the Firestore database.

    Args:
        name: Name of the destination or attraction.
        city: City where the destination is located.
        category: Category of the item (e.g. 'Attraction', 'Hotel', 'Activity', 'Dining').
        description: Detailed summary of what the destination offers.
        price_per_day: Estimated cost per day in USD.
        rating: Rating out of 5.0 (default 4.5).
        tags: List of keywords/tags describing the destination.

    Returns:
        A dictionary confirming the newly created destination document.
    """
    db = get_firestore_client()
    doc_id = f"{city.lower().replace(' ', '-')}-{name.lower().replace(' ', '-')}"
    doc_ref = db.collection("destinations").document(doc_id)

    item_data = {
        "id": doc_id,
        "name": name,
        "city": city,
        "category": category,
        "description": description,
        "price_per_day": float(price_per_day),
        "rating": float(rating),
        "tags": tags or []
    }

    doc_ref.set(item_data)
    return {"status": "success", "message": f"Added destination '{name}' to Firestore", "destination": item_data}


def calculate_trip_budget(
    num_days: int,
    num_travelers: int,
    lodging_cost_per_night: float,
    daily_food_budget: float = 50.0,
    activity_costs: Optional[List[float]] = None,
    tax_rate: float = 0.10,
) -> Dict[str, Any]:
    """Calculate the estimated total budget breakdown for a trip.

    Args:
        num_days: Duration of the trip in days.
        num_travelers: Total number of travelers.
        lodging_cost_per_night: Nightly cost for lodging/hotel in USD.
        daily_food_budget: Estimated daily food budget per person in USD (default $50/day).
        activity_costs: Optional list of individual activity or ticket costs in USD.
        tax_rate: Estimated tax/service fee rate (default 0.10 for 10%).

    Returns:
        A dictionary with subtotal, taxes, grand total budget, and cost per traveler.
    """
    total_lodging = lodging_cost_per_night * max(1, num_days - 1)
    total_food = daily_food_budget * num_days * num_travelers
    total_activities = sum(activity_costs or []) * num_travelers

    subtotal = total_lodging + total_food + total_activities
    tax_and_fees = round(subtotal * tax_rate, 2)
    grand_total = round(subtotal + tax_and_fees, 2)
    per_person = round(grand_total / max(1, num_travelers), 2)

    return {
        "num_days": num_days,
        "num_travelers": num_travelers,
        "breakdown": {
            "lodging_total": round(total_lodging, 2),
            "food_total": round(total_food, 2),
            "activities_total": round(total_activities, 2),
            "subtotal": round(subtotal, 2),
            "taxes_and_fees": tax_and_fees,
        },
        "grand_total_usd": grand_total,
        "cost_per_person_usd": per_person,
    }


def get_exchange_rate(base_currency: str = "USD", target_currency: str = "EUR") -> Dict[str, Any]:
    """Get real-time exchange rates between currencies for international travel.

    Args:
        base_currency: 3-letter currency code to convert from (e.g. 'USD', 'EUR', 'GBP').
        target_currency: 3-letter currency code to convert to (e.g. 'JPY', 'EUR', 'CAD', 'MXN').

    Returns:
        A dictionary containing the real exchange rate, sample conversion string, and update timestamp.
    """
    base = base_currency.upper().strip()
    target = target_currency.upper().strip()

    # Supports optional API key from environment variable if configured, or defaults to free public tier
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    if api_key:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
    else:
        url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TravelConciergeAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("result") == "success":
            rates = data.get("rates", {})
            if target in rates:
                rate = rates[target]
                return {
                    "status": "success",
                    "base_currency": base,
                    "target_currency": target,
                    "exchange_rate": rate,
                    "sample_conversion": f"1 {base} = {rate} {target}",
                    "last_updated": data.get("time_last_update_utc", "")
                }
            return {"status": "error", "message": f"Target currency '{target}' not found."}
        return {"status": "error", "message": "Failed to fetch exchange rates from public API."}
    except Exception as e:
        return {"status": "error", "message": f"Exchange rate API request failed: {str(e)}"}


def get_google_maps_api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GOOGLE_MAPS_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        os.environ["GOOGLE_MAPS_API_KEY"] = key
                        break
    return key or ""


def geocode_address(address: str) -> Dict[str, Any]:
    """Convert a human-readable address into geographic coordinates using Google Maps Geocoding API.

    Args:
        address: The street address, city, landmark, or location string (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A dictionary with key fields: name (formatted address), address, and location (latitude/longitude).
    """
    api_key = get_google_maps_api_key()
    if not api_key:
        return {"status": "error", "message": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_addr = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_addr}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") == "OK" and data.get("results"):
            first = data["results"][0]
            loc = first.get("geometry", {}).get("location", {})
            return {
                "status": "success",
                "name": first.get("formatted_address", address),
                "address": first.get("formatted_address", address),
                "location": {
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lng")
                },
                "place_id": first.get("place_id")
            }
        return {"status": "error", "message": f"Geocoding failed: {data.get('status')}"}
    except Exception as e:
        return {"status": "error", "message": f"Geocoding API error: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1000.0
) -> Dict[str, Any]:
    """Find nearby places of a given type around coordinates using Google Maps Places API (New).

    Args:
        latitude: Latitude coordinate of center point.
        longitude: Longitude coordinate of center point.
        place_type: Type of place to search for (e.g. 'restaurant', 'hotel', 'tourist_attraction', 'cafe').
        radius_meters: Search radius in meters (default 1000m).

    Returns:
        A dictionary containing a list of nearby places with key fields: name, address, and location.
    """
    api_key = get_google_maps_api_key()
    if not api_key:
        return {"status": "error", "message": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
    }

    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": float(radius_meters)
            }
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = []
        for place in data.get("places", []):
            display_name = place.get("displayName", {}).get("text", "")
            address = place.get("formattedAddress", "")
            loc = place.get("location", {})
            results.append({
                "name": display_name,
                "address": address,
                "location": {
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude")
                }
            })

        return {
            "status": "success",
            "place_type": place_type,
            "count": len(results),
            "places": results
        }
    except Exception as e:
        return {"status": "error", "message": f"Places API searchNearby error: {str(e)}"}


BUCKET_NAME = "travel-concierge-media-qwiklabs-gcp-02-877388a9a06c"
_storage_client = None


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        key_file = "/config/Desktop/Session1/sa-key.json"
        if os.path.exists(key_file) and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def generate_destination_image(prompt: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Generate a destination image using gemini-3.1-flash-lite-image model, save as an artifact, and upload to GCS.

    Args:
        prompt: Visual prompt describing the destination, attraction, or hotel image to generate.
        tool_context: ADK ToolContext used to record the generated image artifact.

    Returns:
        A dictionary containing the public HTTPS Cloud Storage URL of the generated image.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=[prompt],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )

        image_bytes = None
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break

        if not image_bytes:
            return {"status": "error", "message": "No image data returned from gemini-3.1-flash-lite-image model."}

        timestamp = int(time.time())
        clean_name = "".join(c if c.isalnum() else "_" for c in prompt[:20]).strip("_") or "destination"
        filename = f"{clean_name}_{timestamp}.png"

        # 1. Save artifact with tool_context for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to public Cloud Storage bucket
        gcs_client = get_storage_client()
        bucket = gcs_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/png")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "image_url": public_url,
            "filename": filename,
            "message": f"Successfully generated destination image and uploaded to Cloud Storage."
        }
    except Exception as e:
        return {"status": "error", "message": f"Image generation failed: {str(e)}"}


def generate_destination_video(prompt: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Generate a short video for a destination, hotel, or attraction using Google's Omni model (gemini-omni-flash-preview) in the global region. Saves as an artifact and uploads to public Cloud Storage.

    Args:
        prompt: Visual prompt describing the video clip to generate for a destination or attraction.
        tool_context: ADK ToolContext used to record the generated video artifact.

    Returns:
        A dictionary containing the public HTTPS Cloud Storage URL of the generated video.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt
        )

        video_bytes = None
        out_vid = getattr(interaction, "output_video", None)
        if out_vid:
            data = getattr(out_vid, "data", None)
            if isinstance(data, bytes):
                video_bytes = data
            elif isinstance(data, str):
                video_bytes = base64.b64decode(data)

        if not video_bytes and hasattr(interaction, "steps"):
            for step in getattr(interaction, "steps", []) or []:
                content = getattr(step, "content", None)
                if content and getattr(content, "data", None):
                    d = content.data
                    if isinstance(d, bytes):
                        video_bytes = d
                        break
                    elif isinstance(d, str):
                        video_bytes = base64.b64decode(d)
                        break

        if not video_bytes:
            return {"status": "error", "message": "No video data returned from gemini-omni-flash-preview model."}

        timestamp = int(time.time())
        clean_name = "".join(c if c.isalnum() else "_" for c in prompt[:20]).strip("_") or "destination_video"
        filename = f"{clean_name}_{timestamp}.mp4"

        # 1. Save artifact with tool_context for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to public Cloud Storage bucket
        gcs_client = get_storage_client()
        bucket = gcs_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "video_url": public_url,
            "filename": filename,
            "message": "Successfully generated destination video and uploaded to Cloud Storage."
        }
    except Exception as e:
        return {"status": "error", "message": f"Video generation failed: {str(e)}"}




