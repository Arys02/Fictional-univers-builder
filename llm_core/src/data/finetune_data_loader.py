import torch
from torch.utils.data import Dataset
import json
from pathlib import Path
from llm_core.src.tokenizer.transformers_tokenizer import TransformersTokenizer

class FineTuneDataset(Dataset):
    def __init__(self, path: str, tokenizer: TransformersTokenizer, max_length: int = 512):
        self.samples = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)

                prompt = f"""Voici des extraits de documentation existante :

{item['context']}

Question : {item['question']}
Si la réponse se trouve dans les extraits, utilise-les strictement. Sinon, génère une réponse cohérente pour compléter l'univers."""

                full_text = prompt + "\n" + item['answer']
                input_ids = tokenizer.encode(full_text)[:max_length]
                prompt_len = len(tokenizer.encode(prompt))

                labels = [-100] * prompt_len + input_ids[prompt_len:]
                labels = labels[:max_length]

                self.samples.append({
                    "input_ids": torch.tensor(input_ids, dtype=torch.long),
                    "labels": torch.tensor(labels, dtype=torch.long)
                })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]
