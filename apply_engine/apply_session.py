"""
apply_engine/apply_session.py

Session state machine for a single job application attempt.
Each session has an ID and progresses through well-defined states.
The session is designed to be run inside an asyncio task.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

from apply_history import AppStatus, create_attempt, update_status


@dataclass
class ApplySession:
    session_id: str
    job_id: str
    company: str
    role: str
    apply_url: str

    # State
    status: str = AppStatus.PENDING
    progress_message: str = "Ready to start"
    error: Optional[str] = None
    confirmation_token: Optional[str] = None
    attempt_db_id: Optional[int] = None

    # Sync event: set when user confirms submission
    _confirm_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    # Sync event: set when user aborts
    _abort_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    # Sync event: set when user manually resumes after CAPTCHA or custom answer
    _resume_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "job_id": self.job_id,
            "company": self.company,
            "role": self.role,
            "apply_url": self.apply_url,
            "status": self.status,
            "progress_message": self.progress_message,
            "error": self.error,
            "confirmation_token": self.confirmation_token,
            "attempt_db_id": self.attempt_db_id,
            "created_at": self.created_at,
        }

    def set_status(self, status: str, message: str, error: str = None,
                   confirmation: str = None):
        self.status = status
        self.progress_message = message
        if error:
            self.error = error
        if confirmation:
            self.confirmation_token = confirmation
        # Persist to DB
        if self.attempt_db_id:
            update_status(
                self.attempt_db_id,
                status=status,
                last_action=message,
                error=error,
                confirmation=confirmation
            )

    def confirm(self):
        """Called when user clicks 'Confirm Submission'."""
        self._confirm_event.set()

    def abort(self):
        """Called when user clicks 'Abort'."""
        self._abort_event.set()

    def resume(self):
        """Called when user solves verification or provides answer."""
        self._resume_event.set()

    async def wait_for_user_decision(self, timeout_seconds: int = 300) -> str:
        """
        Block until user confirms or aborts, or timeout.
        Returns 'confirmed', 'aborted', or 'timeout'.
        """
        done, pending = await asyncio.wait(
            [
                asyncio.ensure_future(self._confirm_event.wait()),
                asyncio.ensure_future(self._abort_event.wait()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout_seconds,
        )
        for task in pending:
            task.cancel()

        if not done:
            return "timeout"
        if self._confirm_event.is_set():
            return "confirmed"
        return "aborted"


# Global registry of active sessions
_sessions: dict[str, ApplySession] = {}


def create_session(job_id: str, company: str, role: str, apply_url: str) -> ApplySession:
    sid = str(uuid.uuid4())
    session = ApplySession(
        session_id=sid,
        job_id=str(job_id),
        company=company,
        role=role,
        apply_url=apply_url,
    )
    _sessions[sid] = session
    # Register in DB
    db_id = create_attempt(job_id=str(job_id), company=company,
                            role=role, apply_url=apply_url)
    session.attempt_db_id = db_id
    return session


def get_session(session_id: str) -> Optional[ApplySession]:
    return _sessions.get(session_id)


def remove_session(session_id: str):
    _sessions.pop(session_id, None)

