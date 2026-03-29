<!-- BEGIN:nextjs-agent-rules -->

# Next.js: ALWAYS read docs before coding

Before any Next.js work, find and read the relevant doc in `node_modules/next/dist/docs/`. Your training data is outdated — the docs are the source of truth.

## Next.js 16 proxy file convention

From Next.js 16 onward, use `proxy.ts` instead of `middleware.ts`.

<!-- END:nextjs-agent-rules -->

# CopilotKit V2 API usage

Provider component `CopilotKit` is shared across v1 and v2 APIs. It must be imported from the root package `@copilotkit/react-core`, not from the v2 subpackage. No need to migrate to `CopilotKitProvider` in `@copilotkit/react-core/v2`.
