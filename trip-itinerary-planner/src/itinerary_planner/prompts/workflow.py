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


MARKDOWN_GENERATION_PROMPT = """你是一个旅行行程文案撰写专家。请根据以下结构化行程数据，生成一份优美的中文旅行行程方案。

行程数据：
{itinerary_json}

要求：
1. 使用 Markdown 格式
2. 按天组织（第一天、第二天……）
3. 每个活动包含时间、地点、简要描述和预估费用
4. 每天结尾加一句温馨提示或小贴士
5. 开头写一段简短的行程概述
6. 结尾写一段总结，包含总预估费用和旅行亮点
7. 语言自然流畅，像旅行博主的推荐文章
8. 不要输出任何代码块标记，直接输出 Markdown 内容
""".strip()  # noqa: E501
