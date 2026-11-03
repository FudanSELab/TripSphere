from typing import Any, Awaitable, Callable, Dict, List, Optional

from ag_ui_adk.adk_agent import ADKAgent, ExecutionState, RunAgentInput
from opentelemetry import context as otel_context


class RootedBackgroundADKAgent(ADKAgent):
    async def _start_background_execution(
        self,
        input: RunAgentInput,
        *,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        message_batch: Optional[List[Any]] = None,
        on_accepted: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> ExecutionState:
        trace_token = otel_context.attach(otel_context.Context())
        try:
            return await super()._start_background_execution(
                input,
                tool_results=tool_results,
                message_batch=message_batch,
                on_accepted=on_accepted,
            )
        finally:
            otel_context.detach(trace_token)
