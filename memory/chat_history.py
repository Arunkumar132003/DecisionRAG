import uuid

class ChatHistory:
    """Manages conversation history by session."""

    def __init__(self):
        self.sessions = {}

    def create_session(self) -> str:
        """Creates a new session."""

        session_id = uuid.uuid4().hex[:10]
        self.sessions[session_id] = []
        return session_id

    def add_user_message(self, session_id: str, message: str):
        """Stores user message."""

        self.sessions.setdefault(session_id, [])
        self.sessions[session_id].append(
            {
                "role": "user",
                "content": message
            }
        )

    def add_assistant_message(self, session_id: str, message: str):
        """Stores assistant message."""

        self.sessions.setdefault(session_id, [])
        self.sessions[session_id].append(
            {
                "role": "assistant",
                "content": message
            }
        )

    def get_history(self, session_id: str) -> list:
        """Returns conversation history."""

        return self.sessions.get(session_id, [])

    def format_history(self, session_id: str, limit: int = None) -> str:
        """Formats history for prompts, optionally capped to the last `limit` messages."""

        history = self.get_history(session_id)
        if not history:
            return ""

        if limit:
            history = history[-limit:]
        return "\n".join(
            f"{message['role'].upper()}: {message['content']}"
            for message in history
        )

    def clear_session(self, session_id: str):
        """Deletes a session."""
        self.sessions.pop(session_id, None)