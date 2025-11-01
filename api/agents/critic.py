from api.models import PlanResponse

def validate(response: PlanResponse) -> list[str]:
    issues = []
    if response.total_cost_estimate_eur <= 0:
        issues.append("Total cost is zero — likely a planning error.")
    return issues