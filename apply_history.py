"""
apply_history.py
SQLite-backed persistent store for all job application attempts.
Records every action, status change, and error for auditability.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

_DB_PATH = Path(__file__).parent / "apply_history.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT    NOT NULL,
    company         TEXT    NOT NULL,
    role            TEXT    NOT NULL,
    apply_url       TEXT,
    attempted_at    TEXT    NOT NULL,
    completed_at    TEXT,
    status          TEXT    NOT NULL DEFAULT 'Pending',
    confirmation    TEXT,
    error_details   TEXT,
    last_action     TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_status  ON applications(status);
"""

# Valid status values
class AppStatus:
    PENDING       = "Pending"
    OPENING       = "Opening application"
    DETECTING     = "Detecting form"
    FILLING       = "Filling details"
    UPLOADING     = "Resume uploaded"
    WAITING       = "Waiting for review"
    SUBMITTED     = "Submitted successfully"
    MANUAL_NEEDED = "Needs manual action"
    FAILED        = "Failed"
    ABORTED       = "Aborted by user"
    DUPLICATE     = "Duplicate — already applied"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.executescript(_CREATE_TABLE_SQL)
    print(f"[apply_history] DB initialised at {_DB_PATH}")


def create_attempt(job_id: str, company: str, role: str, apply_url: str) -> int:
    """Insert a new application attempt. Returns the row id."""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO applications
               (job_id, company, role, apply_url, attempted_at, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(job_id), company, role, apply_url, now, AppStatus.PENDING)
        )
        return cur.lastrowid


def update_status(attempt_id: int, status: str,
                  last_action: str = None, error: str = None,
                  confirmation: str = None):
    """Update status of an existing attempt."""
    now = datetime.now(timezone.utc).isoformat()
    fields = ["status = ?", "last_action = ?"]
    values = [status, last_action or status]

    if error is not None:
        fields.append("error_details = ?")
        values.append(error)
    if confirmation is not None:
        fields.append("confirmation = ?")
        values.append(confirmation)
    if status in (AppStatus.SUBMITTED, AppStatus.FAILED,
                  AppStatus.ABORTED, AppStatus.MANUAL_NEEDED):
        fields.append("completed_at = ?")
        values.append(now)

    values.append(attempt_id)
    sql = f"UPDATE applications SET {', '.join(fields)} WHERE id = ?"
    with _get_conn() as conn:
        conn.execute(sql, values)


def get_attempt(attempt_id: int) -> Optional[Dict]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (attempt_id,)
        ).fetchone()
    return dict(row) if row else None


def get_history(limit: int = 200) -> List[Dict]:
    """Return recent application history."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY attempted_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def has_applied_before(job_id: str) -> Optional[Dict]:
    """Check if a job was already successfully applied to. Returns the record or None."""
    with _get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM applications
               WHERE job_id = ? AND status = ?
               ORDER BY attempted_at DESC LIMIT 1""",
            (str(job_id), AppStatus.SUBMITTED)
        ).fetchone()
    return dict(row) if row else None


def export_history_excel(output_path: str):
    """Export application history to Excel."""
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required for Excel export. Run: pip install openpyxl")

    rows = get_history(limit=10000)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Application History"

    headers = ["ID", "Job ID", "Company", "Role", "Apply URL",
               "Attempted At", "Completed At", "Status",
               "Confirmation", "Error Details", "Last Action", "Notes"]
    ws.append(headers)

    for r in rows:
        ws.append([
            r.get("id"), r.get("job_id"), r.get("company"), r.get("role"),
            r.get("apply_url"), r.get("attempted_at"), r.get("completed_at"),
            r.get("status"), r.get("confirmation"), r.get("error_details"),
            r.get("last_action"), r.get("notes")
        ])

    # Auto-width columns
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    wb.save(output_path)
    return output_path


def get_tracker_summary() -> Dict[str, Any]:
    """Return an executive statistical summary of all tracked applications."""
    with _get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM applications").fetchall()]

    total = len(rows)
    by_status = {}
    for r in rows:
        st = r.get("status", "Pending")
        by_status[st] = by_status.get(st, 0) + 1

    submitted = by_status.get(AppStatus.SUBMITTED, 0)
    interviewing = by_status.get("Interviewing", 0)
    offers = by_status.get("Offer", 0)
    rejected = by_status.get("Rejected", 0)

    # Response rate: (interviewing + offers + rejected) / submitted
    response_rate = round(((interviewing + offers + rejected) / submitted * 100), 1) if submitted > 0 else 0.0

    return {
        "total_applications": total,
        "submitted": submitted,
        "interviewing": interviewing,
        "offers": offers,
        "rejected": rejected,
        "response_rate_percent": response_rate,
        "breakdown": by_status,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


def update_application_status(job_id_or_id: Any, status: str, notes: Optional[str] = None) -> bool:
    """Convenient helper to update status and notes by row id or job_id."""
    with _get_conn() as conn:
        # Check if integer ID
        if isinstance(job_id_or_id, int) or (isinstance(job_id_or_id, str) and job_id_or_id.isdigit()):
            conn.execute(
                "UPDATE applications SET status = ?, notes = COALESCE(?, notes), last_action = ? WHERE id = ?",
                (status, notes, f"Manual update to {status}", int(job_id_or_id))
            )
            return True
        else:
            conn.execute(
                "UPDATE applications SET status = ?, notes = COALESCE(?, notes), last_action = ? WHERE job_id = ?",
                (status, notes, f"Manual update to {status}", str(job_id_or_id))
            )
            return True


def get_applications_by_status(status: str) -> List[Dict[str, Any]]:
    """Return applications matching a specific status."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY attempted_at DESC",
            (status,)
        ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print("History DB ready.")

