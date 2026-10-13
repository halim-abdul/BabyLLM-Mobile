import pytest

torch = pytest.importorskip("torch")
from babyllm.neural import GRUAttentionLM, training_step


def test_causal_attention_and_training_step():
    torch.manual_seed(0)
    model = GRUAttentionLM(vocab_size=8, embedding_dim=4, hidden_dim=6)
    a = torch.tensor([[1, 2, 3, 4]])
    b = torch.tensor([[1, 2, 7, 6]])
    model.eval()
    with torch.no_grad():
        assert torch.allclose(model(a)[:, :2], model(b)[:, :2], atol=1e-6)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    assert training_step(model, a, optimizer) > 0
