import pytest

from babyllm.evaluation import evaluate_next_token
from babyllm.ingest import ingest_file, read_text
from babyllm.memory import NGramMemory, tokenize


def test_unicode_tokenization():
    assert tokenize("Hola, 世界! café") == ["Hola", ",", "世界", "!", "café"]


def test_incremental_counts_and_persistence(tmp_path):
    path = tmp_path / "memory.sqlite3"
    with NGramMemory(path) as memory:
        assert memory.learn("hello world", document_id="doc-1") == 2
        assert memory.learn("hello world", document_id="doc-1") == 0
        assert memory.learn("hello there", document_id="doc-2") == 2
        assert memory.candidates(["<s>", "hello"])[0] == ("there", 0.5)
        assert memory.statistics()["documents"] == 2
    with NGramMemory(path) as memory:
        assert memory.statistics()["observed_tokens"] == 6


def test_completion_and_held_out_evaluation():
    with NGramMemory() as memory:
        memory.learn("hello world")
        assert memory.complete("hello", max_tokens=5) == "world"
        result = evaluate_next_token(memory, ["hello world"])
        assert result["tokens"] == 3
        assert result["top1_accuracy"] == 1.0


def test_html_ingestion_is_explicit_and_deduplicated(tmp_path):
    path = tmp_path / "page.html"
    path.write_text("<style>hide</style><p>hello world</p><script>ignore</script>", encoding="utf-8")
    assert read_text(path).strip() == "hello world"
    with NGramMemory() as memory:
        assert ingest_file(memory, path) == 2
        assert ingest_file(memory, path) == 0


def test_invalid_inputs():
    with pytest.raises(ValueError):
        NGramMemory(order=0)
    with NGramMemory() as memory:
        with pytest.raises(ValueError):
            memory.complete("", max_tokens=-1)
