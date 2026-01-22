RESEARCH_AND_PLAN_PROMPT = """Create a complete {num_days}-day itinerary for {destination}.

User Preferences:
- Interests: {interests}
- Pace: {pace} ({activities_per_day} activities per day)
- Dates: {start_date} to {end_date}
- Additional: {additional_preferences}

Available Attractions:
{attractions}

IMPORTANT: When selecting attractions, you MUST use the EXACT name as listed above (copy the name precisely).
Do not translate or modify the attraction names.

Create a realistic daily schedule with proper timing. Each day should have {activities_per_day} activities.
Include meals and leisure time where appropriate.
Return a complete itinerary plan with destination info, daily activities, highlights, and total cost.
""".strip()  # noqa: E501
