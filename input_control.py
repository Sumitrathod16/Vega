import time

import pyautogui


pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


# Key Aliases
KEY_ALIASES = {
    "control": "ctrl",
    "ctrl": "ctrl",
    "alternate": "alt",
    "alt": "alt",
    "windows": "win",
    "window": "win",
    "win": "win",
    "escape": "esc",
    "esc": "esc",
    "return": "enter",
    "enter": "enter",
    "space": "space",
    "spacebar": "space",
    "delete": "delete",
    "backspace": "backspace",
    "tab": "tab",
    "shift": "shift",
    "home": "home",
    "end": "end",
    "insert": "insert",
    "page up": "pageup",
    "page down": "pagedown",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right"
}


# Normalize Key
def normalize_key(key):

    key = key.strip().lower()

    return KEY_ALIASES.get(
        key,
        key
    )


# Type Text
def type_text(
    text,
    interval=0.03
):

    text = text.strip()

    if not text:
        return "There is nothing to type."

    try:

        pyautogui.write(
            text,
            interval=interval
        )

        return "Text typed."

    except Exception as error:

        print(
            f"Typing error: {error}"
        )

        return "I couldn't type the text."


# Press Key
def press_key(key):

    key = normalize_key(
        key
    )

    try:

        pyautogui.press(
            key
        )

        return f"Pressed {key}."

    except Exception as error:

        print(
            f"Key press error: {error}"
        )

        return f"I couldn't press {key}."


# Hotkey
def press_hotkey(*keys):

    normalized_keys = [
        normalize_key(key)
        for key in keys
    ]

    try:

        pyautogui.hotkey(
            *normalized_keys
        )

        return "Shortcut executed."

    except Exception as error:

        print(
            f"Hotkey error: {error}"
        )

        return "I couldn't execute that shortcut."


# Copy
def copy():

    return press_hotkey(
        "ctrl",
        "c"
    )


# Paste
def paste():

    return press_hotkey(
        "ctrl",
        "v"
    )


# Cut
def cut():

    return press_hotkey(
        "ctrl",
        "x"
    )


# Select All
def select_all():

    return press_hotkey(
        "ctrl",
        "a"
    )


# Save
def save():

    return press_hotkey(
        "ctrl",
        "s"
    )


# Undo
def undo():

    return press_hotkey(
        "ctrl",
        "z"
    )


# Redo
def redo():

    return press_hotkey(
        "ctrl",
        "y"
    )


# Find
def find():

    return press_hotkey(
        "ctrl",
        "f"
    )


# New
def new_item():

    return press_hotkey(
        "ctrl",
        "n"
    )


# Close Window
def close_window():

    return press_hotkey(
        "alt",
        "f4"
    )


# Switch Window
def switch_window():

    return press_hotkey(
        "alt",
        "tab"
    )


# Task Manager
def open_task_manager():

    return press_hotkey(
        "ctrl",
        "shift",
        "esc"
    )


# Lock Computer
def lock_computer():

    return press_hotkey(
        "win",
        "l"
    )


# Multiple Key Press
def press_multiple_keys(keys):

    if not keys:
        return "No keys were provided."

    normalized = [
        normalize_key(key)
        for key in keys
    ]

    try:

        if len(normalized) == 1:

            pyautogui.press(
                normalized[0]
            )

        else:

            pyautogui.hotkey(
                *normalized
            )

        return "Keyboard command executed."

    except Exception as error:

        print(
            f"Keyboard command error: {error}"
        )

        return "I couldn't execute that keyboard command."


# Move Mouse
def move_mouse(
    x,
    y,
    duration=0.3
):

    try:

        pyautogui.moveTo(
            int(x),
            int(y),
            duration=duration
        )

        return f"Mouse moved to {x}, {y}."

    except Exception as error:

        print(
            f"Mouse move error: {error}"
        )

        return "I couldn't move the mouse."


# Left Click
def left_click():

    try:

        pyautogui.click()

        return "Clicked."

    except Exception as error:

        print(
            f"Left click error: {error}"
        )

        return "I couldn't click."


# Right Click
def right_click():

    try:

        pyautogui.rightClick()

        return "Right clicked."

    except Exception as error:

        print(
            f"Right click error: {error}"
        )

        return "I couldn't right click."


# Double Click
def double_click():

    try:

        pyautogui.doubleClick(
            interval=0.15
        )

        return "Double clicked."

    except Exception as error:

        print(
            f"Double click error: {error}"
        )

        return "I couldn't double click."


# Middle Click
def middle_click():

    try:

        pyautogui.middleClick()

        return "Middle clicked."

    except Exception as error:

        print(
            f"Middle click error: {error}"
        )

        return "I couldn't middle click."


# Scroll
def scroll_mouse(amount):

    try:

        pyautogui.scroll(
            int(amount)
        )

        return "Scrolled."

    except Exception as error:

        print(
            f"Scroll error: {error}"
        )

        return "I couldn't scroll."


# Scroll Up
def scroll_up(amount=5):

    return scroll_mouse(
        abs(int(amount))
    )


# Scroll Down
def scroll_down(amount=5):

    return scroll_mouse(
        -abs(int(amount))
    )


# Drag Mouse
def drag_mouse(
    x,
    y,
    duration=0.5
):

    try:

        pyautogui.dragTo(
            int(x),
            int(y),
            duration=duration,
            button="left"
        )

        return f"Dragged to {x}, {y}."

    except Exception as error:

        print(
            f"Mouse drag error: {error}"
        )

        return "I couldn't drag the mouse."


# Mouse Position
def get_mouse_position():

    try:

        position = pyautogui.position()

        return {
            "x": position.x,
            "y": position.y
        }

    except Exception as error:

        print(
            f"Mouse position error: {error}"
        )

        return None


# Test
if __name__ == "__main__":

    print(
        "Keyboard and mouse control ready."
    )

    time.sleep(2)

    position = get_mouse_position()

    print(
        position
    )