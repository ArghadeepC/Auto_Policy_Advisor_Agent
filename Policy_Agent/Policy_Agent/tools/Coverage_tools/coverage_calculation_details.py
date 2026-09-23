def coverage_calculation(
    base_premium: float,
    age_factor: float,
    driving_history_factor: float,
    years_licensed_factor: float,
    mileage_factor: float,
    usage_factor: float,
    location_factor: float,
    safety_discount: float,
    idv_value: float,
    collision_percentage: float,
    comprehensive_percentage: float,
    liability_limit: float,
    liability_limit_multiplier: float,
):
    liability_only = (
        base_premium * liability_limit_multiplier * age_factor
        * driving_history_factor * years_licensed_factor * mileage_factor
        * usage_factor * location_factor * safety_discount
    )
    collision_addon = idv_value * collision_percentage
    comprehensive_addon = idv_value * comprehensive_percentage
    return {
        "liability_price": round(liability_only, 2),
        "collision_price": round(liability_only + collision_addon, 2),
        "comprehensive_price": round(liability_only + comprehensive_addon, 2),
        "max_coverage_liability": liability_limit,
        "max_coverage_collision": liability_limit + idv_value,
        "max_coverage_comprehensive": liability_limit + idv_value,
    }

coverage_calculation_tool = coverage_calculation
