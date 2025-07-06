import torch
from torch.utils.data import Dataset
import json
from llm_core.src.tokenizer.transformers_tokenizer import TransformersTokenizer
from loguru import logger

class FineTuneDataset(Dataset):
    def __init__(self, path: str, tokenizer: TransformersTokenizer, max_length: int = 512):
        self.samples = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with open(path, 'r', encoding='utf-8') as f:
            i = 0
            for line in f:
                i+=1
                item = json.loads(line)

                prompt = f"""Voici des extraits de documentation existante :
{item['context']}
Question : {item['question']}
Si la réponse se trouve dans les extraits, utilise-les strictement. Sinon, génère une réponse cohérente pour compléter l'univers."""

                prompt_ids = tokenizer.encode(prompt)
                answer_ids = tokenizer.encode(item['answer'])

                # Concatène et tronque ensemble
                input_ids = (prompt_ids + answer_ids)[:self.max_length]

                labels = [-100] * len(prompt_ids)
                answer_truncated = input_ids[len(prompt_ids):]  # assure qu’on reste dans max_length
                labels += answer_truncated
                labels = labels[:self.max_length]

                self.samples.append({
                    "input_ids": torch.tensor(input_ids, dtype=torch.long),
                    "labels": torch.tensor(labels, dtype=torch.long)
                })


    def split(self, val_size):
        logger.info(f"FineTuneDataLoader: Splitting data with x{val_size} elements")
        assert self.samples is not None, 'FineTuneDataLoader has not been initialized'

        n = int(len(self.samples) * val_size)

        val_size = n
        train_size = len(self.samples) - n

        for idx, sample in enumerate(self.samples):
            assert isinstance(sample["input_ids"], torch.Tensor), f"sample {idx} input_ids not tensor"
            assert isinstance(sample["labels"], torch.Tensor), f"sample {idx} labels not tensor"

        train_data, val_data = torch.utils.data.random_split(self, [train_size, val_size])
        return train_data, val_data

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]
