from pathlib import Path

import numpy as np
import tiktoken
import torch
from tqdm import tqdm
from transformers import GPT2Tokenizer

from llm_core.config import TOKENIZED_DATA_DIR
from llm_core.src.tokenizer.base_tokenizer import BaseTokenizer


class TransformersTokenizer(BaseTokenizer):
    def __init__(self):
        self.tokens = None
        self.tokenizer: GPT2Tokenizer = GPT2Tokenizer.from_pretrained("antoiloui/belgpt2")

    def train(self, dataset_name, dataset_dir, max_token=256):
        token_file = TOKENIZED_DATA_DIR / f'tokenizer_transformers_{dataset_name}_50257.pt'
        token_temp_file = TOKENIZED_DATA_DIR / f'tokenizer_transformers_{dataset_name}_temp.bin'

        total_tokens = 0

        # Utiliser un fichier binaire temporaire pour écrire les tokens progressivement
        with open(dataset_dir / f'{dataset_name}.txt', 'r', encoding='utf-8') as f, open(token_temp_file,
                                                                                         'wb') as temp_f:
            token_buffer = []
            for line in tqdm(f, desc="Tokenizing"):
                token_buffer.extend(self.tokenizer.encode(line))
                # Flush buffer to disk regularly to avoid excessive RAM usage
                if len(token_buffer) >= max_token:
                    np.array(token_buffer, dtype=np.int32).tofile(temp_f)
                    total_tokens += len(token_buffer)
                    token_buffer = []

            # Write any remaining tokens to file
            if token_buffer:
                np.array(token_buffer, dtype=np.int32).tofile(temp_f)
                total_tokens += len(token_buffer)

        print(f"Total tokens tokenized: {total_tokens}")

        # Load as memory-mapped tensor
        tokens_memmap = np.memmap(token_temp_file, dtype=np.int32, mode='r', shape=(total_tokens,))

        # Save final tensor using torch.save for compatibility
        torch.save(torch.from_numpy(tokens_memmap), token_file)

        # Clean up temporary file
        Path(token_temp_file).unlink()

        self.tokens = torch.from_numpy(tokens_memmap)

        print("Tokenization and saving completed.")

    def encode(self, text):
        tokens = self.tokenizer.encode(text)
        return tokens

    def decode(self, tokens):
        return self.tokenizer.decode(tokens)

    def save(self, path):
        pass

    def load(self, path):
        pass


# @misc{louis2020belgpt2,
#   author = {Louis, Antoine},
#   title = {{BelGPT-2: A GPT-2 Model Pre-trained on French Corpora}},
#   year = {2020},
#   howpublished = {\url{https://github.com/ant-louis/belgpt2}},
# }
