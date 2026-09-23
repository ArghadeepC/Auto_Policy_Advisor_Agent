ADDON_CATALOG = {
    "Roadside Assistance": 40.00,
    "Rental Car Coverage": 70.00,
    "Gap Insurance": 120.00,
}

def plan_breakdown(selected_plan: str, base_price: float, addon_names: list[str], discount_percentage: float = 10):
    addons = []
    addons_total = 0.0
    for name in addon_names or []:
        if name not in ADDON_CATALOG:
            return {"error": f"'{name}' is not a valid add-on. Choose from: {list(ADDON_CATALOG.keys())}"}
        price = ADDON_CATALOG[name]
        addons.append({"name": name, "price": price})
        addons_total += price
    subtotal = float(base_price) + addons_total
    discount_amount = subtotal * (float(discount_percentage) / 100)
    return {
        "coverage": selected_plan,
        "base_price": round(float(base_price), 2),
        "addons": addons,
        "addons_total": round(addons_total, 2),
        "discount_percentage": discount_percentage,
        "discount_amount": round(discount_amount, 2),
        "total_premium": round(subtotal - discount_amount, 2),
    }

plan_breakdown_tool = plan_breakdown
