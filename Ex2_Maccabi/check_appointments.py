from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import subprocess
from datetime import datetime

#APPOINTMENTS_URL = "https://online.maccabi4u.co.il/sonline/appointmentOrder/NewAppointment/Filter/"  # אחר כך נחליף לעמוד התורים האמיתי

#APPOINTMENTS_URL = "https://online.maccabi4u.co.il/serguide/heb/home/?SearchText=%D7%A4%D7%95%D7%93%D7%99%D7%90%D7%98%D7%A8%2F%D7%A4%D7%95%D7%93%D7%95%D7%9C%D7%95%D7%92%2F%D7%9B%D7%99%D7%A8%D7%95%D7%A4%D7%95%D7%93&Source=Home/"
APPOINTMENTS_URL = "https://online.maccabi4u.co.il/serguide/heb/labsandtherapists/labsandtherapistssearchresults/?PageNumber=1&RequestId=0522411c-2bcb-cb47-11f2-aa59d5da397e&SearchText=%D7%A4%D7%95%D7%93%D7%99%D7%90%D7%98%D7%A8%2F%D7%A4%D7%95%D7%93%D7%95%D7%9C%D7%95%D7%92%2F%D7%9B%D7%99%D7%A8%D7%95%D7%A4%D7%95%D7%93&Source=Home"

STATE_PATH = Path(__file__).parent / "state" / "maccabi_state.json"
LOGIN_SCRIPT = Path(__file__).parent / "python save_login.py"


def is_session_expired() -> bool:
    if not STATE_PATH.exists():
        return True
    state = json.loads(STATE_PATH.read_text())
    auth_cookies = [
        c for c in state.get("cookies", [])
        if "sessionId" in c.get("name", "") or "currentCustomer" in c.get("name", "")
    ]
    if not auth_cookies:
        return True
    return all(
        c.get("expires", -1) != -1 and datetime.fromtimestamp(c["expires"]) < datetime.now()
        for c in auth_cookies
    )


if is_session_expired():
    print("Session expired. Launching login flow...")
    result = subprocess.run(["python", str(LOGIN_SCRIPT)])
    if result.returncode != 0:
        print("Login failed or was cancelled. Exiting.")
        exit(1)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context(storage_state=str(STATE_PATH))
    page = context.new_page()

    page.goto(APPOINTMENTS_URL, wait_until="networkidle")

    print(page.locator("body").inner_text()[:3000])

    input("לחץ Enter כדי לסגור את הדפדפן...")
    browser.close()