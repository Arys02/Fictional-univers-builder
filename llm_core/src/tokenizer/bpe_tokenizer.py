import json
from collections import OrderedDict

from tqdm import tqdm

from llm_core.src.tokenizer.base_tokenizer import BaseTokenizer


class BPETokenizer(BaseTokenizer):
    def __init__(self, link: str = None):
        if link is None:
            self.bpe_table = OrderedDict()
        else:
            with open(link, "r") as f:
                raw = json.load(f)
                self.bpe_table = OrderedDict({int(k): tuple(v) for k, v in raw.items()})

    def train(self, corpus, max_token=256):
        tokens = list(map(int, corpus.encode("utf-8")))
        max_token = max_token - 256
        BPE: OrderedDict = OrderedDict()
        new_tokens: list = list(tokens)
        keys_tokens = -1
        for _ in tqdm(range(max_token)):
            did_changed = True
            pairs = {}
            for i in range(1, len(new_tokens)):
                if pairs.get((new_tokens[i - 1], new_tokens[i])) is None:
                    pairs[(new_tokens[i - 1], new_tokens[i])] = 1
                else:
                    pairs[(new_tokens[i - 1], new_tokens[i])] += 1
                    did_changed = False
            if did_changed:
                break
            max_key = max(pairs.keys(), key=(lambda key: pairs[key]))
            # print(max_key)
            BPE[keys_tokens] = max_key
            tmp_tokens = []
            for i in range(1, len(new_tokens)):
                if (new_tokens[i - 1], new_tokens[i]) == max_key:
                    if i != 1:
                        tmp_tokens.pop()
                    tmp_tokens.append(keys_tokens)
                else:
                    if i == 1:
                        tmp_tokens.append(new_tokens[0])
                    tmp_tokens.append(new_tokens[i])

            new_tokens = tmp_tokens
            keys_tokens -= 1
        self.bpe_table = BPE

    def encode(self, text):
        tokens = text.encode("utf-8")
        tokens = list(map(int, tokens))

        for keys in self.bpe_table:
            new_tokens = []

            for i in range(1, len(tokens)):
                if (tokens[i - 1], tokens[i]) == keys:
                    if i != 1:
                        new_tokens.pop()
                    new_tokens.append(keys)
                else:
                    if i == 1:
                        new_tokens.append(tokens[0])
                    new_tokens.append(tokens[i])
            tokens = new_tokens
        return tokens

    def decode(self, tokens):
        tmp_tokens = list(tokens)
        for keys in self.bpe_table.__reversed__():
            new_token = []
            for token in tmp_tokens:
                if token == keys:
                    new_token.append(self.bpe_table[token][0])
                    new_token.append(self.bpe_table[token][1])
                else:
                    new_token.append(token)

            tmp_tokens = new_token

        tmp_tokens = bytes(tmp_tokens)
        decoded_tokens = tmp_tokens.decode("utf-8")
        return decoded_tokens

    def save(self, path):
        with open(path, "w") as f:
            json.dump({str(k): list(v) for k, v in self.bpe_table.items()}, f)

    def load(self, path):
        with open(path, "r") as f:
            raw = json.load(f)
            self.bpe_table = OrderedDict({int(k): tuple(v) for k, v in raw.items()})
