RESEARCH_AND_PLAN_PROMPT = """Create a complete {num_days}-day itinerary for {destination}.

User Preferences:
- Interests: {interests}
- Pace: {pace} ({activities_per_day} activities per day)
- Dates: {start_date} to {end_date}
- Additional: {additional_preferences}

Available Attractions:
{attractions}

Create a realistic daily schedule with proper timing. Each day should have {activities_per_day} activities.
Include breakfast, lunch, dinner, and transportation where appropriate.
Return a complete itinerary plan with destination info, daily activities, highlights, and total cost.
""".strip()  # noqa: E501
