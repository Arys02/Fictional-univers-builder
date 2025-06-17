import json
from collections import OrderedDict
import tiktoken

from tqdm import tqdm

from llm_core.config import SAVED_TOKENIZER_DIR, RAW_DATA_DIR
from llm_core.src.tokenizer.base_tokenizer import BaseTokenizer


class TiktokenTokenizer(BaseTokenizer):
    def __init__(self, tokenizer: str = None):
        pass


    def train(self, dataset_name, max_token=256):
        pass


    def encode(self, text):
        pass


    def decode(self, tokens):
        pass


    def save(self, path):
        pass


    def load(self, path):
        pass
