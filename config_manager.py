import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "commands": [],
            "main_browser": "",
            "trigger_key": "]",
            "speaker_recognition_enabled": False,
            "enrollments": {},
            "active_enrollment": ""
        }
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def add_command_entry(entry):
    config = load_config()
    for cmd in config.get("commands", []):
        if cmd["keyword"].lower() == entry["keyword"].lower():
            raise ValueError("Keyword must be unique.")
    config["commands"].append(entry)
    save_config(config)

def update_command_entry(index, entry):
    config = load_config()
    cmds = config.get("commands", [])
    if index < 0 or index >= len(cmds):
        raise IndexError("Invalid command index.")
    for i, cmd in enumerate(cmds):
        if i != index and cmd["keyword"].lower() == entry["keyword"].lower():
            raise ValueError("Keyword must be unique.")
    cmds[index] = entry
    config["commands"] = cmds
    save_config(config)

def delete_command_entry(index):
    config = load_config()
    cmds = config.get("commands", [])
    if index < 0 or index >= len(cmds):
        raise IndexError("Invalid command index.")
    del cmds[index]
    config["commands"] = cmds
    save_config(config)

def set_main_browser(path):
    config = load_config()
    config["main_browser"] = path
    save_config(config)

def set_trigger_key(key):
    config = load_config()
    config["trigger_key"] = key
    save_config(config)

# — New speaker‑recognition config functions —
def set_speaker_recognition_enabled(enabled):
    config = load_config()
    config["speaker_recognition_enabled"] = bool(enabled)
    save_config(config)

def add_enrollment(name, file_path):
    config = load_config()
    enrollments = config.get("enrollments", {})
    if name in enrollments:
        raise ValueError(f"Enrollment '{name}' already exists.")
    enrollments[name] = file_path
    config["enrollments"] = enrollments
    if not config.get("active_enrollment"):
        config["active_enrollment"] = name
    save_config(config)

def delete_enrollment(name):
    config = load_config()
    enrollments = config.get("enrollments", {})
    if name not in enrollments:
        raise ValueError(f"Enrollment '{name}' not found.")
    del enrollments[name]
    config["enrollments"] = enrollments
    if config.get("active_enrollment") == name:
        config["active_enrollment"] = next(iter(enrollments), "")
    save_config(config)

def set_active_enrollment(name):
    config = load_config()
    enrollments = config.get("enrollments", {})
    if name not in enrollments:
        raise ValueError(f"Enrollment '{name}' not found.")
    config["active_enrollment"] = name
    save_config(config)
