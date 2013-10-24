import os
import re
import json
from collections import Mapping

PREFIX = "SNAKEPIT_"

class Config(Mapping):

    def __init__(self):
        self._d = {}
        try:
            with open("config.json") as f:
                self._d = json.load(f)
        except Exception:
            pass

    def __getitem__(self, key):
        if key is None:
            raise KeyError("key cannot be None")
        value = os.getenv(PREFIX + str(key), self._d.get(key))
        if value is None:
            raise KeyError("No value configured for %s" % (key))
        return value

    def __iter__(self):
        env_keys = (re.sub(PREFIX, "") for k in os.environ.keys() if k.startswith(PREFIX))
        return iter(set(env_keys) & set(iter(self._d)))

    def __len__(self):
        return len(iter(self))

