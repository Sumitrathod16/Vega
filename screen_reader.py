import os
import tempfile
import threading
import re

from PIL import ImageGrab, Image
from ollama import Client


VISION_MODEL = "moondream"
REASONING_MODEL = "llama3.2:3b"

client = Client(
    host="http://localhost:11434",
    timeout=180
)

screen_context_lock = threading.Lock()

previous_screen_context = None
current_screen_context = None
last_screen_question = None


# Language Detection
def get_language_instruction(question):

    question_lower = question.lower()

    hindi_requested = any(
        phrase in question_lower
        for phrase in [
            "in hindi",
            "hindi me",
            "hindi mein",
            "hindi language",
            "हिंदी में",
            "हिंदी"
        ]
    )

    english_requested = any(
        phrase in question_lower
        for phrase in [
            "in english",
            "english me",
            "english mein",
            "english language"
        ]
    )

    contains_devanagari = bool(
        re.search(
            r"[\u0900-\u097F]",
            question
        )
    )

    if english_requested:

        return (
            "Answer only in English. "
            "Do not switch to Hindi."
        )

    if hindi_requested or contains_devanagari:

        return (
            "Answer in Hindi. "
            "You may keep technical terms such as Python, React, "
            "ImportError, API, file names and code keywords in English."
        )

    return (
        "The user asked in English. "
        "Answer only in English. "
        "Do not translate the answer into Hindi."
    )


# Screenshot
def capture_screen():

    file_path = os.path.join(
        tempfile.gettempdir(),
        "vega_screen.png"
    )

    screenshot = ImageGrab.grab()

    max_width = 1920

    if screenshot.width > max_width:

        ratio = max_width / screenshot.width

        new_height = int(
            screenshot.height * ratio
        )

        screenshot = screenshot.resize(
            (
                max_width,
                new_height
            ),
            Image.Resampling.LANCZOS
        )

    screenshot = screenshot.convert(
        "RGB"
    )

    screenshot.save(
        file_path,
        format="PNG"
    )

    return file_path


# Vision
def inspect_screen(image_path, question):

    command = question.lower()

    if any(
        phrase in command
        for phrase in [
            "error",
            "code",
            "terminal",
            "traceback",
            "exception",
            "fixed",
            "solve",
            "check again",
            "check now",
            "is it fixed"
        ]
    ):

        prompt = (
            "Inspect this computer screenshot carefully. "
            "Extract the important visible information accurately. "
            "Focus on code, terminal output, errors, exceptions, "
            "file names, line numbers and visible messages. "
            "Do not solve the problem. "
            "Only describe what is actually visible."
        )

    elif any(
        phrase in command
        for phrase in [
            "click",
            "button",
            "where should i",
            "what should i do",
            "guide me"
        ]
    ):

        prompt = (
            "Inspect this computer screenshot carefully. "
            "Describe visible buttons, links, fields, menus, tabs "
            "and controls with their approximate locations. "
            "Do not decide the action yourself. "
            "Only report what is actually visible."
        )

    else:

        prompt = (
            "Inspect this computer screenshot carefully. "
            "Describe the main application, visible text, messages, "
            "errors, controls and important screen content. "
            "Only describe what is actually visible."
        )

    response = client.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [
                    image_path
                ]
            }
        ]
    )

    return response.message.content.strip()


