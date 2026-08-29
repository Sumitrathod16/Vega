import json
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "config.json"
)

DEFAULT_CONFIG = {
    "assistant_name": "VEGA",
    "user_name": "Sumit",
    "models": {
        "chat_model": "llama3.2:3b",
        "vision_model": "moondream"
    },
    "speech": {
        "whisper_model": "small",
        "whisper_device": "cpu",
        "whisper_compute_type": "int8",
        "energy_threshold": 300,
        "pause_threshold": 0.7
    },
    "browser": {
        "headless": False,
        "timeout_ms": 30000
    },
    "storage": {
        "memory_db_name": "vega_memory.db"
    }
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as file:
                config = json.load(file)
                # Merge defaults for any missing keys
                for key, val in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = val
                    elif isinstance(val, dict) and isinstance(config[key], dict):
                        for sub_key, sub_val in val.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_val
                return config
        except Exception as error:
            print(f"Error loading config.json: {error}. Using defaults.")
    return DEFAULT_CONFIG


def save_config(config_data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(config_data, file, indent=2)
        return True
    except Exception as error:
        print(f"Error saving config.json: {error}")
        return False


config = load_config()
