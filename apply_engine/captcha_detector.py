"""
apply_engine/captcha_detector.py

Real-time Security Challenge, CAPTCHA, and OTP Detector.

Ethical & Safe Automation Rules:
- NEVER attempts to bypass, solve programmatically, or tamper with website security.
- Intelligently detects challenges (Cloudflare, reCAPTCHA, hCaptcha, Arkose, OTP, 2FA).
- Pauses automated actions immediately and notifies the user.
- Monitors the page until the human completes verification, then automatically resumes.
"""

import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import Page
from apply_history import AppStatus


# Challenge signatures across platforms
CHALLENGE_SELECTORS = [
    # Google reCAPTCHA
    {"name": "reCAPTCHA", "selector": "iframe[src*='recaptcha'], .g-recaptcha, [data-sitekey]", "type": "CAPTCHA"},
    
    # Cloudflare Turnstile / Bot Check
    {"name": "Cloudflare Turnstile", "selector": "#challenge-running, #cf-challenge, iframe[src*='turnstile'], .cf-turnstile", "type": "CLOUDFLARE"},
    {"name": "Cloudflare Verification", "selector": "text='Verify you are human', text='Checking your browser'", "type": "CLOUDFLARE"},

    # hCaptcha
    {"name": "hCaptcha", "selector": "iframe[src*='hcaptcha'], .h-captcha", "type": "CAPTCHA"},

    # Arkose Labs / LinkedIn Checkpoint / Funcaptcha
    {"name": "LinkedIn Security Checkpoint", "selector": "iframe[src*='arkoselabs'], iframe[src*='funcaptcha'], .challenge-dialog, [data-test-id='checkpoint']", "type": "SECURITY_CHECK"},
    {"name": "LinkedIn Verification", "selector": "text='Quick security check', text='Let\\'s do a quick security check'", "type": "SECURITY_CHECK"},

    # OTP / 2FA / Verification code
    {"name": "OTP Verification", "selector": "input[name*='otp' i], input[id*='otp' i], input[autocomplete='one-time-code']", "type": "OTP"},
    {"name": "Verification Code", "selector": "input[placeholder*='code' i], input[name*='pin' i], input[name*='verification' i]", "type": "OTP"},
    {"name": "Two-Factor Auth", "selector": "text='Enter verification code', text='Enter the code sent', text='Two-factor authentication'", "type": "OTP"},
]


class CaptchaDetector:
    """Detects CAPTCHA, OTP, and anti-bot verification challenges."""

    def __init__(self, page: Page, session: Any):
        self.page = page
        self.session = session
        self.is_paused = False

    async def check_challenge(self) -> Optional[Dict[str, str]]:
        """
        Inspect current page DOM for any active CAPTCHA, OTP, or security blocker.
        Returns challenge info dict if detected, or None.
        """
        for challenge in CHALLENGE_SELECTORS:
            try:
                el = await self.page.query_selector(challenge["selector"])
                if el and await el.is_visible():
                    return {
                        "name": challenge["name"],
                        "type": challenge["type"],
                        "selector": challenge["selector"]
                    }
            except Exception:
                continue

        # Also inspect page title and text for obvious security barriers
        try:
            page_text = await self.page.evaluate("() => document.body ? document.body.innerText.slice(0, 1500) : ''")
            if "enter the 6-digit code" in page_text.lower() or "enter the 4-digit code" in page_text.lower():
                return {"name": "SMS/Email OTP Code", "type": "OTP", "selector": "body"}
            if "verify your identity" in page_text.lower() or "suspicious activity" in page_text.lower():
                return {"name": "Identity Verification", "type": "SECURITY_CHECK", "selector": "body"}
        except Exception:
            pass

        return None

    async def handle_challenge_if_present(self, timeout_seconds: int = 300) -> bool:
        """
        Check for a security challenge. If present:
        1. Pauses automation.
        2. Notifies user via session status.
        3. Polls until user completes human verification in the browser window.
        4. Resumes automatically once challenge clears.
        Returns True if resolved, or False if timed out / aborted.
        """
        challenge = await self.check_challenge()
        if not challenge:
            return True

        self.is_paused = True
        name = challenge["name"]
        ctype = challenge["type"]

        if ctype == "OTP":
            user_msg = (
                f"🔑 {name} detected! An OTP/verification code was requested. "
                "Please enter the code directly in the open browser window. "
                "Automation is paused and will resume automatically once submitted."
            )
        elif ctype == "CAPTCHA" or ctype == "CLOUDFLARE":
            user_msg = (
                f"🔒 {name} detected! "
                "Please solve the verification in the open browser window. "
                "Automation is paused and will resume automatically once completed."
            )
        else:
            user_msg = (
                f"🛡️ {name} detected! "
                "Please complete the security check in the browser window. "
                "Automation will resume automatically."
            )

        print(f"[captcha_detector] {user_msg}")
        self.session.set_status(AppStatus.MANUAL_NEEDED, user_msg)

        # Wait for user resolution
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
            # Check if user aborted in session
            if getattr(self.session, "_abort_event", None) and self.session._abort_event.is_set():
                self.is_paused = False
                return False

            # Check if user clicked manual resume trigger
            if getattr(self.session, "_resume_event", None) and self.session._resume_event.is_set():
                self.session._resume_event.clear()
                self.is_paused = False
                self.session.set_status(AppStatus.FILLING, "Verification confirmed. Resuming automation…")
                return True

            # Check if challenge element has disappeared
            active_challenge = await self.check_challenge()
            if not active_challenge:
                # Challenge resolved by human!
                print(f"[captcha_detector] Challenge resolved! Resuming automated application.")
                self.session.set_status(
                    AppStatus.FILLING,
                    f"✅ {name} completed! Resuming automated application…"
                )
                self.is_paused = False
                await asyncio.sleep(1.5)  # Let page settle
                return True

            await asyncio.sleep(1.5)

        # Timeout occurred
        self.is_paused = False
        self.session.set_status(
            AppStatus.FAILED,
            f"Security verification timed out after {timeout_seconds}s. Application not submitted."
        )
        return False
