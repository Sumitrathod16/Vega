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

from memory import (
    save_fact,
    delete_fact,
    search_memory,
    get_all_facts,
    log_interaction
)

from input_control import (
    type_text,
    press_key,
    press_multiple_keys,
    copy,
    paste,
    cut,
    select_all,
    save,
    undo,
    redo,
    find,
    new_item,
    close_window,
    switch_window,
    open_task_manager,
    move_mouse,
    left_click,
    double_click,
    right_click,
    middle_click,
    scroll_up,
    scroll_down,
    drag_mouse,
    get_mouse_position
)

recognizer = sr.Recognizer()

recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.7
recognizer.non_speaking_duration = 0.3

interrupt_listener_stop = threading.Event()


# Whisper Model
print(
    "Loading VEGA speech recognition model..."
)

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print(
    "Speech recognition model ready."
)


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

            segment_text = (
                segment.text
                .strip()
            )

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


# Save Memory Extraction
def extract_memory_save(command):

    clean_command = (
        command
        .strip()
    )

    lower_command = (
        clean_command
        .lower()
    )

    prefixes = [
        "remember that ",
        "remember my ",
        "remember ",
        "save that ",
        "save this memory "
    ]

    content = None

    for prefix in prefixes:

        if lower_command.startswith(
            prefix
        ):

            content = clean_command[
                len(prefix):
            ].strip()

            break

    if not content:
        return None

    separators = [
        " is ",
        " = ",
        " as "
    ]

    lower_content = content.lower()

    for separator in separators:

        if separator in lower_content:

            index = lower_content.find(
                separator
            )

            key = content[
                :index
            ].strip()

            value = content[
                index + len(separator):
            ].strip()

            if key.lower().startswith(
                "my "
            ):

                key = key[3:].strip()

            if key and value:

                return (
                    key,
                    value
                )

    return None


# Forget Memory Extraction
def extract_memory_delete(command):

    clean_command = (
        command
        .strip()
    )

    lower_command = (
        clean_command
        .lower()
    )

    prefixes = [
        "forget about ",
        "forget my ",
        "forget that ",
        "forget ",
        "delete memory ",
        "delete memory about "
    ]

    for prefix in prefixes:

        if lower_command.startswith(
            prefix
        ):

            key = clean_command[
                len(prefix):
            ].strip()

            if key.lower().startswith(
                "my "
            ):

                key = key[3:].strip()

            if key:
                return key

    return None


# Memory Search Extraction
def extract_memory_search(command):

    clean_command = (
        command
        .strip()
    )

    lower_command = (
        clean_command
        .lower()
    )

    phrases = [
        "what do you remember about ",
        "what do you know about ",
        "search your memory for ",
        "search memory for ",
        "check your memory for "
    ]

    for phrase in phrases:

        if lower_command.startswith(
            phrase
        ):

            return clean_command[
                len(phrase):
            ].strip()

    return None


# Memory List Command
def is_memory_list_command(command):

    phrases = [
        "what do you remember",
        "what do you remember about me",
        "show my memories",
        "show stored memories",
        "tell me what you remember",
        "what have you remembered"
    ]

    command = command.strip().lower()

    return command in phrases


# Memory Search Formatter
def format_memory_results(results):

    if not results:

        return (
            "I couldn't find anything matching that "
            "in my memory."
        )

    lines = []

    for memory in results[:5]:

        lines.append(
            f"{memory['key']} is "
            f"{memory['value']}"
        )

    return ". ".join(
        lines
    ) + "."


