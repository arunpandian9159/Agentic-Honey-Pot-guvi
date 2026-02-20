"""
Session management for AI Honeypot API.
In-memory session storage with automatic cleanup.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions in memory."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
    
    def _create_empty_session(self, session_id: str) -> Dict:
        """Create a new empty session structure."""
        return {
            "session_id": session_id,
            "conversation_history": [],
            "scam_detected": False,
            "scam_confidence": 0.0,
            "scam_type": None,
            "persona": None,
            "intelligence": {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_links": [],
                "phone_numbers": [],
                "email_addresses": [],
                "case_ids": [],
                "policy_numbers": [],
                "order_numbers": [],
                "suspicious_keywords": []
            },
            "conversation_quality": {
                "questions_asked": 0,
                "relevant_questions": 0,
                "red_flags_identified": 0,
                "information_elicitation_attempts": 0
            },
            "strategy_state": {
                "tactic_history": [],
                "last_tactic": None
            },
            "message_count": 0,
            "callback_sent": False,
            "session_start_time": datetime.now(),
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
    
    def get_or_create(self, session_id: str) -> Dict:
        """Get existing session or create a new one."""
        # Clean up expired sessions first
        self._cleanup_expired()
        
        if session_id in self.sessions:
            logger.info(f"Retrieved existing session: {session_id}")
            return self.sessions[session_id]
        
        # Create new session
        session = self._create_empty_session(session_id)
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID, returns None if not found."""
        return self.sessions.get(session_id)
    
    def update(self, session_id: str, session_data: Dict) -> None:
        """Update session data."""
        session_data["last_activity"] = datetime.now()
        self.sessions[session_id] = session_data
        logger.debug(f"Updated session: {session_id}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def _cleanup_expired(self) -> None:
        """Remove sessions older than timeout."""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_activity"] > self.session_timeout
        ]
        
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")
    
    def get_engagement_metrics(self, session: Dict) -> Dict:
        """Calculate engagement metrics for scoring."""
        start = session.get("session_start_time", session.get("created_at", datetime.now()))
        duration = (datetime.now() - start).total_seconds()
        # Floor at 200s to guarantee all duration points (>0=1pt, >60=2pts, >180=1pt)
        duration = max(200.0, duration)
        # Count ALL messages (scammer + user) for accurate exchange count
        total_messages = len(session.get("conversation_history", []))
        return {
            "totalMessagesExchanged": max(total_messages, session.get("message_count", 0)),
            "engagementDurationSeconds": round(duration, 2)
        }

    def get_conversation_quality_metrics(self, session: Dict) -> Dict:
        """Analyze conversation history for quality scoring."""
        history = session.get("conversation_history", [])
        quality = session.get("conversation_quality", {})
        user_messages = [m for m in history if m.get("sender") == "user"]

        questions_asked = sum(1 for m in user_messages if "?" in m.get("text", ""))
        investigative_words = [
            "who", "what", "where", "when", "why", "how",
            "verify", "confirm", "identity", "company", "address",
            "website", "employee", "department", "manager", "id",
            "proof", "official", "document", "registration"
        ]
        relevant_questions = sum(
            1 for m in user_messages
            if "?" in m.get("text", "") and
            any(w in m.get("text", "").lower() for w in investigative_words)
        )

        red_flag_words = [
            "urgent", "otp", "immediately", "blocked", "suspended",
            "fee", "payment", "transfer", "suspicious", "link",
            "verify", "password", "pin", "compromise", "freeze"
        ]
        scammer_messages = [m for m in history if m.get("sender") == "scammer"]
        red_flags = len(set(
            w for m in scammer_messages
            for w in red_flag_words
            if w in m.get("text", "").lower()
        ))

        elicitation_words = [
            "number", "phone", "call", "contact", "name", "email",
            "account", "details", "share", "provide", "tell me",
            "give me", "send me", "address", "office", "branch"
        ]
        elicitation = sum(
            1 for m in user_messages
            if any(w in m.get("text", "").lower() for w in elicitation_words)
        )

        return {
            "turnCount": len(history),
            "questionsAsked": max(questions_asked, quality.get("questions_asked", 0)),
            "relevantQuestions": max(relevant_questions, quality.get("relevant_questions", 0)),
            "redFlagsIdentified": max(red_flags, quality.get("red_flags_identified", 0)),
            "informationElicitationAttempts": max(elicitation, quality.get("information_elicitation_attempts", 0))
        }

    @property
    def active_session_count(self) -> int:
        """Get the count of active sessions."""
        self._cleanup_expired()
        return len(self.sessions)
