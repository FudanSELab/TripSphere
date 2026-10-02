from __future__ import annotations

import argparse
import ast
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_GROUP = "TRIPSPHERE_PROMPTS"


@dataclass(frozen=True)
class PromptSource:
    data_id: str
    source_file: Path
    constant_name: str


PROMPT_SOURCES = (
    PromptSource(
        data_id="tripsphere.chat.system-prompt",
        source_file=ROOT_DIR / "trip-chat-service/src/chat/prompts/agent.py",
        constant_name="DELEGATOR_INSTRUCTION",
    ),
    PromptSource(
        data_id="tripsphere.itinerary-planner.chat-prompt",
        source_file=ROOT_DIR
        / "trip-itinerary-planner/src/itinerary_planner/prompts/chat_agent.py",
        constant_name="CHAT_AGENT_INSTRUCTION",
    ),
    PromptSource(
        data_id="tripsphere.itinerary-planner.research-prompt",
        source_file=ROOT_DIR
        / "trip-itinerary-planner/src/itinerary_planner/prompts/workflow.py",
        constant_name="RESEARCH_AND_PLAN_PROMPT",
    ),
    PromptSource(
        data_id="tripsphere.itinerary-planner.markdown-prompt",
        source_file=ROOT_DIR
        / "trip-itinerary-planner/src/itinerary_planner/prompts/workflow.py",
        constant_name="MARKDOWN_GENERATION_PROMPT",
    ),
    PromptSource(
        data_id="tripsphere.itinerary-planner.regenerate-day-prompt",
        source_file=ROOT_DIR
        / "trip-itinerary-planner/src/itinerary_planner/prompts/workflow.py",
        constant_name="REGENERATE_DAY_PROMPT",
    ),
    PromptSource(
        data_id="tripsphere.order-assistant.system-prompt",
        source_file=ROOT_DIR / "trip-order-assistant/src/order_assistant/agent.py",
        constant_name="INSTRUCTION",
    ),
    PromptSource(
        data_id="tripsphere.review-summary.query-prompt",
        source_file=ROOT_DIR
        / "trip-review-summary/src/review_summary/prompts/query/"
        "local_search_system_prompt.py",
        constant_name="LOCAL_SEARCH_SYSTEM_PROMPT",
    ),
)


def _literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"lstrip", "rstrip", "strip"}
        and not node.args
        and not node.keywords
    ):
        content = _literal_string(node.func.value)
        return getattr(content, node.func.attr)()

    raise ValueError("Prompt constant must be a string literal or a string trim call")


def _read_constant(source: PromptSource) -> str:
    tree = ast.parse(source.source_file.read_text(encoding="utf-8"))
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == source.constant_name
            for target in statement.targets
        ):
            continue
        return _literal_string(statement.value)
    raise ValueError(
        f"Could not find {source.constant_name} in {source.source_file}"
    )


def _config_endpoint(server_address: str) -> str:
    address = server_address.strip().rstrip("/")
    if not address.startswith(("http://", "https://")):
        address = f"http://{address}"
    if address.endswith("/nacos"):
        return f"{address}/v1/cs/configs"
    return f"{address}/nacos/v1/cs/configs"


def _publish_prompt(
    session: requests.Session,
    endpoint: str,
    source: PromptSource,
    content: str,
    *,
    namespace: str,
    group: str,
    username: str,
    password: str,
    timeout: float,
) -> None:
    params: dict[str, Any] = {
        "dataId": source.data_id,
        "group": group,
        "tenant": namespace,
        "type": "text",
    }
    if username:
        params["username"] = username
    if password:
        params["password"] = password

    response = session.post(
        endpoint,
        params=params,
        data={"content": content},
        timeout=timeout,
    )
    response.raise_for_status()
    if response.text.strip().lower() != "true":
        raise RuntimeError(
            f"Nacos rejected {source.data_id}: {response.text.strip() or '<empty>'}"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish online TripSphere Prompts to Nacos Config."
    )
    parser.add_argument(
        "--server-address",
        default=os.getenv("NACOS_SERVER_ADDRESS", "localhost:8848"),
    )
    parser.add_argument(
        "--namespace",
        default=os.getenv("NACOS_NAMESPACE_ID", "public"),
    )
    parser.add_argument(
        "--group",
        default=os.getenv("PROMPT_CONFIG_GROUP", DEFAULT_GROUP),
    )
    parser.add_argument(
        "--username",
        default=os.getenv("NACOS_USERNAME", "nacos"),
    )
    parser.add_argument(
        "--password",
        default=os.getenv("NACOS_PASSWORD", "nacos"),
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--only",
        action="append",
        dest="data_ids",
        help="Publish only the selected dataId. May be repeated.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    selected_ids = set(args.data_ids or ())
    sources = tuple(
        source
        for source in PROMPT_SOURCES
        if not selected_ids or source.data_id in selected_ids
    )
    unknown_ids = selected_ids - {source.data_id for source in PROMPT_SOURCES}
    if unknown_ids:
        raise SystemExit(f"Unknown dataId(s): {', '.join(sorted(unknown_ids))}")

    endpoint = _config_endpoint(args.server_address)
    session = requests.Session()
    for source in sources:
        content = _read_constant(source).strip()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if args.dry_run:
            print(
                f"dry-run data_id={source.data_id} "
                f"source={source.source_file.relative_to(ROOT_DIR)} "
                f"hash={content_hash}"
            )
            continue
        _publish_prompt(
            session,
            endpoint,
            source,
            content,
            namespace=args.namespace,
            group=args.group,
            username=args.username,
            password=args.password,
            timeout=args.timeout,
        )
        print(
            f"published data_id={source.data_id} "
            f"group={args.group} hash={content_hash}"
        )


if __name__ == "__main__":
    main()
