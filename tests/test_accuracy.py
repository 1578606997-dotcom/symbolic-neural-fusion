import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time

from snf_core import HILCompressor, SNFEngine, SymbolicMemoryMatrix


CASES = [
    ("请分析这份文档并总结要点", "? : $ {b}"),
    ("生成一份项目报告", "! : $"),
    ("把这段文字翻译成英文", "> : $ {e}"),
    ("搜索最近一周的销售数据", "@ : @"),
    ("创建JSON格式的用户反馈总结", "! : @ {s}"),
    ("查询数据库中的错误日志", "@ : @"),
    ("改写这份邮件为中文", "> : $ {z}"),
    ("请用bullet列表输出3个关键点", "! : $ {b} (3)"),
    ("审查这份合同并解释风险", "? : $"),
    ("获取性能指标并生成报告", "! : @"),
]


def test_hil_accuracy_above_80_percent():
    compressor = HILCompressor()

    correct = 0
    for text, expected in CASES:
        actual = compressor.compress(text).hil_symbol
        if actual == expected:
            correct += 1

    accuracy = correct / len(CASES)
    assert accuracy >= 0.8, f"accuracy={accuracy:.2%}, expected >= 80%"


def test_compression_speed_under_1ms_average():
    compressor = HILCompressor()
    payload = "请查询销售数据并生成JSON报告，限制5条"

    rounds = 5000
    start = time.perf_counter()
    for _ in range(rounds):
        compressor.compress(payload)
    avg_ms = (time.perf_counter() - start) / rounds * 1000

    assert avg_ms < 1.0, f"avg compress time {avg_ms:.4f}ms >= 1ms"


def test_engine_and_memory_matrix_flow():
    engine = SNFEngine()
    result = engine.process("请分析用户反馈并用中文输出2个要点")

    assert "current_hil" in result
    assert result["memory_stats"]["total_memories"] == 1
    assert "[上下文记忆]" in result["context_prompt"]
    assert result["current_hil"].startswith("?")

    matrix = SymbolicMemoryMatrix(max_size=2)
    matrix.add(engine.compressor.compress("生成一份报告"))
    matrix.add(engine.compressor.compress("查询关键数据"))
    matrix.add(engine.compressor.compress("改写为英文"))

    assert len(matrix.memories) == 2
    assert matrix.compression_ratio() > 0
    stats = matrix.stats()
    assert stats["max_size"] == 2
    assert stats["memory_size_bytes"] > 0
