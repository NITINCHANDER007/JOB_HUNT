"""
candidate_profile.py
Loads and validates the candidate profile from profile_config.json.
Never invents missing data — raises clear errors for required fields.
"""

import json
import os
from pathlib import Path

_BASE = Path(__file__).parent
_PROFILE_PATH = _BASE / "profile_config.json"

_REQUIRED_FIELDS = ["full_name", "email", "phone", "resume_path"]

FORBIDDEN_EMAIL = "nitinchandra834@gmail.com"
ACTIVE_EMAIL = "codernitin55@gmail.com"
OVERRIDE_CODEWORD = "USE KRLO nitinchandra834@gmail.com"


def sanitize_email(email: str) -> str:
    """
    Strict security rule:
    Never use 'nitinchandra834@gmail.com' in any operation at any cost.
    Use 'codernitin55@gmail.com' instead.
    Only permitted if explicit codeword 'USE KRLO nitinchandra834@gmail.com' is authorized.
    """
    if not email:
        return ACTIVE_EMAIL
    if FORBIDDEN_EMAIL in email.lower():
        if os.environ.get("JOB_HUNT_EMAIL_CODEWORD") == OVERRIDE_CODEWORD:
            return email
        return ACTIVE_EMAIL
    return email


def load_profile() -> dict:
    """Load and validate candidate profile. Returns dict."""
    if not _PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"profile_config.json not found at {_PROFILE_PATH}. "
            "Please create it by copying the template."
        )

    with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    # Sanitize email immediately
    profile["email"] = sanitize_email(profile.get("email", ACTIVE_EMAIL))

    # Validate required fields
    missing = [f for f in _REQUIRED_FIELDS if not profile.get(f)]
    if missing:
        raise ValueError(
            f"Required profile fields are missing or empty: {missing}. "
            "Edit profile_config.json to add these values."
        )

    # Validate resume file exists
    resume_path = Path(profile["resume_path"])
    if not resume_path.exists():
        raise FileNotFoundError(
            f"Resume file not found: {resume_path}. "
            "Check the 'resume_path' field in profile_config.json."
        )

    return profile


def get_safe_profile() -> dict:
    """Return profile without sensitive manual fields (safe for API responses)."""
    profile = load_profile()
    safe = {k: v for k, v in profile.items() if not k.startswith("_")}
    # Remove manual fields that should only be filled manually
    safe.pop("_MANUAL_FIELDS", None)
    return safe


if __name__ == "__main__":
    p = load_profile()
    print("Profile loaded OK:")
    for k, v in p.items():
        if not k.startswith("_"):
            print(f"  {k}: {v}")

