class PlanningDependencyError(RuntimeError):
    """Raised when a required planning dependency cannot provide usable data."""


class InvalidPlanningResultError(ValueError):
    """Raised when generated itinerary data violates the planning contract."""
