# Changelog

Please update changelog as part of any significant pull request. Place short description of your change into "Unreleased" section. During the release process, the "Unreleased" section content is used to generate the release notes.

## Unreleased

- The initial code repository is created.
- **trip-itinerary-planner**: Added AI-powered itinerary planning microservice using LangGraph and OpenAI
  - Intelligent multi-stage planning workflow (research, suggest, schedule, finalize)
  - gRPC API for itinerary generation
  - Integration with Nacos service discovery
  - OpenTelemetry observability
- **trip-itinerary-planner**: Added Human-in-the-Loop functionality
  - New `PlanItineraryInteractive` streaming RPC for real-time user interaction
  - AI can ask clarifying questions during planning to gather additional information
  - Support for status updates, questions, and bidirectional streaming
  - Enhanced workflow with conditional edges for interactive decision-making
  - Extended state management to track questions and user responses
  - Example client demonstrating interactive planning workflow