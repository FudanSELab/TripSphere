# Review Summary MCP migration plan

1. Add failing unit tests for the chat-side page-context headers, the removal
   of `review_summary` from remote A2A discovery, and summary service state
   handling.
2. Extract A2A-independent logic from `A2aAgentExecutor` into
   `ReviewSummaryService`, preserving preflight, postflight, evidence, and
   dependency-failure behavior.
3. Add REST and FastMCP adapters that share the same service instance. The MCP
   adapter accepts only `query` and takes target metadata from trusted headers.
4. Replace the review-summary A2A application lifecycle with normal FastAPI
   lifecycle management while retaining Nacos naming registration.
5. Configure chat-service with a direct Streamable HTTP `McpToolset`; remove
   review-summary from Nacos AI remote-agent discovery and update instructions.
6. Remove stale A2A/Nacos AI source files and dependencies, update lockfiles
   and compose configuration, then run focused tests, static checks, compose
   validation, and image builds.
