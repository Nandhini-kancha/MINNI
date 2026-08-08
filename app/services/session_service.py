import uuid
from typing import Dict, List, Any
from datetime import datetime, timezone


class SessionService:
    """In-memory session manager for storing chat history per session_id."""

    def __init__(self, max_history_turns: int = 5):
        self._sessions: Dict[str, List[Dict[str, str]]] = {}
        self._last_accessed: Dict[str, datetime] = {}
        self.max_history_turns = max_history_turns  # Stores up to N user-model turns (2*N messages)

    def get_or_create_session_id(self, session_id: str | None = None) -> str:
        """Return existing session_id or generate a new unique session UUID."""
        if session_id and session_id.strip():
            sid = session_id.strip()
        else:
            sid = f"session-{uuid.uuid4().hex[:12]}"
        
        if sid not in self._sessions:
            self._sessions[sid] = []
        
        self._last_accessed[sid] = datetime.now(timezone.utc)
        return sid

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve recent conversation history for a given session_id."""
        return self._sessions.get(session_id, [])

    def add_turn(self, session_id: str, user_message: str, model_response: str) -> None:
        """Append a user message and model response to session history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        self._sessions[session_id].append({"role": "user", "content": user_message})
        self._sessions[session_id].append({"role": "model", "content": model_response})
        
        # Keep only recent turns to prevent context blowup
        max_messages = self.max_history_turns * 2
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]
            
        self._last_accessed[session_id] = datetime.now(timezone.utc)

    def clear_session(self, session_id: str) -> bool:
        """Remove a session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._last_accessed.pop(session_id, None)
            return True
        return False


# Global instance
session_service = SessionService()
