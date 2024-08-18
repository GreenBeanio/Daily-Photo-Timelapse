# Daily Photo Timelapse

 A program used to take daily photos and create a video from them.

# How To Use It?

- You need two folders alongside the script
  - photos
  - audio
    - Only if using the ffmpeg script

- Put the photos (jpg or png) in the photos folder
- If using the ffmpeg script and using audio put your audio (wav or mp3) in the audio folder
  - Note that if using the ffmpeg script the video will be the length of the shortest of the combined audio files and the video generated from the images. Be sure to make sure the audio files will be longer than the generated video.

- To add audio, resize, and/or compress the timelapse you will need FFmpeg installed on your system.
  - To use the ffmpeg features run the "main-audio.py" script.
  - If you're not using the ffmpeg features, just the timelapse, use the "main.py" script.

- Setting to modify the scripts actions are at the top of each file. The variables should be self-explanatory.

### Windows

- Initial Run
  - cd /your/folder
  - python3 -m venv env
  - call env/Scripts/activate.bat
  - pip install -r requirements.txt
  - python3 main.py
- Running After
  - cd /your/folder
  - call env/Scripts/activate.bat && python3 main.py

### Linux

- Initial Run
  - cd /your/folder
  - python3 -m venv env
  - source env/bin/activate
  - pip install -r requirements.txt
  - python3 main.py
- Running After
  - cd /your/folder
  - source env/bin/activate && python3 main.py
  - You may have to set executable if it doesn't work
    - chmod +x main.py
