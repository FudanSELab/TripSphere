import logging

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint  # pyright: ignore
from ag_ui_adk.endpoint import make_extract_headers  # type: ignore
from fastapi import FastAPI

from order_assistant.agent import app as adk_app

logging.basicConfig(level=logging.DEBUG)

agent = ADKAgent.from_app(
    adk_app,
    user_id_extractor=lambda input: input.state.get("headers", {}).get(
        "user_id", "anonymous"
    ),
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(debug=True)

add_adk_fastapi_endpoint(
    app,
    agent,
    extract_state_from_request=make_extract_headers(["x-user-id"]),
)
