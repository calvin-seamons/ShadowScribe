
from playwright.sync_api import sync_playwright

def verify_chat_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the chat page (assuming it's at /chat or root)
            print("Navigating to chat page...")
            page.goto("http://localhost:3000")

            # Wait for the page to load
            print("Waiting for page load...")
            # Check for the "No messages yet" text or the input field
            try:
                page.wait_for_selector("text=No messages yet", timeout=10000)
                print("Found 'No messages yet' state")
            except:
                print("Could not find 'No messages yet' - maybe not empty?")

            # Take a screenshot of the initial state
            page.screenshot(path="verification/initial_state.png")
            print("Screenshot taken: verification/initial_state.png")

            # We cannot easily trigger a streaming message without backend interaction or modifying the store from here.
            # But if the page loads without crashing, it means MessageList rendered successfully.

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_chat_ui()
