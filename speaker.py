import asyncio
import edge_tts
import pygame
import os
import tempfile
import uuid
import threading
import time


VOICE = "en-US-GuyNeural"

stop_speaking = threading.Event()

#CREATE AUDIO
async def create_audio(text, file_path):

    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE
    )

    await communicate.save(
        file_path
    )


def stop_voice():

    stop_speaking.set()

    try:

        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    except Exception:
        pass


def shutdown_audio():

    stop_speaking.set()

    try:

        if pygame.mixer.get_init():

            pygame.mixer.music.stop()

            try:
                pygame.mixer.music.unload()

            except Exception:
                pass

            pygame.mixer.quit()

    except Exception:
        pass

#SPEAK AUDIO
def speak(text):

    stop_speaking.clear()

    print(
        f"\nVEGA: {text}"
    )

    file_path = os.path.join(
        tempfile.gettempdir(),
        f"vega_{uuid.uuid4().hex}.mp3"
    )

    try:

        asyncio.run(
            create_audio(
                text,
                file_path
            )
        )

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(
            file_path
        )

        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():

            if stop_speaking.is_set():

                pygame.mixer.music.stop()

                break

            time.sleep(0.05)

        try:
            pygame.mixer.music.unload()

        except Exception:
            pass

    except Exception as error:

        print(
            f"Voice Error: {error}"
        )

    finally:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass


if __name__ == "__main__":

    try:

        speak(
            "Hello boss. "
            "VEGA voice system is working."
        )

    finally:

        shutdown_audio()