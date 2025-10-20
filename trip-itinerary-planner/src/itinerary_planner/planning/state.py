"""State definitions for the itinerary planning workflow."""

from typing import Any, TypedDict


class Question(TypedDict):
    """A question to ask the user."""

    question_id: str
    question_text: str
    suggested_answers: list[str]
    requires_answer: bool


class ItineraryState(TypedDict):
    """State object for the itinerary planning workflow."""

    # Input fields
    user_id: str
    destination: str
    start_date: str
    end_date: str
    interests: list[str]
    budget_level: str
    num_travelers: int
    preferences: dict[str, str]

    # Planning state
    destination_info: str
    activity_suggestions: list[dict[str, Any]]
    daily_schedule: dict[int, list[dict[str, Any]]]

    # Human-in-the-loop fields
    pending_question: Question | None
    user_responses: dict[str, str]  # Maps question_id to answer
    needs_user_input: bool

    # Output fields
    itinerary: dict[str, Any]
    error: str | None
