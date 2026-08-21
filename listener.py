import os
import tempfile
import threading

import speech_recognition as sr

from faster_whisper import WhisperModel

from brain import (
    ask_vega,
    ask_vega_with_web,
    should_use_web
)

from speaker import (
    speak,
    stop_voice,
    shutdown_audio
)

from apps import open_application

from system_control import (
    volume_up,
    volume_down,
    mute,
    unmute,
    set_volume,
    get_volume
)

from web_search import search_web
from screen_reader import analyze_screen


recognizer = sr.Recognizer()

recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.7
recognizer.non_speaking_duration = 0.3

interrupt_listener_stop = threading.Event()


# Whisper Model
print("Loading VEGA speech recognition model...")

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print("Speech recognition model ready.")


# Microphone Calibration
def calibrate_microphone():

    try:

        with sr.Microphone() as source:

            print(
                "Calibrating microphone..."
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            print(
                f"Microphone ready. Energy threshold: "
                f"{recognizer.energy_threshold}"
            )

    except Exception as error:

        print(
            f"Microphone calibration error: {error}"
        )


# Speech Transcription
def transcribe_audio(audio):

    audio_path = os.path.join(
        tempfile.gettempdir(),
        "vega_input.wav"
    )

    try:

        with open(
            audio_path,
            "wb"
        ) as file:

            file.write(
                audio.get_wav_data()
            )

        segments, info = whisper_model.transcribe(
            audio_path,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False
        )

        text_parts = []

        for segment in segments:

            segment_text = segment.text.strip()

            if segment_text:
                text_parts.append(
                    segment_text
                )

        text = " ".join(
            text_parts
        ).strip()

        if not text:
            return None

        return text.lower()

    except Exception as error:

        print(
            f"Transcription error: {error}"
        )

        return None

    finally:

        try:

            if os.path.exists(
                audio_path
            ):

                os.remove(
                    audio_path
                )

        except Exception:
            pass


# Listening
def listen(
    timeout=8,
    phrase_time_limit=10
):

    try:

        with sr.Microphone() as source:

            print(
                "\nListening..."
            )

            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )

        print(
            "Processing voice..."
        )

        text = transcribe_audio(
            audio
        )

        if text:

            print(
                f"Recognized: {text}"
            )

        return text

    except sr.WaitTimeoutError:

        return None

    except OSError as error:

        print(
            f"Microphone error: {error}"
        )

        return None

    except Exception as error:

        print(
            f"Listening error: {error}"
        )

        return None


# Voice Interruption
def listen_for_interruption():

    interrupt_phrases = [
        "stop",
        "stop vega",
        "vega stop",
        "pause",
        "wait",
        "hold on",
        "stop talking",
        "enough"
    ]

    while not interrupt_listener_stop.is_set():

        command = listen(
            timeout=1,
            phrase_time_limit=2
        )

        if interrupt_listener_stop.is_set():
            return

        if not command:
            continue

        if any(
            phrase in command
            for phrase in interrupt_phrases
        ):

            print(
                "VEGA speech interrupted."
            )

            stop_voice()

            interrupt_listener_stop.set()

            return


# Interruptible Speech
def speak_with_interrupt(text):

    interrupt_listener_stop.clear()

    speech_thread = threading.Thread(
        target=speak,
        args=(text,)
    )

    interrupt_thread = threading.Thread(
        target=listen_for_interruption
    )

    speech_thread.start()
    interrupt_thread.start()

    speech_thread.join()

    interrupt_listener_stop.set()

    interrupt_thread.join(
        timeout=2
    )


# Wake Word
def wait_for_wake_word():

    print(
        "\nVEGA sleeping..."
    )

    wake_words = [
        "hey vega",
        "hello vega",
        "okay vega",
        "ok vega"
    ]

    while True:

        text = listen(
            timeout=5,
            phrase_time_limit=4
        )

        if not text:
            continue

        if any(
            phrase in text
            for phrase in wake_words
        ):

            print(
                "VEGA activated."
            )

            return


# Sleep Commands
def should_sleep(command):

    phrases = [
        "go to sleep",
        "go back to sleep",
        "sleep vega",
        "vega go to sleep",
        "you can sleep",
        "take a rest"
    ]

    return any(
        phrase in command
        for phrase in phrases
    )


# Shutdown Commands
def should_shutdown(command):

    phrases = [
        "shutdown vega",
        "shut down vega",
        "exit vega",
        "quit vega",
        "stop vega completely",
        "terminate vega"
    ]

    return any(
        phrase in command
        for phrase in phrases
    )


# Search Query
def extract_search_query(command):

    clean_command = command.replace(
        "vega",
        ""
    ).strip()

    phrases = [
        "search the web for",
        "search internet for",
        "search the internet for",
        "search web for",
        "search for",
        "look up",
        "find online",
        "google"
    ]

    for phrase in phrases:

        if phrase in clean_command:

            query = clean_command.replace(
                phrase,
                "",
                1
            ).strip()

            if query:
                return query

    return None


# App Name
def extract_app_name(command):

    command = command.replace(
        "vega",
        ""
    ).strip()

    if command.startswith(
        "open "
    ):

        return command.replace(
            "open ",
            "",
            1
        ).strip()

    return None


