If you want to run order_assistant with Google ADK's Web UI:

```bash
uv run adk web --log_level debug src/
```

To start the order_assistant with uvicorn:

```bash
uv run uvicorn order_assistant.asgi:app --host 0.0.0.0 --port 24211
```