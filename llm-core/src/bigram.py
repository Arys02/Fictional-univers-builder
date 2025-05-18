import torch
import torch.nn as nn
from tqdm import tqdm

from torch.nn import functional as F

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(4242)
block_size = 8
batch_size = 34
eval_iters = 200
eval_interval = 100
n_embedding = 32
print(f"Device: {device}")


## maybe a abstract class for decoder/encoder

def encode(alphabet, s):
    stoi = {ch: i for i, ch in enumerate(alphabet)}
    return [stoi[c] for c in s]


def decode(alphabet, s):
    itos = {i: ch for i, ch in enumerate(alphabet)}
    return ''.join(itos[c] for c in s)


def get_batch(dataset):
    ix = torch.randint(len(dataset) - block_size, (batch_size,))

    xi = [dataset[x:x + block_size] for x in ix]
    yi = [dataset[x + 1:x + block_size + 1] for x in ix]

    x = torch.stack(xi)
    y = torch.stack(yi)
    return x, y


class BigramLanguageModel(nn.Module):
    def __init__(self, vocab_size, n_embd):
        super().__init__()
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx, target=None):
        B, T = idx.shape
        tok_emb = self.token_embedding_table(idx)
        pos_emb = self.position_embedding_table(torch.arange(T, device=device))
        x = tok_emb + pos_emb
        logits = self.lm_head(x) # (B, T, vocab_size)

        if target is not None:
            B, T, C = logits.shape

            logits = logits.view(B * T, C)
            targets = target.view(B * T)

            loss = F.cross_entropy(logits, targets)
        else:
            loss = None

        return logits, loss

    def generate(self, idx, max_new_token: int):
        for _ in range(max_new_token):
            logits, loss = self(idx)
            logits = logits[:, -1, :]

            probs = F.softmax(logits, dim=-1)

            id_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, id_next), dim=1)
        return idx

    def train_model(self, dataset, val_dataset, steps, optimizer):
        xb, yb = get_batch(dataset)
        for step in tqdm(range(steps)):


            optimizer.zero_grad(set_to_none=True)
            logits, loss = self.forward(xb, yb)
            loss.backward()
            optimizer.step()

            if step % (steps *0.1)== 0:
                losses = self.estimated_loss(dataset, val_dataset)
                print(f"\nstep {iter}: train loss {losses[0]:.4f}, val loss {losses[1]:.4f}")

    def generate_text(self, max_new_token, alphabet):
        return decode(alphabet, self.generate(torch.zeros((1, 1), dtype=torch.long, device=device), max_new_token)[0].tolist())

    @torch.no_grad()
    def estimated_loss(self, ds_train, ds_val):
        out = {}
        self.eval()
        for i, ds in enumerate([ds_train, ds_val]):
            losses = torch.zeros(eval_iters)


            for k in range(eval_iters):
                X, Y = get_batch(ds)
                logits, loss = self.forward(X, Y)
                losses[k] = loss.item()
            out[i] = losses.mean()
        self.train()
        return out

if __name__ == '__main__':
    with open('../data/raw/sheakspear_input.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    chars = sorted(list(set(text)))
    vocab_size = len(chars)

    print(encode(chars, "hello world"))
    print(decode(chars, [46, 43, 50, 50, 53, 1, 61, 53, 56, 50, 42]))

    # on encode le texte du dataset et on le met dans un tensor
    data = torch.tensor(encode(chars, text), dtype=torch.long, device=device)

    n = int(len(data) * 0.9)
    ds_train = data[:n]
    ds_test = data[n:]

    m = BigramLanguageModel(vocab_size, n_embedding ).to(device)
    optimizer = torch.optim.Adam(m.parameters(), lr=0.001)
    print(m.generate_text(500, chars))

    m.train_model(ds_train, ds_test, 10000, optimizer)
    print(m.generate_text(500, chars))


