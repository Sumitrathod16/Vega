import os
import tempfile
import time

import cv2
from ollama import Client

VISION_MODEL = "moondream"

client = Client(host="http://localhost:11434", timeout=180)


def capture_camera(camera_index=0, warmup_frames=8):
    camera = None
    try:
        camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not camera.isOpened():
            return False, "I couldn't access the camera."
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        frame = None
        for _ in range(warmup_frames):
            success, frame = camera.read()
            if not success:
                time.sleep(0.05)
                continue
            time.sleep(0.03)
        success, frame = camera.read()
        if not success or frame is None:
            return False, "I couldn't capture an image."
        image_path = os.path.join(tempfile.gettempdir(), "vega_camera_scan.jpg")
        success = cv2.imwrite(image_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success:
            return False, "I couldn't save the camera frame."
        return True, image_path
    except Exception as error:
        print(f"Camera capture error: {error}")
        return False, "Camera capture failed."
    finally:
        if camera is not None:
            camera.release()


def build_vision_prompt(question):
    return f"""
You are VEGA's visual scanner.

User request:
{question}

Carefully inspect the camera image before answering.

Your job is to identify what is actually visible.

OBJECT DETECTION:
- Identify the main visible objects.
- If multiple objects are visible, mention them separately.
- Do not assume an object exists if it is not clearly visible.
- Ignore irrelevant background details unless they help identify an object.

SPECIFIC OBJECT FOCUS:
- If the user asks about a specific object, focus primarily on that object.
- If the requested object is not visible, clearly say that you cannot see it.
- Do not switch to a different object just because it is easier to identify.

KNOWN VS UNKNOWN:
- If an object is confidently recognizable, name the object.
- If an object cannot be identified confidently, call it uncertain or unknown.
- For unknown objects, describe visible characteristics such as shape, color, material, size, position, or apparent purpose.
- Never invent an identity for an unknown object.

CONFIDENCE:
- Only state an identification when the image provides enough visual evidence.
- If the image is blurry, dark, blocked, too far away, or otherwise unclear, say that identification is uncertain.
- Do not turn a guess into a fact.

BRAND / MODEL / PERSON:
- Do not claim an exact brand, model, person, text, serial number, or component unless it is clearly visible.
- If a brand or model is not readable or visually certain, say that you cannot determine it.

EMPTY / UNCLEAR SCENE:
- If there is no useful object visible, say so.
- Do not fill an unclear scene with guessed objects.

RESPONSE STYLE:
- Keep the answer concise and conversational.
- Start with the most important observation.
- Mention uncertainty when necessary.
- Do not describe your internal reasoning.
"""


def analyze_camera_image(image_path, question=None):
    if not question:
        question = "Describe what is visible in front of the camera."
    prompt = build_vision_prompt(question)
    try:
        response = client.chat(
            model=VISION_MODEL,
            messages=[
                {"role": "user", "content": prompt, "images": [image_path]}
            ],
        )
        answer = response.message.content.strip()
        if not answer:
            return "I captured the image, but I couldn't identify anything reliably."
        return answer
    except Exception as error:
        print(f"Camera vision error: {error}")
        return "I captured the image, but the vision analysis failed."


def scan_camera(question=None, camera_index=0):
    image_path = None
    try:
        success, result = capture_camera(camera_index=camera_index)
        if not success:
            return result
        image_path = result
        print(f"Sending camera image to {VISION_MODEL}...")
        return analyze_camera_image(image_path, question)
    finally:
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as error:
                print(f"Could not delete temporary camera image: {error}")


def camera_available(camera_index=0):
    camera = None
    try:
        camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        return camera.isOpened()
    except Exception as error:
        print(f"Camera availability error: {error}")
        return False
    finally:
        if camera is not None:
            camera.release()


if __name__ == "__main__":
    if not camera_available():
        print("VEGA: No camera is available.")
    else:
        print("VEGA: Camera detected.")
        print(scan_camera("What objects can you see in front of me?"))
