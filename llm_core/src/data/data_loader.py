from pathlib import Path

from llm_core.config import TOKENIZED_DATA_DIR, RAW_DATA_DIR


class DataLoader:
    def __init__(self, path: Path, type: str, device):
        if type == 'tokens':
            self.data = torch.load(path).to(device)
        elif type == 'raw':
            with open(path, 'r', encoding='utf-8') as f:
                self.rawdata = f.read()

    @classmethod
    def fromTokens(cls, type: str, dataset: str, vocab_size: int, device):
        return cls(TOKENIZED_DATA_DIR / f'tokenizer_{type}_{dataset}_{vocab_size}.pt', 'tokens', device)

    @classmethod
    def fromRaw(cls, dataset: str):
        return cls(RAW_DATA_DIR / f'{dataset}.txt', 'raw', "")

    def split(self, val_size):
        n = int(len(self.data) * val_size)
        train_data = self.data[:n]
        val_data = self.data[n:]
        return train_data, val_data
