# TripSphere Agent Rules

For all coding agents working in this repository:

## Toolchain

- JavaScript/TypeScript runtime and package manager: use `bun` with `-b` flag.
- Python package and environment manager: use `uv`.
- Java build and project management: use Maven Wrapper (`./mvnw`), not a global Maven install.

## Code Style & Quality

Maintain a unified coding style to improve code quality and readability:

- Write self-explanatory code: use clear, descriptive names for variables, functions, and classes.
- Avoid spaghetti code: keep functions small and focused, limit nesting depth, and prefer early returns over deep conditionals.
- Minimize comments: Only comment on non-obvious intent, trade-offs, or constraints that the code itself cannot convey.
- Follow language idioms: write idiomatic code for each language (e.g., Pythonic Python, modern ES6+ JavaScript/TypeScript, clean Java).
- Consistent formatting: adhere to project linters and formatters. Do not introduce style inconsistencies.

