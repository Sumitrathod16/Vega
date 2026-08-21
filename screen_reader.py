import os
import tempfile

from PIL import ImageGrab, Image
from ollama import Client


VISION_MODEL = "moondream"
REASONING_MODEL = "llama3.2:3b"

client = Client(
    host="http://localhost:11434",
    timeout=180
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
            "exception"
        ]
    ):

        prompt = (
            "Inspect this computer screenshot carefully. "
            "Extract the important visible text exactly where possible. "
            "Focus especially on code, terminal output, errors, exceptions, "
            "file names, line numbers and visible messages. "
            "Do not solve the problem. "
            "Only describe and extract what you can actually see."
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
            "Inspect this computer screenshot. "
            "Describe the visible interface. "
            "List the important visible buttons, links, fields, menus, tabs "
            "and their approximate locations. "
            "Do not decide what the user should click. "
            "Only report what is visibly present."
        )

    else:

        prompt = (
            "Describe this computer screen accurately. "
            "Mention the main application, important visible text, "
            "errors, messages and useful interface elements. "
            "Do not invent anything."
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
def reason_about_screen(question, visual_context):

    prompt = f"""
You are VEGA, a desktop AI assistant.

The user asked:
{question}

A vision model inspected the user's current screen and reported:

{visual_context}

Answer the user's actual question using only the screen information above.

Rules:

- Do not invent text or UI controls that were not observed.
- If the screen information is insufficient, clearly say so.
- If an error is visible, explain the likely cause and practical next step.
- If code is visible, reason about the visible code or error.
- If the user asks what to click, identify the most relevant visible control
  and explain where it is.
- If the user asks for a page summary, summarize only visible information.
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


# Screen Analysis
def analyze_screen(question=None):

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

        visual_context = inspect_screen(
            image_path,
            question
        )

        if not visual_context:

            return (
                "I could capture the screen, "
                "but I couldn't understand what was visible."
            )

        print(
            "VEGA is reasoning about the screen..."
        )

        answer = reason_about_screen(
            question,
            visual_context
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