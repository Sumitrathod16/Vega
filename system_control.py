import ctypes
import os
import tempfile
import psutil
from PIL import ImageGrab
from pycaw.pycaw import AudioUtilities


# Virtual Key Codes for Windows Media Control
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xCD
KEYEVENTF_KEYUP = 0x0002


def get_device():
    return AudioUtilities.GetSpeakers()


def get_volume_interface():
    device = get_device()
    return device.EndpointVolume


def get_volume():
    try:
        volume = get_volume_interface()
        current = volume.GetMasterVolumeLevelScalar()
        return round(current * 100)
    except Exception as error:
        print(f"Get volume error: {error}")
        return 0


def set_volume(level):
    try:
        volume = get_volume_interface()
        level = max(0, min(100, int(level)))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level} percent."
    except Exception as error:
        print(f"Set volume error: {error}")
        return f"Couldn't set volume: {error}"


def volume_up(step=10):
    current = get_volume()
    return set_volume(min(100, current + step))


def volume_down(step=10):
    current = get_volume()
    return set_volume(max(0, current - step))


def mute():
    try:
        volume = get_volume_interface()
        volume.SetMute(1, None)
        return "Volume muted."
    except Exception as error:
        return f"Couldn't mute audio: {error}"


def unmute():
    try:
        volume = get_volume_interface()
        volume.SetMute(0, None)
        return "Volume unmuted."
    except Exception as error:
        return f"Couldn't unmute audio: {error}"


def is_muted():
    try:
        volume = get_volume_interface()
        return bool(volume.GetMute())
    except Exception:
        return False


def media_control(action):
    """
    Simulate media keys: 'play', 'pause', 'play_pause', 'next', 'previous'
    """
    action = str(action).lower().strip()
    vk_code = None

    if action in ["play", "pause", "play_pause", "toggle"]:
        vk_code = VK_MEDIA_PLAY_PAUSE
    elif action in ["next", "next_track", "skip"]:
        vk_code = VK_MEDIA_NEXT_TRACK
    elif action in ["prev", "previous", "previous_track", "back"]:
        vk_code = VK_MEDIA_PREV_TRACK
    else:
        return f"Unknown media action: {action}"

    try:
        # Key down then key up
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        return f"Media command '{action}' executed."
    except Exception as error:
        print(f"Media control error: {error}")
        return f"Failed to execute media command: {error}"


def lock_pc():
    """
    Lock the Windows workstation.
    """
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked."
    except Exception as error:
        print(f"Lock PC error: {error}")
        return f"Could not lock computer: {error}"


def get_system_status():
    """
    Return CPU load, memory usage, and battery status.
    """
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory().percent
        status_str = f"CPU usage is at {cpu} percent. Memory usage is at {memory} percent."

        battery = psutil.sensors_battery()
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery power"
            status_str += f" Battery is at {battery.percent} percent ({plugged})."

        return status_str
    except Exception as error:
        print(f"System status error: {error}")
        return f"Couldn't retrieve system status: {error}"


def take_screenshot(filename=None):
    """
    Capture a screenshot and save it locally.
    """
    try:
        if not filename:
            temp_dir = tempfile.gettempdir()
            filename = os.path.join(temp_dir, "vega_screenshot.png")

        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        return f"Screenshot saved to {filename}."
    except Exception as error:
        print(f"Screenshot error: {error}")
        return f"Failed to take screenshot: {error}"


if __name__ == "__main__":
    print(f"Current volume: {get_volume()}%")
    print(f"Muted: {is_muted()}")
    print(f"System status: {get_system_status()}")