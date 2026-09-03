Make sure you have installed [uv](https://docs.astral.sh/uv/) and [Task](https://taskfile.dev/).

Set `AMAP_KEY` in the environment or in a local `.env` file before starting the
planner. The service fails fast when the key is missing so geocoding failures
cannot be mistaken for valid itinerary data. Never commit a real key.

Run `task install` to set up the development environment.
