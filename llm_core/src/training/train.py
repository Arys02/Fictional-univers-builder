from llm_core.config import RAW_DATA_DIR, EXPERIMENTS_CONFIG_DIR, SAVED_MODEL_DIR, SAVED_TOKENIZER_DIR, PROCESSED_DATA_DIR, TOKENIZED_DATA_DIR
from llm_core.src.models.gpt import GPTModel
from mlflow.tracking import MlflowClient
from llm_core.src.tokenizer.bpe_tokenizer import BPETokenizer
from llm_core.src.training.config.model_config import ExperimentConfig
from llm_core.src.training.trainer import Trainer
import torch
import mlflow

from llm_core.src.utils.load_config import load_config

with open(RAW_DATA_DIR / 'sheakspear_input.txt', 'r', encoding='utf-8') as f:
    text = f.read()


config = ExperimentConfig(path=f"{EXPERIMENTS_CONFIG_DIR}/experiment_config.yaml")
experiment_name = config.experiment_name
mlflow.set_experiment(experiment_name)


chars = sorted(list(set(text)))
vocab_size = len(chars)
tokenizer_name = "tokenizer_" + config.tokenizer['tokenizer_type'] + '_' + config.meta['dataset'] + '_' + str(config.tokenizer['vocab_size'])
print(f'tokenizer name : {tokenizer_name}')

#tokenizer = CharTokenizer(chars)
tokenizer = BPETokenizer(SAVED_TOKENIZER_DIR / f'{tokenizer_name}.json')
# tokenizer = BPETokenizer()
# tokenizer.train(text, config.tokenizer['vocab_size'])
# tokenizer.save(SAVED_TOKENIZER_DIR / f'{tokenizer_name}.json')



## to factorize in another dataset handler
print(config.to_dict())
#data = torch.tensor(tokenizer.encode(text), dtype=torch.long, device=config.device)

data = torch.load(TOKENIZED_DATA_DIR / f'{tokenizer_name}.pt').to(config.device)

n = int(len(data) * 0.8)
train_data = data[:n]
val_data = data[n:]

#%%

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

#%%
