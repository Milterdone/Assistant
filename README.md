[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# Voice Assistant App

A desktop voice assistant application built with Python and PyQt5. It leverages OpenAI's Whisper for speech-to-text transcription and SpeechBrain for speaker recognition.

## Features

- Triggered recording via a configurable hotkey.
- Real-time audio capture using the `sounddevice` library.
- Speech-to-text transcription with OpenAI Whisper.
- Optional speaker recognition via SpeechBrain’s ECAPA-TDNN model.
- Customizable voice commands to launch applications or control the browser.
- User-friendly GUI for managing commands, enrollments, and settings.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/voice-assistant.git
   cd voice-assistant
   ```

2. Create and activate a Python virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Requirements

- Python 3.8 or higher
- PyQt5
- numpy
- sounddevice
- keyboard
- whisper (OpenAI Whisper)
- speechbrain

## Configuration

The application uses a `config.json` file in the project root to store settings and custom commands. On first run, a default configuration will be generated.

Key settings:

- `trigger_key`: The hotkey to start/stop audio recording (default: `]`).
- `main_browser`: Path to the browser executable for browser commands.
- `speaker_recognition_enabled`: Enable or disable speaker recognition.
- `enrollments`: Map of speaker names to their enrollment audio files.
- `active_enrollment`: The currently selected speaker for verification.
- `commands`: List of custom voice command entries.

## Usage

1. Launch the application:

   ```bash
   python main.py
   ```

2. Use the GUI buttons to add, edit, or delete custom commands, enroll new speakers, or adjust settings.
3. Press the configured trigger key to begin recording, speak your command, and press again to process.
4. View the transcript and action logs in the application console.

## Acknowledgements

This project uses the following third-party libraries and models:

- **OpenAI Whisper** for speech-to-text transcription. Licensed under the MIT License. See the [Whisper repository](https://github.com/openai/whisper) for details.
- **SpeechBrain** for speaker recognition, specifically the `speechbrain/spkrec-ecapa-voxceleb` model. Licensed under the MIT License. See the [SpeechBrain repository](https://github.com/speechbrain/speechbrain) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for full details.

