from tqdm import tqdm

import mlflow

from llm_core.src.training.config.model_config import ExperimentConfig

import torch
import torch.nn as nn


class Trainer:
    def __init__(self, model, optimizer, train_data, val_data, model_config):
        self.model: nn.Module = model
        self.optimizer = optimizer
        self.train_data, self.val_data = train_data, val_data
        self.model_config: ExperimentConfig = model_config

    def get_batch(self, dataset):

        ix = torch.randint(len(dataset) - self.model_config.block_size, (self.model_config.batch_size,))

        xi = [dataset[x:x + self.model_config.block_size] for x in ix]
        yi = [dataset[x + 1:x + self.model_config.block_size + 1] for x in ix]

        x = torch.stack(xi)
        y = torch.stack(yi)
        return x.to(self.model_config.device), y.to(self.model_config.device)

    @torch.no_grad()
    def estimated_loss(self):
        out = {}
        self.model.eval()
        for split, data in [("train",self.train_data), ("val", self.val_data)]:
            losses = torch.zeros(self.model_config.eval_iters)

            for k in range(self.model_config.eval_iters):
                X, Y = self.get_batch(data)
                _, loss = self.model(X, Y)
                losses[k] = loss.item()
            out[split] = losses.mean()
        self.model.train()
        return out

    def train(self):
        for step in tqdm(range(self.model_config.train_steps)):
            xb, yb = self.get_batch(self.train_data)

            self.optimizer.zero_grad(set_to_none=True)
            _, loss = self.model(xb, yb)
            loss.backward()
            self.optimizer.step()

            if step % self.model_config.eval_interval == 0:
                losses = self.estimated_loss()
                print(f"\nstep {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")
                mlflow.log_metric("train_loss", losses["train"], step=step)
                mlflow.log_metric("val_loss", losses["val"], step=step)

        final_losses = self.estimated_loss()
        mlflow.log_metric("final_train_loss", final_losses["train"])
        mlflow.log_metric("final_val_loss", final_losses["val"])

