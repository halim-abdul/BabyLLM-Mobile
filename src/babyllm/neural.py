"""Optional GRU with additive attention for controlled language-model experiments.

PyTorch is imported only when this module is used. This is a research baseline, not
an Android deployment artifact or a pretrained model.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class GRUAttentionLM(nn.Module):
    """Causal next-token model: token embedding -> GRU -> past-only attention."""

    def __init__(self, vocab_size: int, embedding_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        if vocab_size < 2 or embedding_dim < 1 or hidden_dim < 1:
            raise ValueError("model dimensions must be positive and vocab_size >= 2")
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.gru = nn.GRU(embedding_dim, hidden_dim, batch_first=True)
        self.query = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.key = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.value = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.output = nn.Linear(hidden_dim * 2, vocab_size)

    def forward(self, token_ids: Tensor) -> Tensor:
        if token_ids.ndim != 2 or token_ids.shape[1] == 0:
            raise ValueError("token_ids must have shape [batch, nonempty sequence]")
        states, _ = self.gru(self.embedding(token_ids))
        scale = states.shape[-1] ** -0.5
        scores = (self.query(states) @ self.key(states).transpose(1, 2)) * scale
        length = token_ids.shape[1]
        future = torch.ones(length, length, device=token_ids.device, dtype=torch.bool).triu(1)
        weights = scores.masked_fill(future, float("-inf")).softmax(dim=-1)
        attended = weights @ self.value(states)
        return self.output(torch.cat((states, attended), dim=-1))


def training_step(model: GRUAttentionLM, batch: Tensor, optimizer: torch.optim.Optimizer) -> float:
    """One teacher-forced next-token optimization step."""
    if batch.ndim != 2 or batch.shape[1] < 2:
        raise ValueError("batch must have shape [batch, sequence >= 2]")
    model.train()
    optimizer.zero_grad(set_to_none=True)
    logits = model(batch[:, :-1])
    loss = nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), batch[:, 1:].reshape(-1))
    loss.backward()
    optimizer.step()
    return float(loss.detach())
