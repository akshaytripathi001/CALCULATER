# Online voice setup

The calculator records a spoken command and sends the audio to Google's online
speech-recognition service. Internet access is required, and audio is not
processed locally. Speech output remains local and uses the computer's
installed speech voices.

1. Install the optional voice packages from this folder:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Run `python calculater.py`, click **Speak**, and say one short calculation,
   such as “twenty divided by four” or “square root of eighty one”. The voice
   command accepts exactly one math operation; extra words or a second operation
   are rejected so they do not get added to the expression.

Click **Voice on/off** to enable or mute spoken answers.