# Screen Command
def is_screen_command(command):

    screen_words = [
        "screen",
        "this error",
        "this code",
        "this page",
        "this message",
        "what should i click",
        "which button",
        "where should i click",
        "what do you see",
        "what can you see",
        "look at this",
        "look at my",
        "check this",
        "guide me"
    ]

    return any(
        phrase in command
        for phrase in screen_words
    )


# Number Extraction
def extract_number(command):

    command = command.replace(
        "%",
        " "
    )

    for word in command.split():

        if word.isdigit():
            return int(word)

    return None


# Volume Level
def extract_volume_level(command):

    level = extract_number(
        command
    )

    if level is None:
        return None

    if 0 <= level <= 100:
        return level

    return None


# Conversation Mode
def conversation_mode():

    speak(
        "Yes boss?"
    )

    print(
        "\nVEGA ACTIVE"
    )

    while True:

        command = listen(
            timeout=10,
            phrase_time_limit=12
        )

        if not command:
            continue

        print(
            f"You: {command}"
        )

        # Shutdown
        if should_shutdown(
            command
        ):

            speak(
                "Alright boss. "
                "Shutting down VEGA."
            )

            return "shutdown"

        # Sleep
        if should_sleep(
            command
        ):

            speak(
                "Alright boss. "
                "I'll go to sleep."
            )

            return "sleep"

        # Set Volume
        if (
            "set volume to" in command
            or
            "set the volume to" in command
        ):

            level = extract_volume_level(
                command
            )

            if level is None:

                speak(
                    "Tell me the volume percentage."
                )

            else:

                speak(
                    set_volume(level)
                )

            continue

        # Volume Up
        if any(
            phrase in command
            for phrase in [
                "volume up",
                "increase volume",
                "increase the volume",
                "raise the volume"
            ]
        ):

            amount = extract_number(
                command
            )

            if amount is None:
                amount = 10

            speak(
                volume_up(amount)
            )

            continue

        # Volume Down
        if any(
            phrase in command
            for phrase in [
                "volume down",
                "decrease volume",
                "decrease the volume",
                "lower the volume"
            ]
        ):

            amount = extract_number(
                command
            )

            if amount is None:
                amount = 10

            speak(
                volume_down(amount)
            )

            continue

        # Unmute
        if any(
            phrase in command
            for phrase in [
                "unmute",
                "turn sound on"
            ]
        ):

            speak(
                unmute()
            )

            continue

        # Mute
        if any(
            phrase in command
            for phrase in [
                "mute",
                "turn sound off"
            ]
        ):

            speak(
                mute()
            )

            continue

        # Current Volume
        if any(
            phrase in command
            for phrase in [
                "current volume",
                "what is the volume",
                "what's the volume",
                "volume level"
            ]
        ):

            level = get_volume()

            speak(
                f"Current volume is {level} percent."
            )

            continue

        # Manual Web Search
        search_query = extract_search_query(
            command
        )

        if search_query:

            try:

                speak(
                    "Let me check the web."
                )

                search_results = search_web(
                    search_query
                )

                if not search_results:

                    speak(
                        "I couldn't find useful results."
                    )

                    continue

                response = ask_vega_with_web(
                    command,
                    search_results
                )

                speak_with_interrupt(
                    response
                )

            except Exception as error:

                print(
                    f"Web search error: {error}"
                )

            continue

        # Application Control
        app_name = extract_app_name(
            command
        )

        if app_name:

            try:

                success, message = open_application(
                    app_name
                )

                speak(
                    message
                )

            except Exception as error:

                print(
                    f"App error: {error}"
                )

            continue

        # Screen Awareness
        if is_screen_command(
            command
        ):

            try:

                speak(
                    "Let me take a look."
                )

                response = analyze_screen(
                    command
                )

                speak_with_interrupt(
                    response
                )

            except Exception as error:

                print(
                    f"Screen analysis error: {error}"
                )

                speak(
                    "I couldn't analyze the screen."
                )

            continue

        # Automatic Web Detection
        try:

            if should_use_web(
                command
            ):

                speak(
                    "Let me check the latest information."
                )

                search_results = search_web(
                    command
                )

                if search_results:

                    response = ask_vega_with_web(
                        command,
                        search_results
                    )

                    speak_with_interrupt(
                        response
                    )

                else:

                    speak(
                        "I couldn't find reliable current information."
                    )

                continue

        except Exception as error:

            print(
                f"Web routing error: {error}"
            )

        # AI Conversation
        try:

            print(
                "VEGA is thinking..."
            )

            response = ask_vega(
                command
            )

            speak_with_interrupt(
                response
            )

        except Exception as error:

            print(
                f"VEGA error: {error}"
            )

            speak(
                "I ran into a problem while processing that."
            )


# Main System
def main():

    print(
        "\n================================"
    )

    print(
        "           VEGA SYSTEM"
    )

    print(
        "================================"
    )

    print(
        "AI Brain: Ollama"
    )

    print(
        "Speech Recognition: Faster Whisper"
    )

    print(
        "Screen Vision: Moondream"
    )

    print(
        "Screen Reasoning: Llama 3.2"
    )

    print(
        "VEGA online."
    )

    calibrate_microphone()

    try:

        while True:

            wait_for_wake_word()

            result = conversation_mode()

            if result == "shutdown":
                break

    except KeyboardInterrupt:

        print(
            "\nVEGA manually stopped."
        )

    finally:

        interrupt_listener_stop.set()

        stop_voice()

        shutdown_audio()

        print(
            "VEGA OFFLINE"
        )


# Startup
if __name__ == "__main__":

    main()