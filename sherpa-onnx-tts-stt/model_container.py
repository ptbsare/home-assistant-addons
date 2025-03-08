from typing import Any

class ModelContainer:
    def __init__(self, stt_model: Any = None, tts_model: Any = None):
        self.stt_model = stt_model
        self.tts_model = tts_model