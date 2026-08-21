import os
import tempfile

from PIL import ImageGrab, Image
from ollama import Client


VISION_MODEL = "moondream"

client = Client(
    host="http://localhost:11434",
    timeout=180
)


# Screenshot
def capture_screen():

    file_path = os.path.join(
        tempfile.gettempdir(),
        "vega_screen.jpg"
    )

    screenshot = ImageGrab.grab()

    max_width = 1280

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
        format="JPEG",
        quality=80
    )

    return file_path


# Screen Analysis
# Screen Analysis
def analyze_screen(question=None):

    image_path = None

    try:

        image_path = capture_screen()

        if not question:

            question = "Describe what is visible on this screen."

        command = question.lower()

        if any(
            phrase in command
            for phrase in [
                "what should i click",
                "where should i click",
                "which button should i click",
                "which button should i press",
                "what should i do next",
                "where should i go",
                "how do i continue"
            ]
        ):

            prompt = (
                "Look carefully at this computer screenshot. "
                "Tell me which visible button, link, field, menu, or control "
                "I should use next. "
                "Give its visible name, approximate location, "
                "and one short reason. "
                "Do not repeat these instructions. "
                "Do not invent anything that is not visible."
            )

        elif any(
            phrase in command
            for phrase in [
                "explain this error",
                "what is this error",
                "what's this error",
                "fix this error",
                "help me with this error"
            ]
        ):

            prompt = (
                "Look at this computer screenshot and focus on the visible error. "
                "Tell me what the error says, what it probably means, "
                "and one practical next step. "
                "Do not repeat these instructions."
            )

        elif any(
            phrase in command
            for phrase in [
                "what is wrong with this code",
                "what's wrong with this code",
                "check this code",
                "explain this code"
            ]
        ):

            prompt = (
                "Look at the code visible in this screenshot. "
                "Identify the most obvious visible problem and explain it briefly. "
                "Do not invent code that is not visible. "
                "Do not repeat these instructions."
            )

        elif any(
            phrase in command
            for phrase in [
                "summarize this page",
                "summarise this page",
                "read this page",
                "explain this page"
            ]
        ):

            prompt = (
                "Look at this webpage screenshot. "
                "Summarize the most important visible information in a few sentences. "
                "Do not repeat these instructions."
            )

        elif any(
            phrase in command
            for phrase in [
                "read this message",
                "explain this message"
            ]
        ):

            prompt = (
                "Look at the visible message in this screenshot. "
                "Tell me what it says and explain the important part briefly. "
                "Do not repeat these instructions."
            )

        else:

            prompt = (
                "Describe what is visible on this computer screen. "
                "Mention the main application, important text, "
                "and important controls you can clearly see. "
                "Do not repeat these instructions."
            )

        print(
            f"Sending screen to {VISION_MODEL}..."
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

        answer = response.message.content.strip()

        if not answer:

            return (
                "I can see the screen, "
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