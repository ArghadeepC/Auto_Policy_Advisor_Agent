def IDV_calculation(vehicle_price: float, depreciation_rate: float) -> float:
    """Calculate insured declared value from vehicle price and depreciation rate."""
    return round(float(vehicle_price) * (1 - float(depreciation_rate)), 2)

IDV_calculation_tool = IDV_calculation
