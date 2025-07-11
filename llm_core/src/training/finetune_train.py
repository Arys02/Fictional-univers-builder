import mlflow
import torch
from mlflow.tracking import MlflowClient
from loguru import logger
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader

from llm_core.config import EXPERIMENTS_CONFIG_DIR, SAVED_TOKENIZER_DIR, \
    TOKENIZED_DATA_DIR, RAW_DATA_DIR
from llm_core.src.data.finetune_data_loader import FineTuneDataset
from llm_core.src.models.gpt import GPTModel
from llm_core.src.models.gpt2 import GPT2
from llm_core.src.tokenizer.bpe_tokenizer import BPETokenizer
from llm_core.src.tokenizer.char_tokenizer import CharTokenizer
from llm_core.src.tokenizer.transformers_tokenizer import TransformersTokenizer
from llm_core.src.training.config.model_config import ExperimentConfig
from llm_core.src.training.finetune_trainer import FineTuneTrainer
from llm_core.src.training.trainer import Trainer
def collate_fn(batch):
    for idx, item in enumerate(batch):
        assert isinstance(item["input_ids"], torch.Tensor), f"input_ids[{idx}] not tensor but {type(item['input_ids'])}"
        assert isinstance(item["labels"], torch.Tensor), f"labels[{idx}] not tensor but {type(item['labels'])}"

    input_ids = [item["input_ids"] for item in batch]
    labels = [item["labels"] for item in batch]

    input_ids_padded = pad_sequence(input_ids, batch_first=True, padding_value=0)
    labels_padded = pad_sequence(labels, batch_first=True, padding_value=-100)

    return {
        "input_ids": input_ids_padded,
        "labels": labels_padded
    }

config = ExperimentConfig(path=f"{EXPERIMENTS_CONFIG_DIR}/experiment_finetuning_config.yaml")
experiment_name = config.experiment_name
mlflow.set_experiment(experiment_name)
tokenizer_name = config.tokenizer['tokenizer_name']

logger.info(f"Tokenizer name : {tokenizer_name}")

logger.info(f"Configuration json :{config.to_dict()}")

## to opti later
logger.info("Loading dataset...")
tokenizer = TransformersTokenizer()
dataset = FineTuneDataset(RAW_DATA_DIR / "dataset_fiction_local.jsonl", tokenizer)
train_data, val_data = dataset.split(0.2)


train_dataloader = DataLoader(train_data, batch_size=config.batch_size, shuffle=True, collate_fn=collate_fn, drop_last=True)
val_dataloader = DataLoader(val_data, batch_size=config.batch_size, shuffle=False, collate_fn=collate_fn, drop_last=True)

print(f"Taille du dataset de validation : {len(val_data)}")

val_iter = iter(val_dataloader)

try:
    batch_val = next(val_iter)
    print("Premier batch val chargé sans erreur.")
    print("input_ids shape:", batch_val["input_ids"].shape)
    print("labels shape:", batch_val["labels"].shape)
except Exception as e:
    print("Erreur immédiate sur le premier batch val:", e)

try:
    for batch_val in val_dataloader:
        pass
    print("Tous les batchs val chargés sans erreur.")
except Exception as e:
    print("Erreur sur un batch val pendant l'itération:", e)




logger.info("Dataset loaded")

logger.info("Loading model...")
model_uri = f"models:/{config.pretrained_model}/{config.pretrained_model_version}"

model : GPT2 = mlflow.pytorch.load_model(model_uri).to(config.device)
logger.info("Model Loaded")

optimizer = model.configure_optimizers(weight_decay=0.1, learning_rate=6e-4, device_type='cuda')
trainer = FineTuneTrainer(model, optimizer, train_dataloader, val_dataloader, config)

with mlflow.start_run():
    flat_config = {
        **config["model"],
        **config["training"],
        **config["tokenizer"]
    }
    mlflow.log_params(flat_config)

    mlflow.log_param("device", config.device)
    #mlflow.log_param("tokenized_dataset_file", TOKENIZED_DATA_DIR / f'{tokenizer_name}.pt')
    # mlflow.set_tag("tokenizer_path", str(SAVED_TOKENIZER_DIR / f'{tokenizer_name}.json'))
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
