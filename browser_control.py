from urllib.parse import quote_plus

from playwright.sync_api import (
    sync_playwright,
    Error as PlaywrightError
)


playwright_instance = None
browser = None
context = None
active_page = None


# Browser Startup
def start_browser():

    global playwright_instance
    global browser
    global context
    global active_page

    if browser is not None:
        return get_page()

    playwright_instance = sync_playwright().start()

    browser = playwright_instance.chromium.launch(
        headless=False
    )

    context = browser.new_context()

    active_page = context.new_page()

    return active_page


# Current Page
def get_page():

    global active_page

    if browser is None:
        return start_browser()

    pages = [
        page
        for page in context.pages
        if not page.is_closed()
    ]

    if not pages:

        active_page = context.new_page()

    elif (
        active_page is None
        or active_page.is_closed()
    ):

        active_page = pages[-1]

    return active_page


# Normalize URL
def normalize_url(url):

    url = url.strip()

    if not url.startswith(
        (
            "http://",
            "https://"
        )
    ):

        url = "https://" + url

    return url


# Open URL
def open_url(url):

    page = get_page()

    url = normalize_url(
        url
    )

    try:

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.bring_to_front()

        title = page.title()

        if title:

            return f"Opened {title}."

        return "Website opened."

    except PlaywrightError as error:

        print(
            f"Browser open error: {error}"
        )

        return (
            "I couldn't open that website."
        )


# Browser Search
def browser_search(query):

    page = get_page()

    search_url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    try:

        page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.bring_to_front()

        return (
            f"I searched Google for {query}."
        )

    except PlaywrightError as error:

        print(
            f"Browser search error: {error}"
        )

        return (
            "I couldn't complete the browser search."
        )


# New Tab
def new_tab(url=None):

    global active_page

    start_browser()

    active_page = context.new_page()

    active_page.bring_to_front()

    if url:

        try:

            active_page.goto(
                normalize_url(url),
                wait_until="domcontentloaded",
                timeout=30000
            )

            return "Opened the website in a new tab."

        except PlaywrightError as error:

            print(
                f"New tab error: {error}"
            )

            return (
                "I opened a new tab, "
                "but couldn't load the website."
            )

    active_page.goto(
        "about:blank"
    )

    return "Opened a new tab."


# Close Tab
def close_tab():

    global active_page

    if browser is None:
        return "The browser is not open."

    pages = [
        page
        for page in context.pages
        if not page.is_closed()
    ]

    if not pages:
        return "There are no tabs open."

    page = get_page()

    try:

        page.close()

    except Exception as error:

        print(
            f"Close tab error: {error}"
        )

        return "I couldn't close the tab."

    remaining_pages = [
        item
        for item in context.pages
        if not item.is_closed()
    ]

    if remaining_pages:

        active_page = remaining_pages[-1]

        active_page.bring_to_front()

    else:

        active_page = context.new_page()

        active_page.bring_to_front()

    return "Closed the tab."


# Next Tab
def next_tab():

    global active_page

    if browser is None:
        return "The browser is not open."

    pages = [
        page
        for page in context.pages
        if not page.is_closed()
    ]

    if len(pages) <= 1:
        return "There is only one tab open."

    current = get_page()

    try:

        index = pages.index(
            current
        )

    except ValueError:

        index = 0

    active_page = pages[
        (index + 1) % len(pages)
    ]

    active_page.bring_to_front()

    title = active_page.title()

    if title:

        return (
            f"Switched to {title}."
        )

    return "Switched to the next tab."


# Previous Tab
def previous_tab():

    global active_page

    if browser is None:
        return "The browser is not open."

    pages = [
        page
        for page in context.pages
        if not page.is_closed()
    ]

    if len(pages) <= 1:
        return "There is only one tab open."

    current = get_page()

    try:

        index = pages.index(
            current
        )

    except ValueError:

        index = 0

    active_page = pages[
        (index - 1) % len(pages)
    ]

    active_page.bring_to_front()

    title = active_page.title()

    if title:

        return (
            f"Switched to {title}."
        )

    return "Switched to the previous tab."


# Go Back
def browser_back():

    page = get_page()

    try:

        response = page.go_back(
            wait_until="domcontentloaded",
            timeout=30000
        )

        if response is None:

            return (
                "There is no previous page."
            )

        return "Went back."

    except PlaywrightError as error:

        print(
            f"Browser back error: {error}"
        )

        return "I couldn't go back."


# Go Forward
def browser_forward():

    page = get_page()

    try:

        response = page.go_forward(
            wait_until="domcontentloaded",
            timeout=30000
        )

        if response is None:

            return (
                "There is no next page."
            )

        return "Went forward."

    except PlaywrightError as error:

        print(
            f"Browser forward error: {error}"
        )

        return "I couldn't go forward."


# Refresh
def refresh_page():

    page = get_page()

    try:

        page.reload(
            wait_until="domcontentloaded",
            timeout=30000
        )

        return "Page refreshed."

    except PlaywrightError as error:

        print(
            f"Refresh error: {error}"
        )

        return "I couldn't refresh the page."


# Browser Information
def current_browser_page():

    page = get_page()

    try:

        return {
            "title": page.title(),
            "url": page.url
        }

    except Exception:

        return {
            "title": "",
            "url": ""
        }


# Browser Shutdown
def close_browser():

    global playwright_instance
    global browser
    global context
    global active_page

    try:

        if context is not None:

            try:
                context.close()
            except Exception:
                pass

        if browser is not None:

            try:
                browser.close()
            except Exception:
                pass

        if playwright_instance is not None:

            try:
                playwright_instance.stop()
            except Exception:
                pass

    finally:

        playwright_instance = None
        browser = None
        context = None
        active_page = None


# Test
if __name__ == "__main__":

    try:

        print(
            open_url(
                "github.com"
            )
        )

        input(
            "Press Enter to close browser..."
        )

    finally:

        close_browser()