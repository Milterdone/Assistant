from PyQt5.QtCore import QThread, pyqtSignal
import sounddevice as sd
import numpy as np
import wave
import subprocess
import os
import keyboard
import threading
import time
import config_manager
import ctypes.util
import urllib.parse
import whisper
from speechbrain.inference.speaker import SpeakerRecognition

if os.name == "nt":
    if ctypes.util.find_library("c") is None:
        original_find_library = ctypes.util.find_library
        def patched_find_library(name):
            if name == "c":
                return "msvcrt.dll"
            return original_find_library(name)
        ctypes.util.find_library = patched_find_library

class VoiceAssistantThread(QThread):
    log_signal = pyqtSignal(str)
    command_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        cfg = config_manager.load_config()
        self.trigger_key = cfg.get("trigger_key", "]")
        self.speaker_enabled = cfg.get("speaker_recognition_enabled", False)
        self.enrollments = cfg.get("enrollments", {})
        self.active_enrollment = cfg.get("active_enrollment", "")
        self.enroll_path = self.enrollments.get(self.active_enrollment, "")

        self.is_recording = False
        self.audio_buffer = []
        self.stream = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Models
        self.whisper_model = None
        self.verifier = None
        if self.speaker_enabled and os.path.exists(self.enroll_path):
            self.verifier = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device":"cuda"}
            )

    def run(self):
        self.log(f"Voice Assistant started. Trigger key: {self.trigger_key}")
        keyboard.on_press_key(self.trigger_key, self.key_down_callback, suppress=False)
        keyboard.on_release_key(self.trigger_key, self.key_up_callback, suppress=False)
        while not self._stop_event.is_set():
            time.sleep(0.1)
        keyboard.unhook_all()
        self.log("Voice Assistant stopped.")

    def stop(self):
        self._stop_event.set()

    def update_trigger_key(self, new_key):
        keyboard.unhook_all()
        self.trigger_key = new_key
        keyboard.on_press_key(self.trigger_key, self.key_down_callback, suppress=False)
        keyboard.on_release_key(self.trigger_key, self.key_up_callback, suppress=False)
        self.log("Trigger key updated to: " + self.trigger_key)

    def update_speaker_settings(self, enabled, enroll_path):
        self.speaker_enabled = enabled
        self.enroll_path = enroll_path
        if enabled and os.path.exists(enroll_path) and self.verifier is None:
            self.verifier = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device":"cuda"}
            )
        self.log(f"Speaker recognition {'enabled' if enabled else 'disabled'}. Enrollment: {enroll_path}")

    def key_down_callback(self, event):
        with self._lock:
            if not self.is_recording:
                self.is_recording = True
                self.audio_buffer = []
                self.log("Recording started.")
                self.stream = sd.InputStream(samplerate=44100, channels=1, callback=self.audio_callback)
                self.stream.start()

    def key_up_callback(self, event):
        with self._lock:
            if self.is_recording:
                self.is_recording = False
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
                self.log("Recording stopped.")
                threading.Thread(target=self.process_audio).start()

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            self.log("Error: " + str(status))
        self.audio_buffer.append(indata.copy())

    def process_audio(self):
        try:
            audio_data = np.concatenate(self.audio_buffer, axis=0)
            file_path = "last_recording.wav"
            with wave.open(file_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            self.log(f"Saved recording to {file_path}")

            if self.speaker_enabled:
                if self.enroll_path and os.path.exists(self.enroll_path):
                    score, same = self.verifier.verify_files(self.enroll_path, file_path)
                    score = float(score)
                    if not same:
                        self.log(f"Speaker rejected (score={score:.2f})")
                        return
                    self.log(f"Speaker accepted (score={score:.2f})")
                else:
                    self.log("Speaker recognition enabled but no enrollment found; skipping.")

            # Transcribe
            transcription = self.transcribe_audio(file_path).strip(".,?\\")
            self.log("Transcription: " + transcription)
            self.process_command(transcription)

        except Exception as e:
            self.log("Error processing audio: " + str(e))

    def transcribe_audio(self, file_path):
        if self.whisper_model is None:
            self.log("Loading Whisper model...")
            self.whisper_model = whisper.load_model("small")
            self.log("Whisper model loaded.")
        result = self.whisper_model.transcribe(file_path)
        return result.get("text", "").lower()

    def process_command(self, transcription):
        cfg = config_manager.load_config()
        commands = []
        mb = cfg.get("main_browser")
        if mb:
            default = [
                {"title": "Search",    "keyword": "search",    "type": "browser_search",  "data": "https://www.google.com/search?q={query}"},
                {"title": "Wikipedia", "keyword": "wikipedia", "type": "browser_search",  "data": "https://en.wikipedia.org/wiki/{query}"},
                {"title": "Browser",   "keyword": "browser",   "type": "browser_control", "data": "open"},
                {"title": "New Tab",   "keyword": "new tab",   "type": "browser_control", "data": "new_tab"},
                {"title": "Incognito", "keyword": "incognito", "type": "browser_control", "data": "incognito"}
            ]
            commands.extend(default)
        commands.extend(cfg.get("commands", []))

        executed = False
        for cmd in commands:
            kw = cmd.get("keyword","").lower()
            if kw and kw in transcription:
                self.log(f"Running '{cmd.get('title')}' for keyword '{kw}'")
                if cmd["type"] == "app":
                    self.open_app(cmd["data"])
                elif cmd["type"] == "browser_search":
                    q = transcription.split(kw,1)[1].strip()
                    url = cmd["data"].format(query=urllib.parse.quote_plus(q))
                    self.open_browser(url=url)
                else:
                    act = cmd["data"]
                    if act=="open":     self.open_browser()
                    if act=="new_tab":  self.open_browser(extra_args=["--new-tab"])
                    if act=="incognito":self.open_browser(extra_args=["--incognito"])
                executed = True
                break
        if not executed:
            self.log("No command matched.")

    def open_app(self, path):
        if path and os.path.exists(path):
            try: subprocess.Popen([path]); self.log("Launched app: "+path)
            except Exception as e: self.log("Error launching app: "+str(e))
        else:
            self.log("Invalid app path: "+str(path))

    def open_browser(self, url=None, extra_args=None):
        cfg = config_manager.load_config()
        bp = cfg.get("main_browser","")
        if not bp or not os.path.exists(bp):
            self.log("Browser not configured or invalid.")
            return
        args = [bp] + (extra_args or [])
        if url: args.append(url)
        try: subprocess.Popen(args); self.log("Opened browser: "+" ".join(args))
        except Exception as e: self.log("Error opening browser: "+str(e))

    def log(self, message):
        self.log_signal.emit(message)
        print(message)
