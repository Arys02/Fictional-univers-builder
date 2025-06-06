import json

from llm_core.tokenizer.base_tokenizer import BaseTokenizer



class CharTokenizer(BaseTokenizer):
    def __init__(self, alphabet=None):
        if alphabet:
            self.alphabet = alphabet
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
