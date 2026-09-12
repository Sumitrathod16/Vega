import os
import tempfile
import time

import cv2
from ollama import Client


VISION_MODEL = "moondream"

client = Client(
    host="http://localhost:11434",
    timeout=180
)


def capture_camera(
    camera_index=0,
    warmup_frames=8
):
    """
    Capture one frame from the selected webcam.

    Returns:
        (success, image_path_or_error)
    """

    camera = None
    image_path = None

    try:
        camera = cv2.VideoCapture(
            camera_index,
            cv2.CAP_DSHOW
        )

        if not camera.isOpened():
            return (
                False,
                "I couldn't access the camera."
            )

        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            1280
        )

        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            720
        )

        frame = None

        for _ in range(warmup_frames):
            success, frame = camera.read()

            if not success:
                time.sleep(0.05)
                continue

            time.sleep(0.03)

        success, frame = camera.read()

        if not success or frame is None:
            return (
                False,
                "I couldn't capture an image."
            )

        image_path = os.path.join(
            tempfile.gettempdir(),
            "vega_camera_scan.jpg"
        )

        success = cv2.imwrite(
            image_path,
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                90
            ]
        )

        if not success:
            return (
                False,
                "I couldn't save the camera frame."
            )

        return (
            True,
            image_path
        )

    except Exception as error:
        print(
            f"Camera capture error: {error}"
        )

        return (
            False,
            "Camera capture failed."
        )

    finally:
        if camera is not None:
            camera.release()


def analyze_camera_image(
    image_path,
    question=None
):
    if not question:
        question = (
            "Describe what is visible "
            "in front of the camera."
        )

    prompt = f"""
You are VEGA's visual scanner.

User request:
{question}

Carefully inspect the camera image.

Your job is to identify what is actually visible.

Rules:

- Do not invent objects.
- Mention the main visible objects.
- If the user asks about a specific object,
  focus on that object.
- If you cannot identify something confidently,
  say that you are uncertain.
- Do not claim an exact model, brand, person,
  text, or component unless it is clearly visible.
- Keep the answer concise and conversational.
"""

    try:
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

        answer = (
            response.message.content
            .strip()
        )

        if not answer:
            return (
                "I captured the image, but I "
                "couldn't identify anything reliably."
            )

        return answer

    except Exception as error:
        print(
            f"Camera vision error: {error}"
        )

        return (
            "I captured the image, but the "
            "vision analysis failed."
        )


def scan_camera(
    question=None,
    camera_index=0
):
    image_path = None

    try:
        success, result = capture_camera(
            camera_index=camera_index
        )

        if not success:
            return result

        image_path = result

        print(
            f"Sending camera image to "
            f"{VISION_MODEL}..."
        )

        return analyze_camera_image(
            image_path,
            question
        )

    finally:
        if (
            image_path
            and os.path.exists(image_path)
        ):
            try:
                os.remove(
                    image_path
                )
            except Exception:
                pass


def camera_available(
    camera_index=0
):
    camera = None

    try:
        camera = cv2.VideoCapture(
            camera_index,
            cv2.CAP_DSHOW
        )

        return camera.isOpened()

    except Exception as error:
        print(
            f"Camera availability error: {error}"
        )

        return False

    finally:
        if camera is not None:
            camera.release()


if __name__ == "__main__":
    print(
        scan_camera(
            "What can you see in front of me?"
        )
    )