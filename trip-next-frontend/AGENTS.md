# Next.js: ALWAYS read docs before coding

Before any Next.js work, find and read the relevant doc in `node_modules/next/dist/docs/`. Your training data is outdated — the docs are the source of truth.

## Next.js 16 `proxy.ts` convention

From Next.js 16 onward, use `proxy.ts` instead of `middleware.ts`.

# CopilotKit V2 API usage

Provider component `CopilotKit` is shared across v1 and v2 APIs. It must be imported from the root package `@copilotkit/react-core`, not from the v2 subpackage. No need to migrate to `CopilotKitProvider` in `@copilotkit/react-core/v2`.

When writing or modifying CopilotKit code, **always use V2 API**. Consult CopilotKit knowledge via MCP tools for the latest patterns.

# Code Structure & Organization

- Component design: Extract reusable components; avoid duplicating UI logic across pages. Follow React composition patterns for flexible, maintainable APIs.
- Utility functions: Organize helpers into `lib/` or `utils/` with clear categorization. Avoid scattered inline utilities.
- Colocation: Keep related files together (component + styles + tests + types).

# UI/UX & Theming

- Unified theme: Use ShadcnUI and TailwindCSS design tokens consistently. Do NOT hardcode colors (e.g., `#3b82f6`, `rgb(59,130,246)`). Use semantic tokens like `bg-primary`, `text-muted-foreground`, `border-border`.
- CSS variables: Leverage the CSS variable system in `globals.css` for theming.
- Consistent design language: Maintain uniform spacing, typography, border-radius, and shadows across all components.
- Accessibility: Follow WCAG guidelines — proper contrast, keyboard navigation, ARIA attributes.

# Best Practices

- Use latest stable patterns for Next.js (App Router, Server Components, Server Actions).
- Follow ShadcnUI conventions — use `cn()` for conditional classes, prefer composition over prop drilling.
- Prefer Server Components by default; use `"use client"` only when necessary (interactivity, hooks, browser APIs).

# Refactoring Guidelines

When refactoring this frontend, **leverage available Skills and MCP tools** for guidance:

| Task                       | Required Action                                                      |
| -------------------------- | -------------------------------------------------------------------- |
| Component architecture     | Read and follow `shadcn` skill + `vercel-composition-patterns` skill |
| React/Next.js optimization | Read and follow `vercel-react-best-practices` skill                  |
| UI/UX design review        | Read and follow `web-design-guidelines` skill                        |
| CopilotKit code            | **MUST** use V2 API — query CopilotKit knowledge via MCP tools       |

## Workflow

1. Before making changes, read the relevant skill(s) listed above.
2. For CopilotKit, always consult MCP tools to get the latest V2 API patterns.
3. Apply skill guidance to ensure consistency with modern best practices.
