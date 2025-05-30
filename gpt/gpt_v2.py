import torch
import torch.nn as nn
from torch.nn import functional as F

# hyperparameters
batch_size = 32 # how many independent sequences will we process in parallel?
block_size = 8 # what is the maximum context length for predictions?
max_iters = 5000
eval_interval = 500
learning_rate = 1e-3
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
n_embed = 32
# ------------

torch.manual_seed(1337)

# wget https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# here are all the unique characters that occur in this text
chars = sorted(list(set(text)))
vocab_size = len(chars)
# create a mapping from characters to integers
stoi = { ch:i for i,ch in enumerate(chars) }
itos = { i:ch for i,ch in enumerate(chars) }
encode = lambda s: [stoi[c] for c in s] # encoder: take a string, output a list of integers
decode = lambda l: ''.join([itos[i] for i in l]) # decoder: take a list of integers, output a string

# Train and test splits
data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9*len(data)) # first 90% will be train, rest val
train_data = data[:n]
val_data = data[n:]

# data loading
def get_batch(split):
    # generate a small batch of data of inputs x and targets y
    data = train_data if split == 'train' else val_data
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    x, y = x.to(device), y.to(device)
    return x, y

@torch.no_grad()
def estimate_loss():
    out = {}
    model.eval()
    for split in ['train', 'val']:
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            X, Y = get_batch(split)
            logits, loss = model(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out


class Head(nn.Module):
    """ One headed self attention model."""

    def __init__(self, head_size):
        super().__init__()

        self.key = nn.Linear(n_embed, head_size, bias=False)
        self.query = nn.Linear(n_embed, head_size, bias=False)
        self.value = nn.Linear(n_embed, head_size, bias=False)

        self.register_buffer("trill", torch.tril(torch.ones(block_size, block_size)))


    def forward(self, x):
        B,T,C = x.shape

        k  = self.key(x)   # (B, T, head_size)
        q = self.query(x) # (B, T, head_size)
        
        # Compute atention scores (affinities)
        wei = q @ k.transpose(-2, -1)   * C**-0.5# (B, T, head_size) @ (B, head_size, T) ---> (B, T, (C is normalizing it)
        wei = wei.masked_fill(self.trill[:T, :T] == 0, float('-inf')) # mask out the future tokens
        wei = F.softmax(wei, dim=-1) # (B, T, head_size)
        # perform the weighted aggergation of the values
        v = self.value(x) # (B, T, head_size)
        out = wei @ v # (B, T, head_size) @ (B, head_size, C) ---> (B, T, C)
        return out


class MultiHeadAttention(nn.Module):
    """ A multi-headed self attention model."""

    def __init__(self, num_heads, head_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.proj = nn.Linear(n_embed, n_embed)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1) # (B, T, n_heads * head_size)
        out = self.proj(out) # (B, T, n_embed)
        return out


class FeedForward(nn.Module):
    """ A simple, two-layer feed-forward network."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embed, 4 * n_embed),
            nn.ReLU(),
            nn.Linear(4 * n_embed, n_embed),
        )

    def forward(self, x):
        return self.net(x)


class Block(nn.Module): 
    """ A complete transformer block."""

    def __init__(self, n_embed, n_heads):
        super().__init__()

        head_size = n_embed//n_heads

        self.sa = MultiHeadAttention(n_heads, head_size)
        self.ffwd = FeedForward(n_embed)
        self.ln1 = nn.LayerNorm(n_embed)
        self.ln2 = nn.LayerNorm(n_embed)


    def forward(self, x):
        x = x + self.sa(self.ln1(x)) # (B, T, C)
        x = x + self.ffwd(self.ln2(x)) # (B, T, C)
        return x
    

# super simple bigram model
class BigramLanguageModel(nn.Module):

    def __init__(self):
        super().__init__()
        # each token directly reads off the logits for the next token from a lookup table
        self.token_embedding_table = nn.Embedding(vocab_size, n_embed) # n_embed is the dimensionality of the embeddings
        self.position_embedding_table = nn.Embedding(block_size, n_embed) # n_embed is the dimensionality of the embeddings
        self.lm_head = nn.Linear(n_embed, vocab_size) # vocab_size is the size of the output vocabulary
        
        # ## for single headed self attention
        # # self.sa_heads = Head(n_embed)

        # ## For multi headed
        # self.sa_heads = MultiHeadAttention(4, n_embed//4)  # 4 heads, each with 8 dimensionality self attention ( n_embed//4 )
 
        # ## Feed forward nn
        # self.ffwd = FeedForward(n_embed)

        self.blocks = nn.Sequential(
            Block(n_embed, n_heads=4), # 4 transformer blocks
            Block(n_embed, n_heads=4),
            Block(n_embed, n_heads=4),
            nn.LayerNorm(n_embed)
        )



    def forward(self, idx, targets=None):
        B, T = idx.shape

        # idx and targets are both (B,T) tensor of integers
        token_emb = self.token_embedding_table(idx) # (B,T,C)
        pos_emb = self.position_embedding_table(torch.arange(T, device=device)) # (B,T,n_embed)
        x = token_emb + pos_emb # (B,T,C)
        
        # x = self.sa_heads(x) # (B,T,C) Applying self attention head to the embeddings
        
        # x = self.ffwd(x) # (B,T,C) Applying feed forward network to the embeddings
        
        x = self.blocks(x) # (B,T,C) Applying all transformer blocks to the embeddings

        logits = self.lm_head(x) # (B,T,vocab_size)

        if targets is None:
            loss = None
        else:
            B, T, C = logits.shape
            logits = logits.view(B*T, C)
            targets = targets.view(B*T)
            loss = F.cross_entropy(logits, targets)

        return logits, loss

    def generate(self, idx, max_new_tokens):
        # idx is (B, T) array of indices in the current context
        for _ in range(max_new_tokens):
            # Crop idx to the kast block_size tokens
            idx_cond = idx[:, -block_size:] # becomes (B, block_size)
            # get the predictions
            # logits, loss = self(idx)
            logits, loss = self(idx_cond)
            # focus only on the last time step
            logits = logits[:, -1, :] # becomes (B, C)
            # apply softmax to get probabilities
            probs = F.softmax(logits, dim=-1) # (B, C)
            # sample from the distribution
            idx_next = torch.multinomial(probs, num_samples=1) # (B, 1)
            # append sampled index to the running sequence
            idx = torch.cat((idx, idx_next), dim=1) # (B, T+1)
        return idx

model = BigramLanguageModel()
m = model.to(device)

# create a PyTorch optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

for iter in range(max_iters):

    # every once in a while evaluate the loss on train and val sets
    if iter % eval_interval == 0:
        losses = estimate_loss()
        print(f"step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

    # sample a batch of data
    xb, yb = get_batch('train')

    # evaluate the loss
    logits, loss = model(xb, yb)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

# generate from the model
context = torch.zeros((1, 1), dtype=torch.long, device=device)
print(decode(m.generate(context, max_new_tokens=500)[0].tolist()))