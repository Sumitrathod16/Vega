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

from config import config

from memory import (
    save_fact,
    search_memory,
    get_all_facts
)

from system_control import (
    volume_up,
    volume_down,
    mute,
    unmute,
    set_volume,
    get_volume,
    media_control,
    lock_pc,
    get_system_status,
    take_screenshot
)

from web_search import search_web

from screen_reader import (
    analyze_screen,
    clear_screen_memory
)

from agent import execute_goal

from browser_control import (
    open_url,
    browser_search,
    new_tab,
    close_tab,
    next_tab,
    previous_tab,
    browser_back,
    browser_forward,
    refresh_page,
    close_browser
)


speech_cfg = config.get("speech", {})

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = speech_cfg.get("energy_threshold", 300)
recognizer.pause_threshold = speech_cfg.get("pause_threshold", 0.7)
recognizer.non_speaking_duration = 0.3

interrupt_listener_stop = threading.Event()


# Whisper Model
print("Loading VEGA speech recognition model...")

whisper_model = WhisperModel(
    speech_cfg.get("whisper_model", "small"),
    device=speech_cfg.get("whisper_device", "cpu"),
    compute_type=speech_cfg.get("whisper_compute_type", "int8")
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

        return text

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


# Agent Command
def is_agent_command(command):

    command = command.lower()

    agent_phrases = [
        "and then",
        "after that",
        "then",
        "and search",
        "and open",
        "and check",
        "and increase",
        "and decrease",
        "and set",
        "and mute",
        "and unmute"
    ]

    return any(
        phrase in command
        for phrase in agent_phrases
    )


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

        command_lower = command.lower()

        if any(
            phrase in command_lower
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
        "vega",
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

        text_lower = text.lower()

        if any(
            phrase in text_lower
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
        "what is on my screen",
        "what's on my screen",
        "what do you see",
        "what can you see",
        "read my screen",
        "look at my screen",
        "check my screen",
        "analyze my screen",
        "analyse my screen",
        "describe my screen",

        "explain this error",
        "what is this error",
        "what's this error",
        "fix this error",
        "help me with this error",

        "what is wrong with this code",
        "what's wrong with this code",
        "check this code",
        "explain this code",

        "summarize this page",
        "summarise this page",
        "read this page",
        "explain this page",

        "read this message",
        "explain this message",

        "what should i click",
        "where should i click",
        "which button should i press",
        "which button should i click",
        "what should i do next",
        "what should i do here",
        "guide me",

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


# Website Detection
def get_website(command):

    websites = {
        "github": "https://github.com",
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "linkedin": "https://linkedin.com",
        "instagram": "https://instagram.com",
        "gmail": "https://mail.google.com"
    }

    clean_command = command.lower()

    for name, url in websites.items():

        if (
            f"open {name}" in clean_command
            or
            f"go to {name}" in clean_command
        ):

            return url

    return None


# Browser Search Query
def extract_browser_search(command):

    command = command.lower().strip()

    phrases = [
        "search browser for",
        "search google for",
        "google search for",
        "search on google for"
    ]

    for phrase in phrases:

        if phrase in command:

            query = command.replace(
                phrase,
                "",
                1
            ).strip()

            if query:
                return query

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

        command = command.strip()
        command_lower = command.lower()

        print(
            f"You: {command}"
        )

        # Shutdown
        if should_shutdown(
            command_lower
        ):

            speak(
                "Alright boss. "
                "Shutting down VEGA."
            )

            return "shutdown"

        # Sleep
        if should_sleep(
            command_lower
        ):

            speak(
                "Alright boss. "
                "I'll go to sleep."
            )

            return "sleep"

        # Agent Mode
        if is_agent_command(
            command_lower
        ):

            try:

                speak(
                    "Alright boss. I'll handle that."
                )

                print(
                    "VEGA Agent Mode activated."
                )

                response = execute_goal(
                    command
                )

                speak_with_interrupt(
                    response
                )

            except Exception as error:

                print(
                    f"Agent error: {error}"
                )

                speak(
                    "I couldn't complete that task."
                )

            continue

        # Set Volume
        if (
            "set volume to" in command_lower
            or
            "set the volume to" in command_lower
        ):

            level = extract_volume_level(
                command_lower
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
            phrase in command_lower
            for phrase in [
                "volume up",
                "increase volume",
                "increase the volume",
                "raise the volume"
            ]
        ):

            amount = extract_number(
                command_lower
            )

            if amount is None:
                amount = 10

            speak(
                volume_up(amount)
            )

            continue

        # Volume Down
        if any(
            phrase in command_lower
            for phrase in [
                "volume down",
                "decrease volume",
                "decrease the volume",
                "lower the volume"
            ]
        ):

            amount = extract_number(
                command_lower
            )

            if amount is None:
                amount = 10

            speak(
                volume_down(amount)
            )

            continue

        # Unmute
        if any(
            phrase in command_lower
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
            phrase in command_lower
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
            phrase in command_lower
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

        # System Status
        if any(
            phrase in command_lower
            for phrase in [
                "system status",
                "check system",
                "cpu status",
                "battery status",
                "system info",
                "how is my system"
            ]
        ):

            speak(
                get_system_status()
            )

            continue

        # Lock PC
        if any(
            phrase in command_lower
            for phrase in [
                "lock pc",
                "lock computer",
                "lock screen",
                "lock workstation"
            ]
        ):

            speak(
                lock_pc()
            )

            continue

        # Media Controls
        if any(
            phrase in command_lower
            for phrase in [
                "play music",
                "pause music",
                "toggle music",
                "media play",
                "media pause"
            ]
        ):

            speak(
                media_control("play_pause")
            )

            continue

        if any(
            phrase in command_lower
            for phrase in [
                "next song",
                "next track",
                "skip song",
                "skip track"
            ]
        ):

            speak(
                media_control("next")
            )

            continue

        if any(
            phrase in command_lower
            for phrase in [
                "previous song",
                "previous track",
                "last song"
            ]
        ):

            speak(
                media_control("previous")
            )

            continue

        # Take Screenshot
        if any(
            phrase in command_lower
            for phrase in [
                "take a screenshot",
                "take screenshot",
                "capture screen"
            ]
        ):

            speak(
                take_screenshot()
            )

            continue

        # Memory - Remember
        if command_lower.startswith("remember that ") or command_lower.startswith("remember "):
            content = command_lower.replace("remember that ", "", 1).replace("remember ", "", 1).strip()
            if " is " in content:
                k, v = content.split(" is ", 1)
                speak(save_fact(k, v))
            elif "=" in content:
                k, v = content.split("=", 1)
                speak(save_fact(k, v))
            else:
                speak(save_fact("note", content))

            continue

        # Memory - Recall
        if "what do you remember" in command_lower or command_lower.startswith("recall "):
            query = command_lower.replace("what do you remember about", "").replace("what do you remember", "").replace("recall", "").strip()
            if not query:
                facts = get_all_facts()
                if facts:
                    fact_str = ", ".join([f"{f['key']}: {f['value']}" for f in facts])
                    speak(f"I remember the following: {fact_str}")
                else:
                    speak("I don't have any saved memories yet.")
            else:
                speak(search_memory(query))

            continue

        # Browser Website
        website = get_website(
            command_lower
        )

        if website:

            try:

                message = open_url(
                    website
                )

                speak(
                    message
                )

            except Exception as error:

                print(
                    f"Browser website error: {error}"
                )

                speak(
                    "I couldn't open that website."
                )

            continue

        # Browser Back
        if any(
            phrase in command_lower
            for phrase in [
                "go back",
                "browser back",
                "previous page"
            ]
        ):

            speak(
                browser_back()
            )

            continue

        # Browser Forward
        if any(
            phrase in command_lower
            for phrase in [
                "go forward",
                "browser forward",
                "next page"
            ]
        ):

            speak(
                browser_forward()
            )

            continue

        # Browser Refresh
        if any(
            phrase in command_lower
            for phrase in [
                "refresh page",
                "refresh the page",
                "reload page",
                "reload the page"
            ]
        ):

            speak(
                refresh_page()
            )

            continue

        # Browser New Tab
        if any(
            phrase in command_lower
            for phrase in [
                "open new tab",
                "new tab",
                "create new tab"
            ]
        ):

            speak(
                new_tab()
            )

            continue

        # Browser Close Tab
        if any(
            phrase in command_lower
            for phrase in [
                "close tab",
                "close this tab",
                "close current tab"
            ]
        ):

            speak(
                close_tab()
            )

            continue

        # Browser Next Tab
        if any(
            phrase in command_lower
            for phrase in [
                "next tab",
                "switch to next tab"
            ]
        ):

            speak(
                next_tab()
            )

            continue

        # Browser Previous Tab
        if any(
            phrase in command_lower
            for phrase in [
                "previous tab",
                "switch to previous tab"
            ]
        ):

            speak(
                previous_tab()
            )

            continue

        # Browser Search
        browser_query = extract_browser_search(
            command_lower
        )

        if browser_query:

            try:

                message = browser_search(
                    browser_query
                )

                speak(
                    message
                )

            except Exception as error:

                print(
                    f"Browser search error: {error}"
                )

                speak(
                    "I couldn't search in the browser."
                )

            continue

        # Manual Web Search
        search_query = extract_search_query(
            command_lower
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

                speak(
                    "I couldn't complete the web search."
                )

            continue

        # Application Control
        app_name = extract_app_name(
            command_lower
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

                speak(
                    "I couldn't open that application."
                )

            continue

        # Clear Screen Context
        if any(
            phrase in command_lower
            for phrase in [
                "forget the screen",
                "clear screen memory",
                "forget previous screen"
            ]
        ):

            clear_screen_memory()

            speak(
                "Screen context cleared."
            )

            continue

        # Screen Awareness
        if is_screen_command(
            command_lower
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
        "Agent Mode: Ready"
    )

    print(
        "Browser Control: Ready"
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

        close_browser()

        shutdown_audio()

        print(
            "VEGA OFFLINE"
        )


# Startup
if __name__ == "__main__":

    main()