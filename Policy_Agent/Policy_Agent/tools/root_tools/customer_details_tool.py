import logging
from local_data import load_json

logger = logging.getLogger(__name__)

def customer_details(custid: str) -> dict:
    if not custid or not custid.strip():
        return {"status": "not_found", "message": "Customer ID is required."}
    custid = custid.strip()
    row = next((r for r in load_json("customers.json") if str(r.get("cust_id", r.get("customer_id", ""))).lower() == custid.lower()), None)
    if not row:
        return {"status": "not_found", "custid": custid}
    return {
        "status": "success",
        "VIN": row.get("vin"), "license_number": row.get("license", row.get("license_number")),
        "custid": row.get("cust_id", row.get("customer_id", custid)),
        "name": row.get("name") or f"{row.get('f_name','')} {row.get('l_name','')}".strip(),
        "policy_end_date": row.get("policy_end_date"), "policy_start_date": row.get("policy_start_date"),
        "base_premium": row.get("base_premium", 0), "add_ons_amount": row.get("add_ons_amount", 0),
        "discount": row.get("discount", 0), "final_premium_amount": row.get("final_premium_amount", 0),
        "add_ons": row.get("add_ons", []), "policy_type": row.get("policy_type", "Auto"),
        "email": row.get("email"), "phone": row.get("ph_no", row.get("phone")),
    }

customer_details_tool = customer_details
