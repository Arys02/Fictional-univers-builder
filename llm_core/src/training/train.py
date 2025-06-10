from llm_core.config import RAW_DATA_DIR, EXPERIMENTS_CONFIG_DIR
from llm_core.src.models.gpt import GPTModel
from llm_core.src.training.trainer import Trainer
import torch
import mlflow

from llm_core.src.utils.load_config import load_config

with open(RAW_DATA_DIR / 'sheakspear_input.txt', 'r', encoding='utf-8') as f:
    text = f.read()


from llm_core.src.training.model_config import ExperimentConfig
from llm_core.src.tokenizer.char_tokenizer import CharTokenizer

chars = sorted(list(set(text)))
vocab_size = len(chars)

tokenizer = CharTokenizer(chars)

config = ExperimentConfig(path=f"{EXPERIMENTS_CONFIG_DIR}/experiment_config.yaml")

## to factorize in another dataset handler
data = torch.tensor(tokenizer.encode(text), dtype=torch.long, device=config.device)
n = int(len(data) * 0.9)
train_data = data[:n]
val_data = data[n:]


model = GPTModel(config).to(config.device)

optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
trainer = Trainer(model, optimizer, train_data, val_data, config)


with mlflow.start_run():
    mlflow.log_param('vocab_size', vocab_size)
    mlflow.log_param("n_layers", config.n_layers)
    mlflow.log_param("n_head", config.n_head)
    mlflow.log_param("embedding_dim", config.n_embd)
    mlflow.log_param("block_size", config.block_size)
    mlflow.log_param("batch_size", config.batch_size)
    mlflow.log_param("learning_rate", config.lr)
    mlflow.log_param("tokenizer", "char")
    mlflow.log_param("dropout", config.dropout)
    mlflow.log_param("train_steps", config.train_steps)
    mlflow.log_param("device", config.device)
    trainer.train()

    mlflow.pytorch.log_model(model, "model_0.1")
