from local_data import load_json

def fetch_driver_related_details(driver_id: str) -> dict:
    records = load_json("driver_history.json")
    row = next((r for r in records if str(r.get("driver_id", "")).lower() == str(driver_id).lower()), None)
    if not row:
        return {
            "insurance_history": {"error": "Driver history not found"},
            "license_status": {"error": "Driver history not found"},
            "violation_details": {"error": "Driver history not found"},
        }
    return {
        "insurance_history": row.get("insurance_history", {}),
        "license_status": row.get("license_status", {}),
        "violation_details": row.get("violation_details", {}),
    }

driver_lookup_tool = fetch_driver_related_details
