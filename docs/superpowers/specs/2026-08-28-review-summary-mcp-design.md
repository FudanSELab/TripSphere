# Review Summary MCP migration design

## Context

`trip-review-summary` currently starts an A2A application and publishes an
AgentCard through Nacos AI. The installed `a2a-sdk` no longer provides the
imported `a2a.server.apps` module, so the service exits during startup.

The chat service currently discovers `review_summary` as a remote A2A agent.
Review requests already depend on the chat page context for their target ID
and type.

## Decision

Review Summary will be a normal HTTP service:

- Keep normal Nacos service registration because the service and its worker
  still use Nacos naming to find `trip-review-service`.
- Remove A2A routes, AgentCard publication, Nacos AI registration, and the
  A2A SDK dependency from `trip-review-summary`.
- Move the existing summary logic into a reusable `ReviewSummaryService`.
- Expose the existing state contract through a REST endpoint and expose
  `summarize_reviews(query)` through a Streamable HTTP MCP endpoint at
  `/mcp`.
- Configure `trip-chat-service` with an ADK `McpToolset` that connects to
  `trip-review-summary` directly over the Docker network.

## Target context and trust boundary

The MCP tool accepts only the natural-language query. `trip-chat-service`
derives `X-Review-Target-Id` and `X-Review-Target-Type` from the mounted page
context and sends them through the MCP toolset's dynamic header provider.
The MCP server reads those headers from the MCP request context and rejects
missing or invalid values. Therefore a target mentioned in the conversation
cannot replace the currently mounted page target.

## Compatibility

The summary result retains the current `ReviewState` schema and its explicit
statuses: `success`, `empty_reviews`, `index_missing`, and
`dependency_failure`. Existing index-building APIs and the summary worker are
unchanged.
