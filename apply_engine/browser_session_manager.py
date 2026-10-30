"""
apply_engine/browser_session_manager.py

Manages persistent, authenticated browser sessions for supported job portals:
- LinkedIn
- Naukri
- Indeed

Features:
- Stores session storage state (cookies, localStorage) in apply_engine/sessions/
- Provides connection status checking
- Guides secure interactive login (opens headed browser for user to log in)
- Never stores or logs raw passwords
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, BrowserContext, Page

BASE_DIR = Path(__file__).parent.parent
SESSIONS_DIR = BASE_DIR / "apply_engine" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_PLATFORMS = {
    "linkedin": {
        "name": "LinkedIn",
        "login_url": "https://www.linkedin.com/login",
        "home_url": "https://www.linkedin.com/feed/",
        "cookie_names": ["li_at", "JSESSIONID"],
        "auth_indicators": ["nav[aria-label*='Primary']", ".global-nav", "a[href*='/in/']"],
        "icon": "linkedin"
    },
    "naukri": {
        "name": "Naukri",
        "login_url": "https://www.naukri.com/nlogin/login",
        "home_url": "https://www.naukri.com/mnjuser/homepage",
        "cookie_names": ["nauk_sid", "nlogin"],
        "auth_indicators": [".nI-gNb-drawer__bars", "a[href*='my-profile']", ".user-name"],
        "icon": "naukri"
    },
    "indeed": {
        "name": "Indeed",
        "login_url": "https://secure.indeed.com/auth",
        "home_url": "https://www.indeed.com/",
        "cookie_names": ["SURF", "SHOE", "CTK"],
        "auth_indicators": ["button[aria-label*='Account']", "#gnav-account-button", "a[href*='myjobs']"],
        "icon": "indeed"
    }
}


class BrowserSessionManager:
    """Manages authenticated browser sessions and cookies for job portals."""

    def __init__(self, sessions_dir: Path = SESSIONS_DIR):
        self.sessions_dir = sessions_dir

    def get_state_file(self, platform: str) -> Path:
        """Return the storage state file path for the platform."""
        plat = platform.lower()
        return self.sessions_dir / f"{plat}_state.json"

    def has_session_file(self, platform: str) -> bool:
        """Check if a saved storage state file exists and has content."""
        f = self.get_state_file(platform)
        if f.exists() and f.stat().st_size > 50:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    # Check cookies list
                    return bool(data.get("cookies", []))
            except Exception:
                return False
        return False

    def get_account_status(self) -> Dict[str, Any]:
        """Return authentication status for all supported platforms."""
        status = {}
        for plat, config in SUPPORTED_PLATFORMS.items():
            has_file = self.has_session_file(plat)
            f = self.get_state_file(plat)
            last_updated = None
            if has_file and f.exists():
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                last_updated = mtime.strftime("%b %d, %Y %I:%M %p UTC")

            status[plat] = {
                "platform": plat,
                "name": config["name"],
                "connected": has_file,
                "last_updated": last_updated,
                "icon": config["icon"]
            }
        return status

    async def connect_account(self, platform: str, timeout_seconds: int = 180) -> Dict[str, Any]:
        """
        Open a headed browser window for the user to securely log in.
        Waits for successful login, saves cookies/storage state, and closes.
        """
        plat = platform.lower()
        if plat not in SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}. Supported: {list(SUPPORTED_PLATFORMS.keys())}")

        config = SUPPORTED_PLATFORMS[plat]
        state_file = self.get_state_file(plat)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
            # Use existing state if available to refresh or allow partial session
            context_kwargs = {"viewport": None, "accept_downloads": True}
            if state_file.exists() and state_file.stat().st_size > 50:
                try:
                    context_kwargs["storage_state"] = str(state_file)
                except Exception:
                    pass

            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()

            # Navigate to login page
            await page.goto(config["login_url"], wait_until="domcontentloaded")

            # Poll until authentication is detected
            logged_in = False
            start_time = asyncio.get_event_loop().time()

            while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
                # Check 1: Cookies
                cookies = await context.cookies()
                cookie_names = {c["name"] for c in cookies}
                has_key_cookie = any(kc in cookie_names for kc in config["cookie_names"])

                # Check 2: Indicators on page (home URL or logged-in nav elements)
                current_url = page.url.lower()
                is_on_home = any(h in current_url for h in ["feed", "homepage", "dashboard", "home", "myjobs"])

                has_indicator = False
                for sel in config["auth_indicators"]:
                    try:
                        el = await page.query_selector(sel)
                        if el and await el.is_visible():
                            has_indicator = True
                            break
                    except Exception:
                        pass

                if (has_key_cookie and is_on_home) or has_indicator:
                    logged_in = True
                    break

                await asyncio.sleep(2)

            if not logged_in:
                await browser.close()
                return {
                    "status": "failed",
                    "platform": plat,
                    "connected": False,
                    "message": f"Login timed out after {timeout_seconds} seconds. Please try again."
                }

            # Save state
            await context.storage_state(path=str(state_file))
            await browser.close()

            return {
                "status": "success",
                "platform": plat,
                "connected": True,
                "message": f"Successfully connected and saved session for {config['name']}!"
            }

    def disconnect_account(self, platform: str) -> bool:
        """Disconnect and delete saved session for platform."""
        f = self.get_state_file(platform)
        if f.exists():
            try:
                f.unlink()
                return True
            except Exception:
                return False
        return False

    async def get_authenticated_context(
        self,
        pw,
        platform: str,
        headless: bool = False
    ) -> BrowserContext:
        """
        Create a browser context with stored credentials if available.
        """
        plat = platform.lower()
        state_file = self.get_state_file(plat)

        browser = await pw.chromium.launch(
            headless=headless,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )

        context_kwargs = {
            "viewport": None,
            "accept_downloads": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        if state_file.exists() and state_file.stat().st_size > 50:
            try:
                context_kwargs["storage_state"] = str(state_file)
            except Exception as e:
                print(f"[browser_session] Failed to load {plat} state file: {e}")

        context = await browser.new_context(**context_kwargs)
        return context


# Global singleton
session_manager = BrowserSessionManager()
