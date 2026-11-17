# Scientific Calculator

A responsive desktop calculator built with Python and Tkinter. It supports
basic and scientific calculations, linear and quadratic equations, day/night
themes, and plain-language explanations of operations.

## Requirements

- Python 3.10 or newer
- Internet access and a microphone for online voice recognition

## Run

From this folder in Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python calculater.py
```

The calculator window opens. To use voice input, click **Speak** and say one
math operation, such as “six times four” or “square root of eighty one”.

## Test

```bash
python -m unittest -v
```

## Voice privacy

Voice recognition uses Google's online speech-recognition service. Microphone
audio is sent to Google and requires an internet connection. Spoken answers
use the computer's local speech voices. See [VOICE_SETUP.md](VOICE_SETUP.md)
for details.
