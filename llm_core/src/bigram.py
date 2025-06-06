import torch
import torch.nn as nn
from torch.nn import functional as F

from llm_core.tokenizer.char_tokenizer import CharTokenizer

from tqdm import tqdm

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(4242)
block_size = 36
batch_size = 8
eval_iters = 200
eval_interval = 100
n_embedding =  50# embeddings
n_layers = 6
dropout = 0.2
n_heads = 6
print(f"Device: {device}")


## maybe a abstract class for decoder/encoder


def get_batch(dataset):
    ix = torch.randint(len(dataset) - block_size, (batch_size,))

    xi = [dataset[x:x + block_size] for x in ix]
    yi = [dataset[x + 1:x + block_size + 1] for x in ix]

    x = torch.stack(xi)
    y = torch.stack(yi)
    return x, y


class FeedForwardNet(nn.Module):
    def __init__(self, n_embd):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),  # on multiplie par 4 c'est ce qu'ils font dans le papier
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class Head(nn.Module):
    ## one head of self-attention
    def __init__(self, block_size, n_embd, head_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape

        k = self.key(x)
        q = self.query(x)

        kq = q @ k.transpose(-2, -1) * C ** -0.5
        kq = kq.masked_fill(self.tril[:T, :T] == 0, float('-inf'))
        kq = F.softmax(kq, dim=-1)
        kq = self.dropout(kq)

        v = self.value(x)
        attention = kq @ v
        return attention


class MultiHeadAttention(nn.Module):
    def __init__(self, block_size, n_embd, head_size, num_heads):
        super().__init__()
        self.heads = nn.ModuleList([Head(block_size, n_embd, head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(head_size * num_heads, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        out = self.proj(out)
        out = self.dropout(out)

        return out


class Block(nn.Module):
    def __init__(self, n_embd, n_head, block_size):
        super().__init__()
        head_size = n_embd // n_head
        self.sa_heads = MultiHeadAttention(block_size, n_embd, head_size, n_head)
        self.fwd = FeedForwardNet(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa_heads.forward(x)
        x = x + self.fwd.forward(x)
        return x


class GPTModel(nn.Module):
    def __init__(self, vocab_size, n_embd):
        super().__init__()
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(*[Block(n_embd, n_head=n_heads, block_size=block_size) for _ in range(n_layers)])
        self.ln1 = nn.LayerNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
    def forward(self, idx, target=None):
        B, T = idx.shape
        tok_emb = self.token_embedding_table(idx)
        pos_emb = self.position_embedding_table(torch.arange(T, device=device))  # (T, C)
        x = tok_emb + pos_emb  # (B, T, C)
        x = self.blocks(x)
        x = self.ln1(x)
        logits = self.lm_head(x)  # (B, T, vocab_size)

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
            idx_cond = idx[:, -block_size:]
            logits, loss = self.forward(idx_cond)
            logits = logits[:, -1, :]

            probs = F.softmax(logits, dim=-1)

            id_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, id_next), dim=1)
        return idx

    def train_model(self, train_dataset, val_dataset, steps, optimizer):
        for step in tqdm(range(steps)):
            xb, yb = get_batch(train_dataset)

            optimizer.zero_grad(set_to_none=True)
            logits, loss = self.forward(xb, yb)
            loss.backward()
            optimizer.step()

            if step % (steps * 0.1) == 0:
                losses = self.estimated_loss(train_dataset, val_dataset)
                print(f"\nstep {iter}: train loss {losses[0]:.4f}, val loss {losses[1]:.4f}")

    def generate_text(self, max_new_token, encoder):
        return encoder.decode(
                      self.generate(torch.zeros((1, 1), dtype=torch.long, device=device), max_new_token)[0].tolist())

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

    tokenizer = CharTokenizer()
    t = CharTokenizer(chars)

    print(t.encode("hello world"))
    print(t.decode([46, 43, 50, 50, 53, 1, 61, 53, 56, 50, 42]))

    # on encode le texte du dataset et on le met dans un tensor
    data = torch.tensor(t.encode( text), dtype=torch.long, device=device)

    n = int(len(data) * 0.9)
    ds_train = data[:n]
    ds_test = data[n:]

    m = GPTModel(vocab_size, n_embedding).to(device)
    optimizer = torch.optim.Adam(m.parameters(), lr=0.001)
    print(m.generate_text(500, t))

    m.train_model(ds_train, ds_test, 10000, optimizer)
    print("post train : ")
    print(m.generate_text(500, t))
