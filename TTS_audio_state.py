# audio_state.py
import threading

class AudioState:
    def __init__(self):
        self.current_sound = None
        self.sound_lock = threading.Lock()

audio_state = AudioState()