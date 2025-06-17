import mlflow
import torch
from mlflow.tracking import MlflowClient

from llm_core.config import EXPERIMENTS_CONFIG_DIR, SAVED_TOKENIZER_DIR, \
    TOKENIZED_DATA_DIR
from llm_core.src.data.data_loader import DataLoader
from llm_core.src.models.gpt import GPTModel
from llm_core.src.tokenizer.bpe_tokenizer import BPETokenizer
from llm_core.src.tokenizer.char_tokenizer import CharTokenizer
from llm_core.src.training.config.model_config import ExperimentConfig
from llm_core.src.training.trainer import Trainer

config = ExperimentConfig(path=f"{EXPERIMENTS_CONFIG_DIR}/experiment_config.yaml")
experiment_name = config.experiment_name
mlflow.set_experiment(experiment_name)

tokenizer_name = config.tokenizer['tokenizer_name']

print(f'tokenizer name : {tokenizer_name}')

tokenizer = CharTokenizer(config.meta['dataset'])
tokenizer = BPETokenizer(tokenizer_name)
# tokenizer = BPETokenizer()
tokenizer.train(config.meta['dataset'], config.tokenizer['vocab_size'])
# tokenizer.save(SAVED_TOKENIZER_DIR / f'{tokenizer_name}.json')


## to factorize in another dataset handler
print(config.to_dict())
# data = torch.tensor(tokenizer.encode(text), dtype=torch.long, device=config.device)

data = DataLoader.fromTokens(type=config.tokenizer['tokenizer_type'], dataset=config.meta['dataset'],
                             vocab_size=config.tokenizer['vocab_size'], device=config.device)

train_data, val_data = data.split(0.8)


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
    mlflow.log_param("tokenized_dataset_file", TOKENIZED_DATA_DIR / f'{tokenizer_name}.pt')
    mlflow.set_tag("tokenizer_path", str(SAVED_TOKENIZER_DIR / f'{tokenizer_name}.json'))
    mlflow.log_artifact(SAVED_TOKENIZER_DIR / f'{tokenizer_name}.json', artifact_path='tokenizer')
    mlflow.log_artifact(EXPERIMENTS_CONFIG_DIR / 'experiment_config.yaml', artifact_path='config')

    trainer.train()

    mlflow.pytorch.log_model(model, config.model_name)
    run_id = mlflow.active_run().info.run_id
    model_uri = f"runs:/{run_id}/{config.model_name}"
    result = mlflow.register_model(model_uri, config.model_name)

    client = MlflowClient()
    client.transition_model_version_stage(
        name=config.model_name,
        version=result.version,
        stage="Staging",
        archive_existing_versions=True
    )

# %%
