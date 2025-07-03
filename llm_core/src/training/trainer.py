import math
import os
import time
from pathlib import Path

import mlflow
import torch
import torch.nn as nn
from loguru import logger
from tqdm import tqdm

from llm_core.src.data.data_loader import DataLoader
from llm_core.src.training.config.model_config import ExperimentConfig


class Trainer:
    def __init__(self, model, optimizer, data_loader: DataLoader, model_config):
        logger.info(f"Trainer: Initializing Trainer")
        self.model: nn.Module = model
        self.optimizer = optimizer
        self.dataloader = data_loader
        self.train_data, self.val_data = data_loader.split(model_config.split_ratio)
        self.model_config: ExperimentConfig = model_config

    @torch.no_grad()
    def estimated_loss(self):

        B, T = self.model_config.batch_size, self.model_config.block_size
        out = {}
        self.model.eval()
        for split, data in [("train", self.train_data), ("val", self.val_data)]:
            losses = torch.zeros(self.model_config.eval_iters)
            for k in range(self.model_config.eval_iters):
                X, Y = self.dataloader.get_batch(B, T, data)
                _, loss = self.model(X, Y)
                losses[k] = loss.item()
            out[split] = losses.mean()
        self.model.train()
        return out

    def _get_lr(self, i):
        max_steps = self.model_config.train_steps
        warmup_steps = int(max_steps * 0.1)
        max_lr = 6e-4
        min_lr = max_lr * 0.1
        if i < warmup_steps:
            return max_lr * (i + 1) / warmup_steps

        if i > max_steps:
            return min_lr

        decay_ratio = (i - warmup_steps) / (max_steps - warmup_steps)
        assert 0 <= decay_ratio <= 1
        coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
        return min_lr + coeff * (max_lr - min_lr)

    def save_checkpoint(self, step):
        Path(self.model_config.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        checkpoint_path = os.path.join(
            self.model_config.checkpoint_dir, f"checkpoint_step_{step}.pt"
        )

        torch.save({
            'step': step,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, checkpoint_path)
        logger.info(f"Checkpoint saved at step {step} → {checkpoint_path}")

    def load_checkpoint(self, checkpoint_path):
        if os.path.isfile(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.model_config.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            start_step = checkpoint['step'] + 1
            logger.info(f"Checkpoint loaded → resuming from step {start_step}")
            return start_step
        else:
            logger.warning(f"No checkpoint found at {checkpoint_path}, starting from scratch.")
            return 0

    def train(self):
        logger.info(f"Trainer: Start Training pipeline")
        B, T = self.model_config.batch_size, self.model_config.block_size
        grad_acc_step = self.model_config.total_batch_GA // (B * T)
        assert grad_acc_step != 0, "grad_acc_step must be greater than 0"

        logger.info(f"Trainer: batch_size {self.model_config.batch_size}, block_size {self.model_config.block_size}")
        logger.info(f"Trainer: number of Gradiant Accumulation Step = {grad_acc_step}")

        # should score and test on mlflow with an wo
        if self.model_config.set_float32_opti:
            torch.set_float32_matmul_precision('high')

        loss_accum = 0.0
        # start_step = self.load_checkpoint("checkpoints/checkpoint_step_500.pt")
        for step in tqdm(range(self.model_config.train_steps)):
            last_step = (step == self.model_config.train_steps - 1)
            t0 = time.time()

            dt_val = 0.
            if step % self.model_config.eval_interval == 0 or last_step:
                t0_val = time.time()
                self.model.eval()
                self.dataloader.current_position['val'] = 0

                with torch.no_grad():
                    val_loss_acc = 0.0

                    for _ in range(self.model_config.eval_iters):
                        x, y = self.dataloader.get_batch(B, T, 'val')
                        x, y = x.to(self.model_config.device), y.to(self.model_config.device)

                        if self.model_config.set_autocast_opti:
                            with torch.autocast(device_type=self.model_config.device, dtype=torch.bfloat16):
                                _, loss = self.model(x, y)
                        else:
                            _, loss = self.model(x, y)
                        loss = loss / self.model_config.eval_iters
                        val_loss_acc += loss.detach()

                val_loss = val_loss_acc / self.model_config.eval_iters
                train_loss = loss_accum / self.model_config.eval_iters
                mlflow.log_metric("val_loss", val_loss, step=step)
                mlflow.log_metric("train_loss", train_loss, step=step)
                if last_step:
                    mlflow.log_metric("final_train_loss", train_loss)
                    mlflow.log_metric("final_val_loss", val_loss)
                loss_accum = 0

                self.model.eval()
                t1_val = time.time()
                dt_val = t1_val - t0_val
                mlflow.log_metric("time validation", dt_val * 1000, step=step)

            self.optimizer.zero_grad(set_to_none=True)
            for micro_step in range(grad_acc_step):
                xb, yb = self.dataloader.get_batch(B, T, 'train')

                # torch opti à check:
                if self.model_config.set_autocast_opti:
                    with torch.autocast(device_type=self.model_config.device, dtype=torch.bfloat16):
                        _, loss = self.model(xb, yb)
                else:
                    _, loss = self.model(xb, yb)
                loss = loss / grad_acc_step
                loss_accum += loss.detach()
                loss.backward()

            norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

            lr = self._get_lr(step)
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = lr

            self.optimizer.step()

            dt_checkpoint = 0.

            if self.model_config.model_checkpoint > 0:
                if step % self.model_config.model_checkpoint == 0 or last_step:
                    t0_check = time.time()
                    self.save_checkpoint(step)
                    t1_check = time.time()
                    dt_checkpoint = t1_check - t0_check

            t1 = time.time()
            torch.cuda.synchronize()
            dt = (t1 - t0) - dt_val - dt_checkpoint

            if step == 0:
                continue
            mlflow.log_metric("time", dt * 1000, step=step)
            mlflow.log_metric("tok/sec", (B * T * grad_acc_step) / dt, step=step)
            mlflow.log_metric("lr", lr, step=step)
            mlflow.log_metric("norm", norm, step=step)
