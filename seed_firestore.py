import sys
from google.cloud import firestore

# Hardcode project ID as requested to prevent Agent Platform project-number resolution issues
PROJECT_ID = "qwiklabs-gcp-02-877388a9a06c"

def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")

    sample_items = [
        {
            "id": "sf-golden-gate",
            "name": "Golden Gate Bridge",
            "city": "San Francisco",
            "category": "Attraction",
            "description": "Iconic red suspension bridge with scenic bay views and walking paths.",
            "price_per_day": 0.0,
            "rating": 4.9,
            "tags": ["scenic", "landmark", "outdoor"]
        },
        {
            "id": "sf-fisherman-wharf-hotel",
            "name": "Fisherman's Wharf Luxury Hotel",
            "city": "San Francisco",
            "category": "Hotel",
            "description": "Boutique waterfront hotel near Pier 39 with harbor views.",
            "price_per_day": 250.0,
            "rating": 4.7,
            "tags": ["waterfront", "luxury", "hotel"]
        },
        {
            "id": "ny-central-park",
            "name": "Central Park Guided Bike Tour",
            "city": "New York",
            "category": "Activity",
            "description": "2-hour guided bike tour through Central Park's famous landmarks.",
            "price_per_day": 35.0,
            "rating": 4.8,
            "tags": ["outdoors", "guided", "cycling"]
        },
        {
            "id": "ny-empire-state",
            "name": "Empire State Building Observatory",
            "city": "New York",
            "category": "Attraction",
            "description": "86th floor open-air observatory offering 360-degree views of NYC.",
            "price_per_day": 45.0,
            "rating": 4.6,
            "tags": ["landmark", "viewpoint", "iconic"]
        },
        {
            "id": "kyoto-arashiyama",
            "name": "Arashiyama Bamboo Grove",
            "city": "Kyoto",
            "category": "Attraction",
            "description": "Serene bamboo forest path near historic temples.",
            "price_per_day": 0.0,
            "rating": 4.9,
            "tags": ["nature", "scenic", "historic"]
        }
    ]

    print("Seeding destinations collection...")
    for item in sample_items:
        doc_ref = collection_ref.document(item["id"])
        doc_ref.set(item)
        print(f"  ✓ Seeded destination: {item['name']} ({item['city']})")

    print("\n✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
