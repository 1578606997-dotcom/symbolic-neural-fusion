import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from snf_core import SymbolicMemory, SymbolicMemoryMatrix


def test_symbolic_memory_to_dict_truncates_raw_text_over_100_chars():
    raw_text = "x" * 120
    memory = SymbolicMemory(
        timestamp=123.45,
        hil_symbol="? : $",
        raw_text=raw_text,
        intent={"action": "?"},
    )

    data = memory.to_dict()

    assert data["timestamp"] == 123.45
    assert data["hil"] == "? : $"
    assert data["raw"] == ("x" * 100) + "..."
    assert data["intent"] == {"action": "?"}


def test_symbolic_memory_to_dict_keeps_short_raw_text_intact():
    memory = SymbolicMemory(
        timestamp=1.0,
        hil_symbol="! : $",
        raw_text="short text",
        intent={"object": "$"},
    )

    data = memory.to_dict()

    assert data["raw"] == "short text"


def test_symbolic_memory_matrix_fifo_and_window_behavior():
    matrix = SymbolicMemoryMatrix(max_size=2)

    matrix.add(SymbolicMemory(1.0, "a", "text1", {}))
    matrix.add(SymbolicMemory(2.0, "b", "text2", {}))
    matrix.add(SymbolicMemory(3.0, "c", "text3", {}))

    # FIFO: 最早记录应被淘汰
    assert [m.hil_symbol for m in matrix.memories] == ["b", "c"]
    assert [m.hil_symbol for m in matrix.get_context(window_size=1)] == ["c"]


def test_symbolic_memory_matrix_empty_state_boundaries():
    matrix = SymbolicMemoryMatrix()

    assert matrix.get_context() == []
    assert matrix.to_prompt() == ""
    assert matrix.compression_ratio() == 0.0

    stats = matrix.stats()
    assert stats["total_memories"] == 0
    assert stats["memory_size_bytes"] == 0


def test_symbolic_memory_matrix_stats_and_prompt_content():
    matrix = SymbolicMemoryMatrix(max_size=5)
    matrix.add(SymbolicMemory(1.0, "? : $", "请分析报告", {"action": "?"}))
    matrix.add(SymbolicMemory(2.0, "! : $", "生成总结", {"action": "!"}))

    prompt = matrix.to_prompt(window_size=5)
    stats = matrix.stats()

    assert "[上下文记忆]" in prompt
    assert "1. ? : $" in prompt
    assert "2. ! : $" in prompt
    assert "[当前任务]" in prompt

    assert stats["total_memories"] == 2
    assert stats["max_size"] == 5
    assert stats["compression_ratio"] > 0

    # 覆盖 to_dict() 序列化路径
    payload = json.dumps([m.to_dict() for m in matrix.memories], ensure_ascii=False)
    assert "请分析报告" in payload
