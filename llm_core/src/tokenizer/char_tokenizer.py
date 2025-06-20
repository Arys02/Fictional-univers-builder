import json

from llm_core.config import RAW_DATA_DIR
from llm_core.src.tokenizer.base_tokenizer import BaseTokenizer


class CharTokenizer(BaseTokenizer):
    def __init__(self, dataset_name=None):
        if dataset_name:
            with open(RAW_DATA_DIR / dataset_name / '.txt', 'r', encoding='utf-8') as f:
                text = f.read()
            chars = sorted(list(set(text)))
            vocab_size = len(chars)
            self.alphabet = vocab_size
        else:
            self.alphabet = ""
        self.stoi = {ch: i for i, ch in enumerate(self.alphabet)}
        self.itos = {i: ch for i, ch in enumerate(self.alphabet)}

    def encode(self, text):
        return [self.stoi[c] for c in text if c in self.stoi]

    def decode(self, tokens):
        return ''.join(self.itos[t] for t in tokens)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'alphabet': self.alphabet}, f)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.alphabet = data['alphabet']
            self.stoi = {ch: i for i, ch in enumerate(self.alphabet)}
            self.itos = {i: ch for i, ch in enumerate(self.alphabet)}

    def train(self, text, directory, max_tokens=10):
        pass
