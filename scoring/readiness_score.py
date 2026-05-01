from models import ValidationCheck


def calculate_readiness_score(checks: list[ValidationCheck]) -> int:
    if not checks:
        return 0

    passed_checks = sum(1 for check in checks if check.passed)
    return round((passed_checks / len(checks)) * 100)


def get_readiness_status(score: int) -> str:
    if score == 100:
        return "Ready for Work"
    if score >= 75:
        return "Needs Refinement"
    return "Not Ready"
