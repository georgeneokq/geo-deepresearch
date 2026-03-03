import os

class Config:
    def __init__(self):
        self.parallel_mode_enabled = os.environ.get("PARALLEL_MODE", "").lower() == "true"

    def is_parallel_mode_enabled(self):
        return self.parallel_mode_enabled

config = Config()
