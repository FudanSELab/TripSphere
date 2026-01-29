import time
from typing import Any

from google.adk.errors.already_exists_error import AlreadyExistsError
from google.adk.events.event import Event
from google.adk.sessions import BaseSessionService, Session, _session_util
from google.adk.sessions.base_session_service import (
    GetSessionConfig,
    ListSessionsResponse,
)
from google.adk.sessions.state import State
from pymongo import AsyncMongoClient

from chat.config.settings import get_settings
from chat.utils.uuid import uuid7


class MongoSessionService(BaseSessionService):
    @staticmethod
    def _serialize_event(event: Event) -> dict[str, Any]:
        """Serialize Event to MongoDB-compatible dict."""
        event_dict = event.model_dump()
        # Convert set to list for MongoDB compatibility
        if event_dict.get("long_running_tool_ids") is not None:
            event_dict["long_running_tool_ids"] = list(
                event_dict["long_running_tool_ids"]
            )
        return event_dict

    @staticmethod
    def _deserialize_event(event_data: dict[str, Any]) -> Event:
        """Deserialize Event from MongoDB dict."""
        # Convert list back to set
        if event_data.get("long_running_tool_ids") is not None:
            event_data["long_running_tool_ids"] = set[str](
                event_data["long_running_tool_ids"]
            )
        return Event.model_validate(event_data)

    def __init__(self, mongo_client: AsyncMongoClient[dict[str, Any]]) -> None:
        self.client = mongo_client
        self.database = self.client.get_database(get_settings().mongo.database)
        self.sessions = self.database.get_collection("sessions")
        self.user_state = self.database.get_collection("user_state")
        self.app_state = self.database.get_collection("app_state")

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> Session:
        # Check if session already exists
        if session_id:
            existing = await self.get_session(
                app_name=app_name, user_id=user_id, session_id=session_id
            )
            if existing:
                raise AlreadyExistsError(  # type: ignore
                    f"Session with id {session_id} already exists."
                )

        # Extract state deltas
        state_deltas = _session_util.extract_state_delta(state or {})
        app_state_delta = state_deltas["app"]
        user_state_delta = state_deltas["user"]
        session_state = state_deltas["session"]

        # Update app state
        if app_state_delta:
            await self.app_state.update_one(
                {"_id": app_name},
                {"$set": app_state_delta},
                upsert=True,
            )

        # Update user state
        if user_state_delta:
            await self.user_state.update_one(
                {"_id": f"{app_name}:{user_id}"},
                {"$set": user_state_delta},
                upsert=True,
            )

        # Generate session ID if not provided
        session_id = (
            session_id.strip() if session_id and session_id.strip() else str(uuid7())
        )

        # Create session document
        session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state=session_state or {},
            last_update_time=time.time(),
        )

        # Store in MongoDB
        session_doc = {
            "_id": f"{app_name}:{user_id}:{session_id}",
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "state": session.state,
            "events": list[Event](),
            "last_update_time": session.last_update_time,
        }
        await self.sessions.insert_one(session_doc)

        # Return session with merged state
        return await self._merge_state(app_name, user_id, session)

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: GetSessionConfig | None = None,
    ) -> Session | None:
        """Gets a session."""
        doc = await self.sessions.find_one(
            {"_id": f"{app_name}:{user_id}:{session_id}"}
        )
        if not doc:
            return None

        # Reconstruct Session object
        session = Session(
            app_name=doc["app_name"],
            user_id=doc["user_id"],
            id=doc["session_id"],
            state=doc["state"],
            last_update_time=doc["last_update_time"],
        )

        # Reconstruct events
        for event_data in doc.get("events", []):
            event = self._deserialize_event(event_data)
            session.events.append(event)

        # Apply config filters
        if config:
            if config.num_recent_events:
                session.events = session.events[-config.num_recent_events :]
            if config.after_timestamp:
                i = len(session.events) - 1
                while i >= 0:
                    if session.events[i].timestamp < config.after_timestamp:
                        break
                    i -= 1
                if i >= 0:
                    session.events = session.events[i + 1 :]

        # Return session with merged state
        return await self._merge_state(app_name, user_id, session)

    async def _merge_state(
        self, app_name: str, user_id: str, session: Session
    ) -> Session:
        """Merges app and user state into session state."""
        # Merge app state
        app_state_doc = await self.app_state.find_one({"_id": app_name})
        if app_state_doc:
            for key, value in app_state_doc.items():
                if key != "_id":
                    session.state[State.APP_PREFIX + key] = value

        # Merge user state
        user_state_doc = await self.user_state.find_one(
            {"_id": f"{app_name}:{user_id}"}
        )
        if user_state_doc:
            for key, value in user_state_doc.items():
                if key != "_id":
                    session.state[State.USER_PREFIX + key] = value

        return session

    async def list_sessions(
        self, *, app_name: str, user_id: str | None = None
    ) -> ListSessionsResponse:
        """Lists all the sessions for a user.

        Args:
            app_name: The name of the app.
            user_id: The ID of the user. If not provided,
                lists all sessions for all users.

        Returns:
            A ListSessionsResponse containing the sessions.
        """
        query = {"app_name": app_name}
        if user_id is not None:
            query["user_id"] = user_id

        sessions_without_events: list[Session] = []
        cursor = self.sessions.find(query)

        async for doc in cursor:
            session = Session(
                app_name=doc["app_name"],
                user_id=doc["user_id"],
                id=doc["session_id"],
                state=doc["state"],
                last_update_time=doc["last_update_time"],
            )
            # No need to add events as list_sessions returns sessions without events
            session = await self._merge_state(doc["app_name"], doc["user_id"], session)
            sessions_without_events.append(session)

        return ListSessionsResponse(sessions=sessions_without_events)

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Deletes a session."""
        await self.sessions.delete_one({"_id": f"{app_name}:{user_id}:{session_id}"})

    async def append_event(self, session: Session, event: Event) -> Event:
        """Appends an event to a session."""
        if event.partial:
            return event

        app_name = session.app_name
        user_id = session.user_id
        session_id = session.id

        # Check if session exists
        doc = await self.sessions.find_one(
            {"_id": f"{app_name}:{user_id}:{session_id}"}
        )
        if not doc:
            return event

        # Update the in-memory session
        await super().append_event(session=session, event=event)
        session.last_update_time = event.timestamp

        # Prepare event data for storage
        event_dict = self._serialize_event(event)

        # Update storage with event and state delta
        update_doc: dict[str, Any] = {
            "$push": {"events": event_dict},
            "$set": {"last_update_time": event.timestamp},
        }

        # Handle state deltas
        if event.actions and event.actions.state_delta:
            state_deltas = _session_util.extract_state_delta(event.actions.state_delta)
            app_state_delta = state_deltas["app"]
            user_state_delta = state_deltas["user"]
            session_state_delta = state_deltas["session"]

            # Update app state
            if app_state_delta:
                await self.app_state.update_one(
                    {"_id": app_name}, {"$set": app_state_delta}, upsert=True
                )

            # Update user state
            if user_state_delta:
                await self.user_state.update_one(
                    {"_id": f"{app_name}:{user_id}"},
                    {"$set": user_state_delta},
                    upsert=True,
                )

            # Update session state
            if session_state_delta:
                state_updates = {
                    f"state.{key}": value for key, value in session_state_delta.items()
                }
                update_doc["$set"].update(state_updates)

        # Update the session document
        await self.sessions.update_one(
            {"_id": f"{app_name}:{user_id}:{session_id}"}, update_doc
        )

        return event
