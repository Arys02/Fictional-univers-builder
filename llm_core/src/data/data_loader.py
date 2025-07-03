from pathlib import Path

import torch

from llm_core.config import TOKENIZED_DATA_DIR, RAW_DATA_DIR

from loguru import logger


class DataLoader:
    def __init__(self, path: Path, type: str, device):
        logger.info(f"DataLoader: Initializing DataLoader, Loading data from {path}")
        self.val_data = None
        self.train_data = None
        if type == 'tokens':
            self.tokens = torch.load(path).to(dtype=torch.int64).to(device)
        elif type == 'raw':
            with open(path, 'r', encoding='utf-8') as f:
                self.rawdata = f.read()
        self.current_position = {'train': 0, 'val': 0}

    @classmethod
    def fromTokens(cls, type: str, dataset: str, vocab_size: int, device):
        return cls(TOKENIZED_DATA_DIR / f'tokenizer_{type}_{dataset}_{vocab_size}.pt', 'tokens', device)

    @classmethod
    def fromRaw(cls, dataset: str):
        return cls(RAW_DATA_DIR / f'{dataset}.txt', 'raw', "")

    def split(self, val_size):
        logger.info(f"DataLoader: Splitting data with x{val_size} elements")
        assert self.tokens is not None, 'DataLoader has not been initialized'
        n = int(len(self.tokens) * val_size)
        train_data = self.tokens[:n]
        val_data = self.tokens[n:]
        self.val_data = val_data
        self.train_data = train_data
        return train_data, val_data

    def get_batch(self, batch_size : int, block_size: int, dataset: str):
        assert self.train_data is not None, 'Data has not been splited'
        dataset_tensor = self.train_data if dataset == 'train' else self.val_data
        B, T = batch_size, block_size
        buf = dataset_tensor[self.current_position[dataset]:self.current_position[dataset] + B * T + 1]
        x = (buf[:-1]).view(B, T)
        y = (buf[1:]).view(B, T)

        self.current_position[dataset] += B * T

        if self.current_position[dataset] + (B * T + 1) >= len(dataset_tensor):
            self.current_position[dataset] = 0
        return x, y
