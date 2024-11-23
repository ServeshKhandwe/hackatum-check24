# main.py

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import json
import os

app = FastAPI()

# Data models
class Offer(BaseModel):
    ID: str  # UUID
    data: str  # base64 encoded 256 Byte array
    mostSpecificRegionID: int
    startDate: int  # int64
    endDate: int  # int64
    numberSeats: int
    price: int
    carType: str
    hasVollkasko: bool
    freeKilometers: int

class SearchResultOffer(BaseModel):
    ID: str  # UUID
    data: str  # base64 encoded 256 Byte array

class PriceRange(BaseModel):
    start: int
    end: int
    count: int

class CarTypeCount(BaseModel):
    small: int
    sports: int
    luxury: int
    family: int

class SeatsCount(BaseModel):
    numberSeats: int
    count: int

class FreeKilometerRange(BaseModel):
    start: int
    end: int
    count: int

class VollkaskoCount(BaseModel):
    trueCount: int
    falseCount: int

class GetOffersResponse(BaseModel):
    offers: List[SearchResultOffer]
    priceRanges: List[PriceRange]
    carTypeCounts: CarTypeCount
    seatsCount: List[SeatsCount]
    freeKilometerRange: List[FreeKilometerRange]
    vollkaskoCount: VollkaskoCount

# In-memory database
offers_db = []

# Load regions data (if available)
regions_data = {}
regions_file = 'regions.json'

if os.path.exists(regions_file):
    with open(regions_file) as f:
        regions_data = json.load(f)
else:
    print(f"Regions file {regions_file} not found. Using empty regions data.")
    regions_data = {}  # Use empty dictionary as placeholder

# POST /api/offers
@app.post("/api/offers")
def create_offers(offers: List[Offer]):
    # Blocking operation: process offers before returning
    try:
        # Convert Offer objects to dictionaries
        offer_dicts = [offer.dict() for offer in offers]
        offers_db.extend(offer_dicts)
        return {"status": "success", "message": "Offers created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /api/offers
@app.get("/api/offers", response_model=GetOffersResponse)
def get_offers(
    regionID: int = Query(..., description="Region ID for which offers are returned."),
    timeRangeStart: int = Query(..., description="Timestamp (ms since UNIX epoch) from when offers are considered (inclusive)"),
    timeRangeEnd: int = Query(..., description="Timestamp (ms since UNIX epoch) until when offers are considered (inclusive)"),
    numberDays: int = Query(..., description="The number of full days (24h) the car is available within the rangeStart and rangeEnd"),
    sortOrder: str = Query(..., description="The order in which offers are returned.", regex="^(price-asc|price-desc)$"),
    page: int = Query(..., description="The page number from pagination"),
    pageSize: int = Query(..., description="The number of offers per page"),
    priceRangeWidth: int = Query(..., description="The width of the price range blocks in cents."),
    minFreeKilometerWidth: int = Query(..., description="The width of the min free kilometer in km."),
    minNumberSeats: Optional[int] = Query(None, description="How many seats the returned cars each have"),
    minPrice: Optional[int] = Query(None, description="Minimum (inclusive) price the offers have in cent"),
    maxPrice: Optional[int] = Query(None, description="Maximum (exclusive) price the offers have in cent"),
    carType: Optional[str] = Query(None, description="The car type.", regex="^(small|sports|luxury|family)$"),
    onlyVollkasko: Optional[bool] = Query(None, description="Whether only offers with vollkasko are returned"),
    minFreeKilometer: Optional[int] = Query(None, description="Minimum number of kilometers that the offer includes for free")
):
    # Build mandatory and optional filters
    mandatory_filters = {
        "regionID": regionID,
        "timeRangeStart": timeRangeStart,
        "timeRangeEnd": timeRangeEnd,
        "numberDays": numberDays
    }
    optional_filters = {
        "minNumberSeats": minNumberSeats,
        "minPrice": minPrice,
        "maxPrice": maxPrice,
        "carType": carType,
        "onlyVollkasko": onlyVollkasko,
        "minFreeKilometer": minFreeKilometer
    }

    # Remove None values from optional_filters
    optional_filters = {k: v for k, v in optional_filters.items() if v is not None}

    # Filter offers
    filtered_offers = [offer for offer in offers_db if matches_filters(offer, mandatory_filters, optional_filters)]

    # Apply sorting
    reverse_sort = True if sortOrder == "price-desc" else False
    filtered_offers.sort(key=lambda x: (x['price'], x['ID']), reverse=reverse_sort)

    # Implement pagination
    start_index = (page - 1) * pageSize
    end_index = start_index + pageSize
    paginated_offers = filtered_offers[start_index:end_index]

    # Create SearchResultOffer objects
    search_result_offers = [
        SearchResultOffer(ID=offer['ID'], data=offer['data']) for offer in paginated_offers
    ]

    # Compute aggregations
    price_ranges, car_type_counts, seats_counts, free_kilometer_ranges, vollkasko_counts = compute_aggregations(
        filtered_offers, priceRangeWidth, minFreeKilometerWidth, mandatory_filters, optional_filters
    )

    # Prepare response
    response = GetOffersResponse(
        offers=search_result_offers,
        priceRanges=price_ranges,
        carTypeCounts=car_type_counts,
        seatsCount=seats_counts,
        freeKilometerRange=free_kilometer_ranges,
        vollkaskoCount=vollkasko_counts
    )

    return response

# DELETE /api/offers
@app.delete("/api/offers")
def delete_offers():
    offers_db.clear()
    return {"status": "success", "message": "All offers deleted"}

# Helper functions
def matches_filters(offer, mandatory_filters, optional_filters):
    # Placeholder: Accept all offers
    return True

def compute_aggregations(filtered_offers, priceRangeWidth, minFreeKilometerWidth, mandatory_filters, optional_filters):
    # Placeholder implementations

    # Price Ranges
    price_ranges = []

    # Car Type Counts
    car_type_counts = CarTypeCount(small=0, sports=0, luxury=0, family=0)

    # Seats Counts
    seats_counts = []

    # Free Kilometer Ranges
    free_kilometer_ranges = []

    # Vollkasko Counts
    vollkasko_counts = VollkaskoCount(trueCount=0, falseCount=0)

    # Return empty aggregations
    return price_ranges, car_type_counts, seats_counts, free_kilometer_ranges, vollkasko_counts