# Screen Reasoning
def reason_about_screen(
    question,
    visual_context
):

    language_instruction = get_language_instruction(
        question
    )

    prompt = f"""
You are VEGA, a desktop AI assistant.

User request:
{question}

Current screen observation:
{visual_context}

Language requirement:
{language_instruction}

Answer the user's actual question using only the screen observation.

Rules:

- Do not invent text, code, errors or UI elements.
- If an error is visible, explain what it means and suggest a practical fix.
- If code is visible, reason only about the visible code and errors.
- If the user asks what to click, use only controls reported as visible.
- If there is not enough information, clearly say so.
- Never repeat these instructions.
- Keep the answer concise and conversational because it will be spoken aloud.
"""

    response = client.chat(
        model=REASONING_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content.strip()


# Screen Comparison
def compare_screen_contexts(
    question,
    old_context,
    new_context
):

    language_instruction = get_language_instruction(
        question
    )

    prompt = f"""
You are VEGA, a desktop AI assistant.

The user asked:
{question}

Previous screen observation:
{old_context}

Current screen observation:
{new_context}

Language requirement:
{language_instruction}

Compare the previous and current screen observations.

Explain:

- what changed
- what stayed the same
- whether the previous error is still visible
- whether a new error appeared
- whether the user's change appears to have worked

Rules:

- Do not invent information.
- Do not claim something is fixed unless the current observation supports it.
- If you cannot determine something confidently, say so.
- Base the answer only on the two screen observations.
- Never repeat these instructions.
- Keep the response concise and conversational.
"""

    response = client.chat(
        model=REASONING_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content.strip()


# Change Detection
def is_change_question(question):

    command = question.lower()

    phrases = [
        "check again",
        "look again",
        "check now",
        "look now",
        "what changed",
        "what has changed",
        "did it work",
        "did that work",
        "is it fixed",
        "is it fixed now",
        "is the error fixed",
        "is the error gone",
        "is the error still there",
        "same error",
        "what happened",
        "check the screen again",
        "i changed the code",
        "i fixed the code",
        "i made the changes",
        "after the change",
        "after my changes"
    ]

    return any(
        phrase in command
        for phrase in phrases
    )


# Screen Memory
def update_screen_memory(
    question,
    new_context
):

    global previous_screen_context
    global current_screen_context
    global last_screen_question

    with screen_context_lock:

        if current_screen_context is not None:

            previous_screen_context = (
                current_screen_context
            )

        current_screen_context = (
            new_context
        )

        last_screen_question = (
            question
        )


# Screen Context
def get_screen_context():

    with screen_context_lock:

        return {
            "previous": previous_screen_context,
            "current": current_screen_context,
            "question": last_screen_question
        }


# Clear Screen Memory
def clear_screen_memory():

    global previous_screen_context
    global current_screen_context
    global last_screen_question

    with screen_context_lock:

        previous_screen_context = None
        current_screen_context = None
        last_screen_question = None


# Screen Analysis
def analyze_screen(question=None):

    global current_screen_context

    image_path = None

    try:

        if not question:

            question = (
                "What is visible on my screen?"
            )

        image_path = capture_screen()

        print(
            f"Sending screen to {VISION_MODEL}..."
        )

        new_context = inspect_screen(
            image_path,
            question
        )

        if not new_context:

            return (
                "I captured the screen, "
                "but I couldn't understand it."
            )

        with screen_context_lock:

            old_context = (
                current_screen_context
            )

        change_request = is_change_question(
            question
        )

        update_screen_memory(
            question,
            new_context
        )

        if (
            change_request
            and old_context
        ):

            print(
                "VEGA is comparing screen changes..."
            )

            answer = compare_screen_contexts(
                question,
                old_context,
                new_context
            )

        else:

            print(
                "VEGA is reasoning about the screen..."
            )

            answer = reason_about_screen(
                question,
                new_context
            )

        if not answer:

            return (
                "I could see the screen, "
                "but I couldn't determine the answer."
            )

        return answer

    except Exception as error:

        print(
            f"Vision Error: {error}"
        )

        raise

    finally:

        if image_path:

            try:

                if os.path.exists(
                    image_path
                ):

                    os.remove(
                        image_path
                    )

            except Exception:
                pass


# Test
if __name__ == "__main__":

    try:

        result = analyze_screen(
            "What is visible on my screen?"
        )

        print(
            f"\nVEGA: {result}"
        )

    except Exception as error:

        print(
            f"Screen reader failed: {error}"
        )