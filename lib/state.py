"""File-based JSON state management for Forge Protocol sessions."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

_SESSION_ID_RE = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')


@dataclass
class ModeEntry:
    mode: str
    entered_at: float
    exited_at: float | None = None
    message_count: int = 0


@dataclass
class Violation:
    timestamp: float
    mode: str
    violation_type: str  # "input" or "output"
    rule_id: str
    message: str


@dataclass
class AuditStatus:
    last_canary: float | None = None
    last_stress_test: float | None = None
    last_dependency_audit: float | None = None


@dataclass
class Session:
    session_id: str
    current_mode: str = "executor"
    mode_history: list[ModeEntry] = field(default_factory=list)
    message_count: int = 0
    last_checkpoint_at: int = 0
    violations: list[Violation] = field(default_factory=list)
    audit_status: AuditStatus = field(default_factory=AuditStatus)
    created_at: float = 0.0
    updated_at: float = 0.0


def _default_state_dir() -> Path:
    """Resolve the state directory: env var > ~/.forge-state/"""
    env_dir = os.environ.get("FORGE_STATE_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    return Path.home() / ".forge-state"


class StateManager:
    """Manages session state as JSON files on disk."""

    def __init__(self, state_dir: str | Path | None = None):
        self.state_dir = Path(state_dir).expanduser() if state_dir else _default_state_dir()
        self.sessions_dir = self.state_dir / "sessions"
        self.audit_dir = self.state_dir / "audit"
        self._dirs_ready = False

    def _ensure_dirs(self) -> None:
        if self._dirs_ready:
            return
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._dirs_ready = True

    def _session_path(self, session_id: str) -> Path:
        if not _SESSION_ID_RE.match(session_id):
            raise ValueError(f"Invalid session_id: {session_id!r}")
        path = (self.sessions_dir / f"{session_id}.json").resolve()
        if not str(path).startswith(str(self.sessions_dir.resolve())):
            raise ValueError(f"session_id escapes state directory: {session_id!r}")
        return path

    def create_session(self, session_id: str | None = None, initial_mode: str = "executor") -> Session:
        """Create a new session with a unique ID."""
        self._ensure_dirs()
        sid = session_id or str(uuid.uuid4())
        now = time.time()
        session = Session(
            session_id=sid,
            current_mode=initial_mode,
            mode_history=[ModeEntry(mode=initial_mode, entered_at=now)],
            created_at=now,
            updated_at=now,
        )
        self._write_session(session)
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Load a session from disk. Returns None if not found."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return self._deserialize(data)

    def get_or_create_session(self, session_id: str, initial_mode: str = "executor") -> Session:
        """Get an existing session or create a new one."""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, initial_mode)
        return session

    def _require_session(self, session_id: str) -> Session:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        return session

    def switch_mode(self, session_id: str, new_mode: str) -> Session:
        """Switch the current mode for a session."""
        session = self._require_session(session_id)

        if session.current_mode == new_mode:
            return session

        now = time.time()

        if session.mode_history:
            session.mode_history[-1].exited_at = now
            session.mode_history[-1].message_count = (
                session.message_count - sum(e.message_count for e in session.mode_history[:-1])
            )

        session.mode_history.append(ModeEntry(mode=new_mode, entered_at=now))
        session.current_mode = new_mode
        session.last_checkpoint_at = session.message_count
        session.updated_at = now

        self._write_session(session)
        return session

    def increment_messages(self, session_id: str) -> int:
        """Increment message count, return new count."""
        session = self._require_session(session_id)
        session.message_count += 1
        session.updated_at = time.time()
        self._write_session(session)
        return session.message_count

    def log_violation(self, session_id: str, mode: str, violation_type: str, rule_id: str, message: str) -> None:
        """Record an enforcement violation."""
        session = self._require_session(session_id)
        session.violations.append(
            Violation(
                timestamp=time.time(),
                mode=mode,
                violation_type=violation_type,
                rule_id=rule_id,
                message=message,
            )
        )
        session.updated_at = time.time()
        self._write_session(session)

    def update_checkpoint(self, session_id: str) -> None:
        """Mark that a metacognitive checkpoint was delivered."""
        session = self._require_session(session_id)
        session.last_checkpoint_at = session.message_count
        session.updated_at = time.time()
        self._write_session(session)

    def update_audit(self, session_id: str, audit_type: str) -> None:
        """Record that an audit was completed."""
        session = self._require_session(session_id)

        now = time.time()
        if audit_type == "canary":
            session.audit_status.last_canary = now
        elif audit_type == "stress_test":
            session.audit_status.last_stress_test = now
        elif audit_type == "dependency":
            session.audit_status.last_dependency_audit = now

        session.updated_at = now
        self._write_session(session)

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        self._ensure_dirs()
        return [p.stem for p in self.sessions_dir.glob("*.json")]

    def _write_session(self, session: Session) -> None:
        self._ensure_dirs()
        path = self._session_path(session.session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._serialize(session), f, indent=2)

    def _serialize(self, session: Session) -> dict:
        return {
            "session_id": session.session_id,
            "current_mode": session.current_mode,
            "mode_history": [
                {
                    "mode": e.mode,
                    "entered_at": e.entered_at,
                    "exited_at": e.exited_at,
                    "message_count": e.message_count,
                }
                for e in session.mode_history
            ],
            "message_count": session.message_count,
            "last_checkpoint_at": session.last_checkpoint_at,
            "violations": [
                {
                    "timestamp": v.timestamp,
                    "mode": v.mode,
                    "violation_type": v.violation_type,
                    "rule_id": v.rule_id,
                    "message": v.message,
                }
                for v in session.violations
            ],
            "audit_status": {
                "last_canary": session.audit_status.last_canary,
                "last_stress_test": session.audit_status.last_stress_test,
                "last_dependency_audit": session.audit_status.last_dependency_audit,
            },
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    def _deserialize(self, data: dict) -> Session:
        audit_raw = data.get("audit_status", {})
        return Session(
            session_id=data["session_id"],
            current_mode=data.get("current_mode", "executor"),
            mode_history=[
                ModeEntry(
                    mode=e["mode"],
                    entered_at=e["entered_at"],
                    exited_at=e.get("exited_at"),
                    message_count=e.get("message_count", 0),
                )
                for e in data.get("mode_history", [])
            ],
            message_count=data.get("message_count", 0),
            last_checkpoint_at=data.get("last_checkpoint_at", 0),
            violations=[
                Violation(
                    timestamp=v["timestamp"],
                    mode=v["mode"],
                    violation_type=v["violation_type"],
                    rule_id=v["rule_id"],
                    message=v["message"],
                )
                for v in data.get("violations", [])
            ],
            audit_status=AuditStatus(
                last_canary=audit_raw.get("last_canary"),
                last_stress_test=audit_raw.get("last_stress_test"),
                last_dependency_audit=audit_raw.get("last_dependency_audit"),
            ),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
        )
