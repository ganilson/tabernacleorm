"""
FastAPI Example 3: Real Estate API with Geospatial Queries
Demonstrates: geospatial queries, location-based search, complex filtering
"""

from typing import List, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel
from tabernacleorm import connect, Model, fields
import math


class Property(Model):
    title = fields.StringField(required=True)
    description = fields.StringField()
    price = fields.FloatField(required=True)
    bedrooms = fields.IntegerField()
    bathrooms = fields.IntegerField()
    area = fields.FloatField()  # in square meters
    property_type = fields.StringField()  # apartment, house, condo
    latitude = fields.FloatField(required=True)
    longitude = fields.FloatField(required=True)
    address = fields.JSONField()
    amenities = fields.JSONField()  # List of amenities
    status = fields.StringField(default="available")
    
    class Meta:
        collection = "properties"


app = FastAPI(title="Real Estate API")


@app.on_event("startup")
async def startup():
    db = connect("sqlite:///realestate.db")
    await db.connect()
    await Property.createTable()


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers (Haversine formula)"""
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


@app.get("/properties/nearby")
async def find_nearby_properties(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    property_type: Optional[str] = None
):
    """Find properties within radius of a location"""
    # Get all properties (in production, use spatial index)
    query = {}
    if min_price:
        query.setdefault("price", {})["$gte"] = min_price
    if max_price:
        query.setdefault("price", {})["$lte"] = max_price
    if bedrooms:
        query["bedrooms"] = bedrooms
    if property_type:
        query["property_type"] = property_type
    
    properties = await Property.find(query).exec()
    
    # Filter by distance
    nearby = []
    for prop in properties:
        distance = calculate_distance(latitude, longitude, prop.latitude, prop.longitude)
        if distance <= radius_km:
            nearby.append({
                "id": str(prop.id),
                "title": prop.title,
                "price": prop.price,
                "bedrooms": prop.bedrooms,
                "distance_km": round(distance, 2),
                "location": {"lat": prop.latitude, "lng": prop.longitude}
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x["distance_km"])
    return nearby


@app.get("/properties/search")
async def search_properties(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    min_area: Optional[float] = None,
    property_type: Optional[str] = None,
    amenities: Optional[List[str]] = Query(None)
):
    """Advanced property search"""
    query = {}
    
    if min_price or max_price:
        price_filter = {}
        if min_price:
            price_filter["$gte"] = min_price
        if max_price:
            price_filter["$lte"] = max_price
        query["price"] = price_filter
    
    if min_bedrooms:
        query["bedrooms"] = {"$gte": min_bedrooms}
    
    if min_area:
        query["area"] = {"$gte": min_area}
    
    if property_type:
        query["property_type"] = property_type
    
    properties = await Property.find(query).sort("-price").exec()
    
    # Filter by amenities if provided
    if amenities:
        properties = [
            p for p in properties
            if all(amenity in (p.amenities or []) for amenity in amenities)
        ]
    
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "price": p.price,
            "bedrooms": p.bedrooms,
            "area": p.area,
            "property_type": p.property_type
        }
        for p in properties
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
