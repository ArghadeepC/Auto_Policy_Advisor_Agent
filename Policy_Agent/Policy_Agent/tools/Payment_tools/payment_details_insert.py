import uuid
from datetime import datetime, timezone
from local_data import load_json, save_json

def insert_payment(CustomerName: str, Vehicle: str, VIN: str, PlateNumber: str, License: str,
                   Address: str, Policytype: str, ZipCode: str, PaymentMethod: str,
                   PaymentAmount: float, PaymentStatus: str):
    transaction_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    customer_id = f"{CustomerName.replace(' ', '_')}_{datetime.now().strftime('%d%f')}"
    policy_id = f"0000{License.replace(' ', '_')}{ZipCode.replace(' ', '_')}"
    row = {
        "Transaction_ID": transaction_id, "Customer_ID": customer_id, "Policy_ID": policy_id,
        "CustomerName": CustomerName, "Vehicle": Vehicle, "Vehicle_Number": VIN,
        "Plate_Number": PlateNumber, "License": License, "Address": Address,
        "Policy_Type": Policytype, "PaymentMethod": PaymentMethod,
        "PaymentAmount": float(PaymentAmount), "PaymentStatus": PaymentStatus,
        "PaymentDateTime": now,
    }
    payments = load_json("payments.json")
    payments.append(row)
    save_json("payments.json", payments)
    return {"success": True, "message": "Payment recorded successfully", **{k: row[k] for k in ("Transaction_ID", "Customer_ID", "Policy_ID", "PaymentDateTime")}}

insert_payment_tool = insert_payment
