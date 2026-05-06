from playwright.sync_api import Playwright, sync_playwright
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

USER_ID = os.getenv("MACCABI_USER_ID")
PASSWORD = os.getenv("MACCABI_PASSWORD")
URL = os.getenv("MACCABI_URL")


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context()
    page = context.new_page()

    page.goto(URL)

    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="למכבי Online").click()

    page1 = page1_info.value
    page1.wait_for_load_state("networkidle")

    page1.get_by_role("textbox", name="מספר תעודת זהות").fill(USER_ID)
    page1.get_by_role("button", name="המשך").click()

    page1.locator("#chooseType").get_by_text("כניסה עם סיסמה").click()

    page1.get_by_role("textbox", name="מספר תעודת זהות").fill(USER_ID)
    page1.get_by_role("textbox", name="סיסמה").fill(PASSWORD)
    page1.get_by_role("button", name="המשך").click()

    # מחכה שתתחבר בפועל
    page1.wait_for_load_state("networkidle")

    #input("אם אתה רואה שאתה מחובר לאתר — לחץ Enter כדי לשמור session...")
    
    state_path = Path(__file__).parent / "state" / "maccabi_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(state_path))
    print ("state saved to:", state_path)

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)