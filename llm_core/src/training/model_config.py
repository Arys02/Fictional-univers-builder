import torch


class ModelConfig:
    block_size = 36
    batch_size = 8
    n_embd = 50
    n_layers = 6
    n_head = 6
    dropout = 0.2
    vocab_size = None
    train_steps = 1000
    eval_iters = 200
    eval_interval = 50
    lr = 1e-3
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
