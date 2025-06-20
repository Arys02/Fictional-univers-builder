#%%
from llm_core.config import EXPERIMENTS_CONFIG_DIR, PROCESSED_DATA_DIR
from llm_core.src.tokenizer.tiktoken_tokenizer import TiktokenTokenizer
from llm_core.src.training.config.model_config import ExperimentConfig

config = ExperimentConfig(path=f"{EXPERIMENTS_CONFIG_DIR}/experiment_config.yaml")

from array import array


#%%
tokenizer_name = config.tokenizer['tokenizer_name']

#%%
tokenizer = TiktokenTokenizer('gpt2')
#%%
dataset_dir = PROCESSED_DATA_DIR
dataset_name = config.meta["dataset"]
#%%
tokenizer.train(config.meta['dataset'], PROCESSED_DATA_DIR, config.tokenizer['vocab_size'])
#%%
from llm_core.config import SAVED_TOKENIZER_DIR

tokenizer.save(SAVED_TOKENIZER_DIR / f"{tokenizer_name}.json") 
#%%
