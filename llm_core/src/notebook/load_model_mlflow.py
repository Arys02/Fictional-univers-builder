import mlflow
import torch

#%%
from llm_core.config import MLFLOW_PATH
from llm_core.src.tokenizer.transformers_tokenizer import TransformersTokenizer

print("Tracking URI:", mlflow.get_tracking_uri())
#%%
experiments = mlflow.search_experiments()
for exp in experiments:
    print(f"ID: {exp.experiment_id} - Name: {exp.name}")
#%%
runs = mlflow.search_runs(experiment_ids=["0"])

print("Tous les run_id disponibles dans l'expérience 0 :")
for rid in runs["run_id"]:
    print("-", rid)
#%%
from llm_core.src.models.gpt2 import GPT2
from llm_core.src.models.gpt import GPTModel

experiment_id = "494534413940730003"
run_id = "98f938de200d4310b9ea8d3f0d17c067"
model : GPT2 = mlflow.pytorch.load_model(f"{MLFLOW_PATH}/{experiment_id}/{run_id}/artifacts/gpt2")
#%%
from llm_core.config import RAW_DATA_DIR, SAVED_TOKENIZER_DIR

tokenizer = TransformersTokenizer()

#%%
print(model.generate_text(500, tokenizer))
#%%
