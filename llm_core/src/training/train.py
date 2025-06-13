from llm_core.config import RAW_DATA_DIR, EXPERIMENTS_CONFIG_DIR, SAVED_MODEL_DIR, SAVED_TOKENIZER_DIR
from llm_core.src.models.gpt import GPTModel
from llm_core.src.tokenizer.bpe_tokenizer import BPETokenizer
from llm_core.src.training.config.model_config import ExperimentConfig
from llm_core.src.training.trainer import Trainer
import torch
import mlflow

from llm_core.src.utils.load_config import load_config

with open(RAW_DATA_DIR / 'sheakspear_input.txt', 'r', encoding='utf-8') as f:
    text = f.read()


config = ExperimentConfig(path=f"{EXPERIMENTS_CONFIG_DIR}/experiment_config.yaml")
from llm_core.src.tokenizer.char_tokenizer import CharTokenizer

chars = sorted(list(set(text)))
vocab_size = len(chars)

#tokenizer = CharTokenizer(chars)
tokenizer = BPETokenizer()
tokenizer.train(text, config.tokenizer['vocab_size'])
tokenizer.save(SAVED_TOKENIZER_DIR / 'tokenizer_sheakspear_8192.json')


experiment_name = config.experiment_name

mlflow.set_experiment(experiment_name)

## to factorize in another dataset handler
print(config.device)
print(config)
data = torch.tensor(tokenizer.encode(text), dtype=torch.long, device=config.device)

n = int(len(data) * 0.9)
train_data = data[:n]
val_data = data[n:]


model = GPTModel(config).to(config.device)

optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
trainer = Trainer(model, optimizer, train_data, val_data, config)


with mlflow.start_run():

    flat_config = {
        **config["model"],
        **config["training"],
        **config["tokenizer"]
    }
    mlflow.log_params(flat_config)

    mlflow.log_param("device", config.device)
    trainer.train()

    mlflow.pytorch.log_model(model, config.model_name)
