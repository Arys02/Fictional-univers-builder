import torch

from llm_core.src.utils.load_config import load_config


class ExperimentConfig:
    def __init__(self, path):
        c = load_config(path=path)
        self.model = c["model"]
        self.training = c["training"]
        self.meta = c['meta']
        self.meta['device'] = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = c['tokenizer']

        self.tokenizer['tokenizer_name'] = ("tokenizer_"
                                            + c['tokenizer']['tokenizer_type']
                                            + '_'
                                            + c['meta']['dataset']
                                            + '_'
                                            + str(c['tokenizer']['vocab_size']))

        self.config = c['model'] | c['training'] | c['meta'] | c['tokenizer']
        self.config['lr'] = float(self.config['lr'])
        self.config['checkpoint_dir'] = "./checkpoints"

    def __getattr__(self, value):
        config = self.__dict__.get("config", {})
        if value in config:
            return config[value]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{value}'")

    def __getitem__(self, key):
        if key == "meta":
            return self.meta
        if key == "training":
            return self.training
        if key == "model":
            return self.model
        if key == "tokenizer":
            return self.tokenizer
        return self.config

    def to_dict(self):
        return {
            "meta": self.meta,
            "training": self.training,
            "model": self.model,
            "tokenizer": self.tokenizer,
        }
