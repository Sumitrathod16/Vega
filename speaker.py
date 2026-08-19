import asyncio
import edge_tts
import pygame
import os
import tempfile
import uuid


VOICE = "en-US-GuyNeural"


async def create_audio(text, file_path):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE
    )
    await communicate.save(file_path)


def speak(text):
    print(f"\n VEGA: {text}")

    try:
        file_path = os.path.join(
            tempfile.gettempdir(),
            f"vega_{uuid.uuid4().hex}.mp3"
        )

        asyncio.run(
            create_audio(text, file_path)
        )

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(20)

        pygame.mixer.music.unload()

        try:
            os.remove(file_path)
        except:
            pass

    except Exception as error:
        print(f"Voice Error: {error}")