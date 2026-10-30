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


def load_profile() -> dict:
    """Load and validate candidate profile. Returns dict."""
    if not _PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"profile_config.json not found at {_PROFILE_PATH}. "
            "Please create it by copying the template."
        )

    with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

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

