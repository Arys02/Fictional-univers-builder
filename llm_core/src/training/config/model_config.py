import torch

from llm_core.src.utils.load_config import load_config


class ExperimentConfig:
    def __init__(self, path):
        c = load_config(path=path)
        self.model = c["model"]
        self.training = c["training"]
        self.meta = c['meta']
        self.meta['device'] = "cuda" if torch.cuda.is_available() else "cpu"

        self.config = c['model'] | c['training'] | c['meta']
        self.config['lr'] = float(self.config['lr'])

    def __getattr__(self, value):
        try:
            return self.config[value]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{value}'")


    def __getitem__(self, key):
        if key == "meta":
            return self.meta
        if key == "training":
            return self.training
        if key == "model":
            return self.model
        return self.config

    def to_dict(self):
        return {
            "meta": self.meta,
            "training": self.training,
            "model": self.model,
        }
