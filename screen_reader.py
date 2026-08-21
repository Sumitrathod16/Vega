import os
import tempfile

from PIL import ImageGrab, Image
from ollama import Client


VISION_MODEL = "moondream"

client = Client(
    host="http://localhost:11434",
    timeout=300
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
        quality=75,
        optimize=True
    )

    return file_path


# Screen Analysis
def analyze_screen(question=None):

    image_path = None

    try:

        image_path = capture_screen()

        if not question:

            question = (
                "Describe what is visible on this computer screen. "
                "Focus on important applications, text, errors and UI elements. "
                "Keep your answer concise because it will be spoken aloud."
            )

        print(
            f"Sending screen to {VISION_MODEL}..."
        )

        response = client.chat(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": question,
                    "images": [
                        image_path
                    ]
                }
            ]
        )

        answer = response.message.content.strip()

        if not answer:

            return (
                "I could see the screen, "
                "but I couldn't understand enough to describe it."
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