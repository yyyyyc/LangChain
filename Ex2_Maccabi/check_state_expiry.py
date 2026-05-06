import json
from datetime import datetime
from pathlib import Path

STATE_PATH = Path(__file__).parent / "state" / "maccabi_state.json"

if not STATE_PATH.exists():
    print("State file not found. Run save_login.py first.")
    exit(1)

state = json.loads(STATE_PATH.read_text())
cookies = state.get("cookies", [])

if not cookies:
    print("State file is empty or has no cookies. Run save_login.py first.")
    exit(1)

now = datetime.now()
print(f"Checked at: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
print(f"{'Cookie':<40} {'Expires':<25} {'Status'}")
print("-" * 80)

any_valid = False
for cookie in sorted(cookies, key=lambda c: c.get("expires", -1)):
    name = cookie.get("name", "?")
    expires = cookie.get("expires", -1)

    if expires == -1:
        status = "session (no expiry)"
        expires_str = "—"
    else:
        exp_dt = datetime.fromtimestamp(expires)
        expires_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
        if exp_dt < now:
            status = "EXPIRED"
        else:
            delta = exp_dt - now
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes = remainder // 60
            status = f"valid ({hours}h {minutes}m remaining)"
            any_valid = True

    print(f"{name:<40} {expires_str:<25} {status}")

print()
if any_valid:
    print("Session appears valid.")
else:
    print("All cookies are expired. Run save_login.py to refresh the session.")
