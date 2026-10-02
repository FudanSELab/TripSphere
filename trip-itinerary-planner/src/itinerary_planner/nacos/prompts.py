from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from opentelemetry import trace
from v2.nacos import ClientConfigBuilder, ConfigParam, NacosConfigService  # type: ignore

logger = logging.getLogger(__name__)

PromptSource = Literal["local", "nacos"]


@dataclass(frozen=True)
class PromptSpec:
    key: str
    data_id: str
    default: str
    required_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptSnapshot:
    key: str
    data_id: str
    content: str
    source: PromptSource
    content_hash: str


class PromptConfigError(RuntimeError):
    """Raised when a Prompt configuration cannot be used safely."""


class PromptStore:
    def __init__(
        self,
        group: str,
        required: bool,
        config_service: NacosConfigService | None,
    ) -> None:
        self.group = group
        self.required = required
        self._config_service = config_service

    @classmethod
    async def create(
        cls,
        *,
        server_address: str,
        namespace_id: str,
        username: str,
        password: str,
        group: str,
        enabled: bool,
        required: bool,
        timeout_ms: int,
    ) -> PromptStore:
        if not enabled:
            if required:
                raise PromptConfigError(
                    "Nacos Prompt configuration is required but disabled"
                )
            logger.info("Nacos Prompt loading is disabled; using local defaults")
            return cls(group=group, required=required, config_service=None)

        builder = (
            ClientConfigBuilder()
            .server_address(server_address)
            .namespace_id(namespace_id)
            .timeout_ms(timeout_ms)
        )
        # Nacos 3.x serves client config over the SDK-compatible gRPC endpoint.
        # Passing console credentials makes nacos-sdk-python call the removed
        # legacy login endpoint before it can read the configuration.

        try:
            config_service = await NacosConfigService.create_config_service(
                client_config=builder.build()
            )
        except Exception as exc:
            if required:
                raise PromptConfigError(
                    "Nacos Prompt configuration is required but unavailable"
                ) from exc
            logger.warning(
                "Nacos Prompt configuration is unavailable; using local defaults: %s",
                exc,
            )
            config_service = None

        return cls(
            group=group,
            required=required,
            config_service=config_service,
        )

    async def load_all(
        self,
        specs: Sequence[PromptSpec],
    ) -> dict[str, PromptSnapshot]:
        return {spec.key: await self.load(spec) for spec in specs}

    async def load(self, spec: PromptSpec) -> PromptSnapshot:
        if self._config_service is not None:
            try:
                content = await self._config_service.get_config(
                    ConfigParam(data_id=spec.data_id, group=self.group)
                )
            except Exception as exc:
                if self.required:
                    raise PromptConfigError(
                        f"Failed to load required Prompt {spec.data_id}"
                    ) from exc
                logger.warning(
                    "Failed to load Prompt %s; using local default: %s",
                    spec.data_id,
                    exc,
                )
            else:
                if content and content.strip():
                    normalized = _validate_content(spec, content)
                    snapshot = _snapshot(spec, normalized, "nacos")
                    logger.info(
                        "Loaded Prompt data_id=%s source=%s hash=%s",
                        snapshot.data_id,
                        snapshot.source,
                        snapshot.content_hash,
                    )
                    return snapshot
                logger.info(
                    "Prompt data_id=%s is not published; using local default",
                    spec.data_id,
                )
                if self.required:
                    raise PromptConfigError(
                        f"Required Prompt {spec.data_id} is not published"
                    )

        normalized = _validate_content(spec, spec.default)
        snapshot = _snapshot(spec, normalized, "local")
        logger.info(
            "Loaded Prompt data_id=%s source=%s hash=%s",
            snapshot.data_id,
            snapshot.source,
            snapshot.content_hash,
        )
        return snapshot

    async def close(self) -> None:
        if self._config_service is None:
            return
        try:
            await self._config_service.shutdown()
        finally:
            self._config_service = None


def _validate_content(spec: PromptSpec, content: str) -> str:
    normalized = content.strip()
    if not normalized:
        raise PromptConfigError(f"Prompt {spec.data_id} must not be empty")

    missing_fields = [
        field
        for field in spec.required_fields
        if "{" + field + "}" not in normalized
    ]
    if missing_fields:
        raise PromptConfigError(
            f"Prompt {spec.data_id} is missing placeholders: "
            f"{', '.join(missing_fields)}"
        )
    return normalized


def _snapshot(
    spec: PromptSpec,
    content: str,
    source: PromptSource,
) -> PromptSnapshot:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return PromptSnapshot(
        key=spec.key,
        data_id=spec.data_id,
        content=content,
        source=source,
        content_hash=content_hash,
    )


_ACTIVE_PROMPTS: dict[str, PromptSnapshot] = {}


def set_active_prompts(prompts: Mapping[str, PromptSnapshot]) -> None:
    _ACTIVE_PROMPTS.clear()
    _ACTIVE_PROMPTS.update(prompts)


def clear_active_prompts() -> None:
    _ACTIVE_PROMPTS.clear()


def get_prompt_snapshot(key: str) -> PromptSnapshot | None:
    return _ACTIVE_PROMPTS.get(key)


def get_prompt(key: str, default: str) -> str:
    snapshot = get_prompt_snapshot(key)
    return snapshot.content if snapshot is not None else default


def annotate_prompt(snapshot: PromptSnapshot | None) -> None:
    if snapshot is None:
        return

    span = trace.get_current_span()
    if not span.is_recording():
        return

    prefix = f"tripsphere.prompt.{_attribute_slug(snapshot.data_id)}"
    span.set_attribute(f"{prefix}.data_id", snapshot.data_id)
    span.set_attribute(f"{prefix}.source", snapshot.source)
    span.set_attribute(f"{prefix}.hash", snapshot.content_hash)
    span.set_attribute("tripsphere.prompt.data_id", snapshot.data_id)
    span.set_attribute("tripsphere.prompt.source", snapshot.source)
    span.set_attribute("tripsphere.prompt.hash", snapshot.content_hash)


def annotate_active_prompts() -> None:
    for snapshot in _ACTIVE_PROMPTS.values():
        annotate_prompt(snapshot)


def _attribute_slug(data_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", data_id).strip("_")
