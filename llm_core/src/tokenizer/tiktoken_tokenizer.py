import json
from collections import OrderedDict
import tiktoken

from tqdm import tqdm

from llm_core.config import SAVED_TOKENIZER_DIR, RAW_DATA_DIR
from llm_core.src.tokenizer.base_tokenizer import BaseTokenizer


class TiktokenTokenizer(BaseTokenizer):
    def __init__(self, tokenizer: str = None):
        self.tokens = None
        self.tokenizer = tokenizer
        self.encoder = tiktoken.get_encoding(tokenizer)


    def train(self, dataset_name, max_token=256):
        with open(RAW_DATA_DIR / f'{dataset_name}.txt', 'r', encoding='utf-8') as f:
            text = f.read()

        tokens = self.encoder.encode(text)
        self.tokens = torch.tensor(tokens)


    def encode(self, text):
        print(type(text))
        tokens = self.encoder.encode(text)
        return tokens


    def decode(self, tokens):
        pass


    def save(self, path):
        pass


    def load(self, path):
        pass
