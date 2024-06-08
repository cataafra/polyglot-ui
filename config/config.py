import json
import os


def load_config(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


class Config:
    def __init__(self, filepath):
        self.config = load_config(filepath)

    def get(self, section, key=None):
        if key:
            return self.config.get(section, {}).get(key)
        return self.config.get(section)

    def getint(self, section, key):
        return int(self.get(section, key))

    def getboolean(self, section, key):
        return self.get(section, key).lower() in ['true', '1', 'yes', 'y']


config_path = 'config.json'
config = Config(config_path)
