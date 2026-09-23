import logging
from local_data import load_json

logger = logging.getLogger(__name__)

def fetch_vehicle_driver_accident_details(vin: str, license_number: str) -> dict:
    vehicles = load_json("vehicles.json")
    drivers = load_json("drivers.json")
    accidents = load_json("accidents.json")
    vehicle = next((r for r in vehicles if str(r.get("vin", "")).lower() == vin.lower()), None)
    driver = next((r for r in drivers if str(r.get("license_number", r.get("license", ""))).lower() == license_number.lower()), None)
    accident = next((r for r in accidents if str(r.get("vin", "")).lower() == vin.lower()), None)
    return {
        "vehicle_details": vehicle or {"error": "Vehicle not found"},
        "driver_details": driver or {"error": "Driver not found"},
        "accident_details": accident or {"accidents": 0},
    }

lookup_tool = fetch_vehicle_driver_accident_details
