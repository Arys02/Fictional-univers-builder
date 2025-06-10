import torch

from llm_core.src.utils.load_config import load_config


class ExperimentConfig:
    def __init__(self, path):
        c = load_config(path=path)
        self.config = {
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        }
        self.config = self.config | c['model'] | c['training'] | c['meta']
        self.config['lr'] = float(self.config['lr'])

    def __getattr__(self, value):
        try:
            return self.config[value]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{value}'")

    def __setattr__(self, key, value):
        if key == 'config':
            super().__setattr__(key, value)
        else:
            self.config[key] = value

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def to_dict(self):
        return self.config
