import os
import re
import json
from collections import Mapping

PREFIX = "SNAKEPIT_"

class Config(Mapping):

    def __init__(self, mode = None):
        self._d = {}
        self._mode = mode
        try:
            with open("config.json") as f:
                self._d = json.load(f)
        except Exception:
            pass

    def __getitem__(self, key):
        if key is None:
            raise KeyError("key cannot be None")

        if self._mode and not key.startswith(self._mode):
            modekey = self._mode + "_" + key
            if modekey in self:
                return self[modekey]

        value = os.getenv(PREFIX + str(key), self._d.get(key))
        if value is None:
            raise ConfigurationError("No value configured for %s" % (key))
        return value

    def __iter__(self):
        env_keys = (re.sub(PREFIX, "", k) for k in os.environ.keys() if k.startswith(PREFIX))
        return iter(set(env_keys) | set(iter(self._d)))

    def __len__(self):
        return len(iter(self))

class ConfigurationError(KeyError):
    """
    Class for reporting that a value has been configured incorrectly.
    """
    pass

