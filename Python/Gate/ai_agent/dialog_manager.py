"""Dialog manager module.

Responsible for managing multi-turn dialogue context and maintaining session history.
"""

import json
import logging
import threading
import time
import uuid
from collections import deque
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DialogManager:
    """Dialog manager, maintains multi-turn dialogue context and history.

    Attributes:
        max_context_turns: Maximum number of dialogue turns to keep
        session_timeout: Session timeout (seconds)
        sessions: Session dictionary {session_id: {"history": deque, "last_active": timestamp}}
    """

    def __init__(self, max_context_turns: int = 5, session_timeout: int = 3600) -> None:
        """Initialize dialog manager.

        Args:
            max_context_turns: Maximum number of dialogue turns to keep, default 5
            session_timeout: Session timeout (seconds), default 1 hour
        """
        self.max_context_turns = max_context_turns
        self.session_timeout = session_timeout
        self._lock = threading.Lock()
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create new session.

        Args:
            user_id: User identifier, optional

        Returns:
            session_id: New session ID
        """
        session_id = str(uuid.uuid4())
        with self._lock:
            self.sessions[session_id] = {
                "user_id": user_id,
                "history": deque(maxlen=self.max_context_turns),
                "last_active": time.time(),
            }
        logger.info("Created new session: %s (user: %s)", session_id, user_id)
        return session_id

    def add_message(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        context_before: Optional[Dict] = None,
        context_after: Optional[Dict] = None,
    ) -> bool:
        """Add a dialogue turn to session history.

        Args:
            session_id: Session ID
            user_input: User input
            agent_response: Agent response
            context_before: Context before execution, optional
            context_after: Context after execution, optional

        Returns:
            bool: Whether addition was successful
        """
        with self._lock:
            if session_id not in self.sessions:
                logger.warning("Session does not exist: %s", session_id)
                return False

            session = self.sessions[session_id]
            session["history"].append(
                {
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "context_before": context_before,
                    "context_after": context_after,
                    "timestamp": time.time(),
                }
            )
            session["last_active"] = time.time()
            logger.debug("Session %s added dialogue turn: %s", session_id, user_input[:50])
            return True

    def get_context(self, session_id: str) -> List[Dict]:
        """Get session context history.

        Args:
            session_id: Session ID

        Returns:
            List[Dict]: Dialogue history list
        """
        with self._lock:
            if session_id not in self.sessions:
                logger.warning("Session does not exist: %s", session_id)
                return []

            session = self.sessions[session_id]
            return list(session["history"])

    def get_context_string(self, session_id: str) -> str:
        """Get string representation of session context for LLM prompts.

        Args:
            session_id: Session ID

        Returns:
            str: Formatted dialogue history string
        """
        history = self.get_context(session_id)
        if not history:
            return "No dialogue history"

        context_parts = []
        for i, turn in enumerate(history, 1):
            context_parts.append(f"Round {i}:")
            context_parts.append(f"User: {turn['user_input']}")
            context_parts.append(f"Assistant: {turn['agent_response']}")
            context_parts.append("")

        return "\n".join(context_parts)

    def clear_session(self, session_id: str) -> bool:
        """Clear specified session history.

        Args:
            session_id: Session ID

        Returns:
            bool: Whether clear was successful
        """
        with self._lock:
            if session_id not in self.sessions:
                return False

            self.sessions[session_id]["history"].clear()
            self.sessions[session_id]["last_active"] = time.time()
            logger.info("Cleared session history: %s", session_id)
            return True

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            int: Number of cleaned up sessions
        """
        current_time = time.time()
        expired_sessions = []

        with self._lock:
            for session_id, session in self.sessions.items():
                if current_time - session["last_active"] > self.session_timeout:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]

        if expired_sessions:
            logger.info("Cleaned expired sessions: %d", len(expired_sessions))

        return len(expired_sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information.

        Args:
            session_id: Session ID

        Returns:
            Optional[Dict]: Session information dictionary, returns None if not exists
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                return {
                    "user_id": session["user_id"],
                    "last_active": session["last_active"],
                    "turn_count": len(session["history"]),
                }
            return None
