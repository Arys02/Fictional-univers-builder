from pathlib import Path

from llm_core.config import TOKENIZED_DATA_DIR, RAW_DATA_DIR
import torch


class DataLoader:
    def __init__(self, path: Path, type: str, device):
        if type == 'tokens':
            self.tokens = torch.load(path).to(device)
        elif type == 'raw':
            with open(path, 'r', encoding='utf-8') as f:
                self.rawdata = f.read()
        self.current_position = 0

    @classmethod
    def fromTokens(cls, type: str, dataset: str, vocab_size: int, device):
        return cls(TOKENIZED_DATA_DIR / f'tokenizer_{type}_{dataset}_{vocab_size}.pt', 'tokens', device)

    @classmethod
    def fromRaw(cls, dataset: str):
        return cls(RAW_DATA_DIR / f'{dataset}.txt', 'raw', "")

    def split(self, val_size):
        assert self.tokens is not None, 'DataLoader has not been initialized'
        n = int(len(self.tokens) * val_size)
        train_data = self.tokens[:n]
        val_data = self.tokens[n:]
        return train_data, val_data

    def get_batch(self, batch_size, block_size):
        assert self.tokens is not None, 'DataLoader has not been initialized'
        B, T = batch_size, block_size
        buf = self.tokens[self.current_position:self.current_position + B*T+1]
        x = (buf[:-1]).view(B, T)
        y = (buf[1:]).view(B, T)

        self.current_position += B*T

        if self.current_position  + (B * T + 1) >= len(self.tokens):
            self.current_position = 0
        return x, y