# All Memory Formatter
def format_all_memories():

    facts = get_all_facts()

    if not facts:

        return (
            "I don't have any persistent memories stored yet."
        )

    lines = []

    for fact in facts[:15]:

        lines.append(
            f"{fact['key']} is "
            f"{fact['value']}"
        )

    return (
        "Here's what I remember. "
        + ". ".join(lines)
        + "."
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

# Typing Command
def extract_typing_text(command):

    clean_command = command.strip()
    lower_command = clean_command.lower()

    prefixes = [
        "type ",
        "write ",
        "type this ",
        "write this "
    ]

    for prefix in prefixes:

        if lower_command.startswith(
            prefix
        ):

            text = clean_command[
                len(prefix):
            ].strip()

            if text:
                return text

    return None


# Key Command
def extract_key_command(command):

    command = command.strip().lower()

    prefixes = [
        "press ",
        "hit "
    ]

    for prefix in prefixes:

        if command.startswith(
            prefix
        ):

            key_text = command[
                len(prefix):
            ].strip()

            if not key_text:
                return None

            replacements = {
                "control": "ctrl",
                "plus": " ",
                "+": " "
            }

            for old, new in replacements.items():

                key_text = key_text.replace(
                    old,
                    new
                )

            keys = [
                key
                for key in key_text.split()
                if key
            ]

            return keys

    return None

# Mouse Coordinates
def extract_mouse_coordinates(command):
    command=command.lower().strip()
    phrases =[
        "move mouse to",
        "move cursor to",
        "move to"
    ]
    for phrase in phrases:
        if command.startswith(
            phrase
        ):
          text = command[
            len(phrase):
          ].strip()
          numbers =[
            int(word)
            for word in text.replace(
                ",",
                " "
            ).split()
            if word.isdigit()
          ]
          if len(numbers)>= 2:
            return (
                numbers[0],
                numbers[1]
            )
    return None
# Drag Coordinates

def extract_drag_coordinates(command):
    command=command.lower().strip()
    phrases=[
        "drag to",
        "drag mouse to",
        "drag cursor to"
    ]                
    for phrase in phrases:
        if command.startswith(
            phrase
        ):
         text = command[
            len(phrase):
         ].strip()

         numbers = [
            int(word)
            for word in text.replace(
                ",",
                " "
            ).split()
            if word.isdigit()
         ]
         if len(numbers)>=2:
            return(
                numbers[0],
                numbers[1]
            )
    return None

# Scroll Amount
def extract_scroll_amount(command):
    words = command.split()
    for word in words:
        if word.isdigit():
            return int(word)
    return 5                    
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

        # Save Memory
        memory_save = extract_memory_save(
            command
        )

        if memory_save:

            key, value = memory_save

            response = save_fact(
                key,
                value,
                "user"
            )

            print(
                f"Memory saved: {key} = {value}"
            )

            speak(
                f"Got it. I'll remember that "
                f"{key} is {value}."
            )

            log_interaction(
                command,
                response
            )

            continue

        # Forget Memory
        memory_delete = extract_memory_delete(
            command
        )

        if memory_delete:

            response = delete_fact(
                memory_delete
            )

            print(
                response
            )

            speak(
                response
            )

            log_interaction(
                command,
                response
            )

            continue

        # Search Memory
        memory_query = extract_memory_search(
            command
        )

        if memory_query:

            results = search_memory(
                memory_query
            )

            response = format_memory_results(
                results
            )

            speak_with_interrupt(
                response
            )

            log_interaction(
                command,
                response
            )

            continue

        # List Memory
        if is_memory_list_command(
            command_lower
        ):

            response = format_all_memories()

            speak_with_interrupt(
                response
            )

            log_interaction(
                command,
                response
            )

            continue
        # Keyboard Routing
        typing_text = extract_typing_text(
            command
        )
        if typing_text:
            response = type_text(
                typing_text
            )
            print(
                response
            )
            continue
                # Move Mouse
        mouse_coordinates = extract_mouse_coordinates(
            command
        )

        if mouse_coordinates:

            x, y = mouse_coordinates

            response = move_mouse(
                x,
                y
            )

            print(
                response
            )

            continue

        # Drag Mouse
        drag_coordinates = extract_drag_coordinates(
            command
        )

        if drag_coordinates:

            x, y = drag_coordinates

            response = drag_mouse(
                x,
                y
            )

            print(
                response
            )

            continue

        # Double Click
        if command_lower in [
            "double click",
            "double click here"
        ]:

            print(
                double_click()
            )

            continue

        # Right Click
        if command_lower in [
            "right click",
            "right click here"
        ]:

            print(
                right_click()
            )

            continue

        # Middle Click
        if command_lower in [
            "middle click"
        ]:

            print(
                middle_click()
            )

            continue

        # Left Click
        if command_lower in [
            "click",
            "left click",
            "click here"
        ]:

            print(
                left_click()
            )

            continue

        # Scroll Up
        if any(
            phrase in command_lower
            for phrase in [
                "scroll up",
                "move page up"
            ]
        ):

            amount = extract_scroll_amount(
                command_lower
            )

            print(
                scroll_up(
                    amount
                )
            )

            continue

        # Scroll Down
        if any(
            phrase in command_lower
            for phrase in [
                "scroll down",
                "move page down"
            ]
        ):

            amount = extract_scroll_amount(
                command_lower
            )

            print(
                scroll_down(
                    amount
                )
            )

            continue

        # Mouse Position
        if command_lower in [
            "mouse position",
            "cursor position",
            "where is the mouse",
            "where is the cursor"
        ]:

            position = get_mouse_position()

            if position:

                response = (
                    f"Mouse position is "
                    f"X {position['x']} "
                    f"and Y {position['y']}."
                )

                print(
                    response
                )

                speak(
                    response
                )

            continue
        # Keyboard Shortcuts
        shortcut_commands ={
            "copy": copy,
            "copy this": copy,
            "paste": paste,
            "paste here": paste,
            "cut": cut,
            "cut this": cut,
            "select all": select_all,
            "save": save,
            "save this": save,
            "undo": undo,
            "redo": redo,
            "find": find,
            "new file": new_item,
            "close window": close_window,
            "switch window": switch_window,
            "open task manager": open_task_manager
        }
        if command_lower in shortcut_commands:
            response = shortcut_commands[
                command_lower
            ]()
            print(
                response
            )
            continue

        # Press Keys
        keys = extract_key_command(
            command
        )
        if keys:
            response = press_multiple_keys(
                keys
            )
            print(
                response
            )
            continue
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

        # Browser Website
        website = get_website(
            command_lower
        )

        if website:

            try:

                speak(
                    open_url(
                        website
                    )
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

                speak(
                    browser_search(
                        browser_query
                    )
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
        "Persistent Memory: SQLite"
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