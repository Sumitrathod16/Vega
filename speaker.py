import os
import re
import asyncio
import tempfile
import threading

import edge_tts
import pygame


ENGLISH_VOICE = "en-US-GuyNeural"
HINDI_VOICE = "hi-IN-MadhurNeural"

speech_lock = threading.Lock()
stop_speaking = threading.Event()

pygame.mixer.init()


# Language Detection
def contains_hindi(text):

    return bool(
        re.search(
            r"[\u0900-\u097F]",
            text
        )
    )


# Voice Selection
def choose_voice(text):

    if contains_hindi(text):
        return HINDI_VOICE

    return ENGLISH_VOICE


# Audio Generation
async def create_audio(
    text,
    file_path
):

    voice = choose_voice(text)

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice
    )

    await communicate.save(
        file_path
    )


# Speech
def speak(text):

    if not text:
        return

    stop_speaking.clear()

    file_path = os.path.join(
        tempfile.gettempdir(),
        "vega_speech.mp3"
    )

    try:

        with speech_lock:

            asyncio.run(
                create_audio(
                    text,
                    file_path
                )
            )

            if stop_speaking.is_set():
                return

            pygame.mixer.music.load(
                file_path
            )

            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():

                if stop_speaking.is_set():

                    pygame.mixer.music.stop()
                    break

                pygame.time.Clock().tick(20)

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

    except Exception as error:

        print(
            f"Speech error: {error}"
        )

    finally:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass


# Stop Voice
def stop_voice():

    stop_speaking.set()

    try:

        if pygame.mixer.get_init():

            pygame.mixer.music.stop()

    except Exception:
        pass


# Audio Shutdown
def shutdown_audio():

    stop_voice()

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