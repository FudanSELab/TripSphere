# Trip Itinerary Planner Service

An AI-powered microservice for intelligent travel itinerary planning using LangGraph and OpenAI.

## Features

- **Intelligent Planning**: Uses LangGraph workflow with OpenAI GPT models for context-aware itinerary generation
- **Human-in-the-Loop**: Interactive planning with AI asking clarifying questions for personalized results
- **Multi-stage Planning**: 
  - Destination research and analysis
  - Intelligent clarification checking
  - Activity suggestion based on interests and budget
  - Daily schedule optimization
  - Complete itinerary finalization
- **gRPC API**: High-performance service interface with streaming support
- **Service Discovery**: Integration with Nacos for service registration
- **Observability**: OpenTelemetry instrumentation for distributed tracing

## Architecture

### LangGraph Workflow

The service uses a LangGraph state machine with the following nodes:

1. **Research Destination**: Gathers comprehensive information about the destination
2. **Check Clarification**: Determines if additional user input is needed
3. **Ask Question** (conditional): Poses clarifying questions to the user
4. **Suggest Activities**: Generates activity recommendations based on user preferences
5. **Create Daily Schedule**: Organizes activities into an optimal daily itinerary
6. **Finalize Itinerary**: Structures and formats the complete trip plan

**Standard Workflow:**
```
[Start] → Research → Check → Suggest Activities → Create Schedule → Finalize → [End]
```

**Interactive Workflow (with Human-in-the-Loop):**
```
[Start] → Research → Check → Ask Question → Incorporate Response → Suggest → Schedule → Finalize → [End]
```

### Tech Stack

- **Python 3.12+**
- **LangGraph**: Workflow orchestration
- **LangChain**: LLM integration
- **OpenAI GPT-4**: Natural language processing
- **gRPC**: Service communication
- **Nacos**: Service discovery and configuration
- **OpenTelemetry**: Observability
- **UV**: Package management

## Configuration

The service can be configured via environment variables:

### Service Configuration
- `SERVICE__NAME`: Service name (default: `trip-itinerary-planner`)
- `SERVICE__NAMESPACE`: Service namespace (default: `tripsphere`)

### gRPC Configuration
- `GRPC__PORT`: gRPC server port (default: `50059`)

### Nacos Configuration
- `NACOS__SERVER_ADDRESS`: Nacos server address (default: `nacos:8848`)
- `NACOS__NAMESPACE_ID`: Nacos namespace ID (default: `public`)
- `NACOS__GROUP_NAME`: Nacos group name (default: `DEFAULT_GROUP`)

### LLM Configuration
- `LLM__API_KEY`: OpenAI API key (required)
- `LLM__BASE_URL`: Custom API base URL for OpenAI-compatible APIs (optional)
  - Default: `None` (uses OpenAI's official API)
  - Example: `https://api.openai.com/v1`
  - Example: `https://your-proxy.com/v1` (for custom proxy)
- `LLM__MODEL`: OpenAI model to use (default: `gpt-4o-mini`)
- `LLM__TEMPERATURE`: Model temperature (default: `0.7`)
- `LLM__MAX_TOKENS`: Maximum tokens per request (default: `4000`)

**Configuration Examples:**

Using .env file:
```bash
cp env.example .env
# Edit .env with your configuration
```

## Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key

### Setup

1. Install dependencies:
```bash
cd trip-itinerary-planner
uv sync
```

2. Generate protobuf files:
```bash
# From the project root
make compile-proto
```

3. Set environment variables:
```bash

```

4. Run the service:
```bash
uv run python -m itinerary_planner.server
```

### Testing

Run tests with pytest:
```bash
uv run pytest
```

## API

### PlanItinerary

Creates a new itinerary based on user preferences (non-interactive, single request/response).

**Request**:
```protobuf
message PlanItineraryRequest {
  string user_id = 1;
  string destination = 2;
  string start_date = 3;  // ISO 8601 format (YYYY-MM-DD)
  string end_date = 4;
  repeated string interests = 5;
  string budget_level = 6;  // "budget", "moderate", or "luxury"
  int32 num_travelers = 7;
  map<string, string> preferences = 8;
}
```

**Response**:
```protobuf
message PlanItineraryResponse {
  string itinerary_id = 1;
  string status = 2;
  Itinerary itinerary = 3;
  string message = 4;
}
```

### PlanItineraryInteractive (New! 🎉)

Creates a new itinerary with human-in-the-loop interaction. The AI can ask clarifying questions during planning to gather additional information for more personalized results.

**Features**:
- Bidirectional streaming for real-time interaction
- Progress updates during planning
- AI-generated clarifying questions
- Support for suggested answers

**Request Stream**:
```protobuf
message PlanItineraryInteractiveRequest {
  oneof request_type {
    InitialRequest initial_request = 1;    // First message
    UserResponse user_response = 2;         // Follow-up answers
  }
}
```

**Response Stream**:
```protobuf
message PlanItineraryInteractiveResponse {
  oneof response_type {
    StatusUpdate status_update = 1;         // Progress updates
    Question question = 2;                  // Questions for user
    FinalItinerary final_itinerary = 3;     // Final result
    ErrorMessage error = 4;                 // Errors
  }
}
```

**Example Flow**:
1. Client sends `InitialRequest` with travel preferences
2. Server responds with `StatusUpdate` messages showing progress
3. Server may send `Question` messages asking for clarification
4. Client responds with `UserResponse` containing answers
5. Server continues planning and sends `FinalItinerary`

See [HUMAN_IN_THE_LOOP.md](./HUMAN_IN_THE_LOOP.md) for detailed documentation and examples.

### RefineItinerary

Refines an existing itinerary (coming soon).

