import random
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

INSTAGRAM_USERNAME = "kxnli_05"

WORDS = [
    "Woof",
    "Worf",
    "Bork",
    "food?",
    "snack?",
    "walk?",
    "sus",
    "zoomies",
    "where snack?",
    "am dog?",
    "very busy?",
    "car?",
    "ruff",
    "arf!",
    "I am a dog?",
    "doggy?",
    "bleh?",
]

BASE_DIR = Path(__file__).parent

PROFILE_DIR = BASE_DIR / "instagram_chrome_profile"

INSTAGRAM_LOGIN = "https://www.instagram.com/accounts/login/"
INSTAGRAM_DMS = "https://www.instagram.com/direct/inbox/"
INSTAGRAM_PROFILE = f"https://www.instagram.com/{INSTAGRAM_USERNAME}/"

HEADLESS = False
ACTUALLY_SHARE = True


def choose_note():
    return random.choice(WORDS)


def is_authenticated_url(url):
    url = url.lower()

    return (
        "instagram.com/direct/" in url
        and "/accounts/login" not in url
        and "/recaptcha" not in url
        and "/challenge" not in url
        and "/checkpoint" not in url
    )


def session_is_logged_in(page):
    print("Checking Instagram session...")

    page.goto(
        INSTAGRAM_DMS,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    page.wait_for_timeout(3000)

    print("Current URL:", page.url)

    return is_authenticated_url(page.url)


def ensure_logged_in(page):
    if session_is_logged_in(page):
        print("Instagram session verified.")
        return

    print()
    print("==================================================")
    print("INSTAGRAM LOGIN / VERIFICATION REQUIRED")
    print("==================================================")
    print()
    print("Complete whatever Instagram shows in Chrome:")
    print("- login")
    print("- CAPTCHA")
    print("- security verification")
    print("- trusted-device confirmation")
    print()
    print("Do this manually in the browser window.")
    print()
    print("The session will be stored in:")
    print(PROFILE_DIR)
    print()

    current_url = page.url.lower()

    verification_page = any(
        marker in current_url
        for marker in [
            "/recaptcha",
            "/challenge",
            "/checkpoint",
        ]
    )

    if not verification_page:
        page.goto(
            INSTAGRAM_LOGIN,
            wait_until="domcontentloaded",
            timeout=30_000,
        )

    input(
        "Once Instagram is fully logged in, press Enter here..."
    )

    print()
    print("Verifying Instagram login...")

    page.goto(
        INSTAGRAM_DMS,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    page.wait_for_timeout(3000)

    print("Verification URL:", page.url)

    if not is_authenticated_url(page.url):
        raise RuntimeError(
            "Instagram authentication could not be verified."
        )

    print("Instagram login verified successfully.")


def open_note_composer(page):
    print("Opening profile...")

    page.goto(
        INSTAGRAM_PROFILE,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    page.wait_for_timeout(4000)

    print("Finding Note bubble...")

    note_button = page.locator('[role="button"]').first

    note_button.wait_for(
        state="visible",
        timeout=10_000,
    )

    print(
        "Note bubble text:",
        repr(note_button.inner_text())
    )

    note_button.click()

    page.wait_for_timeout(1000)

    leave_new_note = page.get_by_text(
        "Leave a new note",
        exact=True,
    )

    try:
        if leave_new_note.is_visible(timeout=2000):
            print("Existing Note detected.")
            print("Clicking 'Leave a new note'...")

            leave_new_note.click()

            page.wait_for_timeout(750)

    except PlaywrightTimeoutError:
        pass

    print("Waiting for Note editor...")

    editor = page.locator(
        '[contenteditable="true"]'
        '[aria-label="Share a thought..."]'
    )

    editor.wait_for(
        state="visible",
        timeout=10_000,
    )

    print("Note editor found.")

    return editor


def post_note(page, note):
    print()
    print("==================================================")
    print("BUBBLES BOT")
    print("==================================================")
    print()
    print("Selected Note:", repr(note))
    print()

    editor = open_note_composer(page)

    print("Typing Note...")

    editor.click()
    page.keyboard.type(note)

    page.wait_for_timeout(500)

    print("Finding Share button...")

    dialog = page.locator('[role="dialog"]')

    dialog.wait_for(
        state="visible",
        timeout=10_000,
    )

    share_button = dialog.get_by_text(
        "Share",
        exact=True,
    )

    share_button.wait_for(
        state="visible",
        timeout=10_000,
    )

    print("Share button found.")

    if not ACTUALLY_SHARE:
        print()
        print("==================================================")
        print("TEST MODE")
        print("==================================================")
        print()
        print("Would post:", repr(note))
        print()
        print("Share was NOT clicked.")
        print()

        input("Press Enter to close Chrome...")

        return

    print("Posting Note...")

    share_button.click()

    page.wait_for_timeout(2500)

    print("Verifying Note...")

    page.goto(
        INSTAGRAM_PROFILE,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    page.wait_for_timeout(4000)

    note_button = page.locator('[role="button"]').first

    note_button.wait_for(
        state="visible",
        timeout=10_000,
    )

    try:
        displayed_note = note_button.inner_text(
            timeout=5000
        ).strip()

    except Exception:
        displayed_note = ""

    print(
        "Displayed Note after posting:",
        repr(displayed_note)
    )

    if displayed_note == note:
        print()
        print("==================================================")
        print("SUCCESS")
        print("==================================================")
        print()
        print(
            f"Instagram Note is now: {note!r}"
        )

    else:
        print()
        print("==================================================")
        print("WARNING")
        print("==================================================")
        print()
        print("Share was clicked, but verification did")
        print("not exactly match.")
        print()
        print("Expected:", repr(note))
        print("Found:   ", repr(displayed_note))


def main():
    note = choose_note()

    with sync_playwright() as p:
        print("Launching Chrome...")

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=HEADLESS,
            chromium_sandbox=True,
            viewport={
                "width": 1400,
                "height": 900,
            },
        )

        try:
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()

            ensure_logged_in(page)

            post_note(page, note)

        except PlaywrightTimeoutError as e:
            print()
            print("==================================================")
            print("PLAYWRIGHT TIMEOUT")
            print("==================================================")
            print()
            print(e)

            raise

        except Exception as e:
            print()
            print("==================================================")
            print("ERROR")
            print("==================================================")
            print()
            print(e)

            raise

        finally:
            print()
            print("Closing Chrome...")

            context.close()


if __name__ == "__main__":
    main()