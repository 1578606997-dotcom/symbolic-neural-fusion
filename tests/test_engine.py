import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from snf_core import HILCompressor, SNFEngine


def test_hil_compressor_extracts_action_object_modifier_and_limit():
    compressor = HILCompressor()

    memory = compressor.compress("请创建JSON格式的用户反馈总结，输出3个要点")

    assert memory.hil_symbol == "! : @ {b,s} (3)"
    assert memory.intent["action"] == "!"
    assert memory.intent["object"] == "@"
    assert memory.intent["constraints"]["limit"] == 3


def test_hil_compressor_builds_vs_syntax_for_comparison_query():
    compressor = HILCompressor()

    memory = compressor.compress("对比产品A和产品B的价格和质量")

    assert memory.hil_symbol == "@vs(productA,productB){price,quality}"
    assert memory.intent["comparison"] == {
        "entities": ["productA", "productB"],
        "dimensions": ["price", "quality"],
    }


def test_hil_compressor_falls_back_when_comparison_info_incomplete():
    compressor = HILCompressor()

    memory = compressor.compress("对比产品A和产品B")

    assert memory.intent["comparison"] is None
    assert memory.hil_symbol == "? : $"


def test_engine_process_returns_expected_shape_and_updates_memory():
    engine = SNFEngine()

    result = engine.process("请分析用户反馈并用中文输出2个要点")

    assert set(result.keys()) == {"current_hil", "context_prompt", "memory_stats", "full_context"}
    assert result["memory_stats"]["total_memories"] == 1
    assert "[上下文记忆]" in result["context_prompt"]


def test_engine_accumulates_context_over_multiple_turns():
    engine = SNFEngine()

    engine.process("生成一份周报")
    engine.process("查询数据库日志")
    final = engine.process("改写成英文")

    assert final["memory_stats"]["total_memories"] == 3
    assert "1." in final["context_prompt"]
    assert "2." in final["context_prompt"]
    assert "3." in final["context_prompt"]


def test_engine_full_context_contains_intent_json_and_stats():
    engine = SNFEngine()

    result = engine.process("对比产品A和产品B的价格和质量")

    full_context = result["full_context"]
    assert "=== SNF 符号神经融合上下文 ===" in full_context
    assert "[当前输入 HIL]: @vs(productA,productB){price,quality}" in full_context
    assert "[原始意图]:" in full_context
    assert "[统计]: 压缩率" in full_context

    # 验证原始意图包含 comparison 字段
    assert '"comparison"' in full_context
    parsed_stats = result["memory_stats"]
    assert parsed_stats["memory_size_bytes"] > 0

    # 确认 JSON 可序列化
    json.dumps(result, ensure_ascii=False)

from snf_core import (
    test_compression as run_demo_compression,
    test_long_context_retention as run_demo_long_context_retention,
)


def test_hil_compressor_entity_fallback_with_bijiao_keyword():
    compressor = HILCompressor()

    entities = compressor._extract_entities_for_comparison("比较方案A与方案B的性能")

    assert entities == ["方案A", "方案B"]


def test_hil_compressor_dimensions_support_extended_keywords():
    compressor = HILCompressor()

    dims = compressor._extract_dimensions_for_comparison("对比产品X和产品Y的成本、功能和服务")

    assert dims == ["price", "feature", "service"]


def test_hil_compressor_predict_label_returns_default_on_no_match():
    compressor = HILCompressor()

    label = compressor._predict_label("完全无关输入", compressor.action_features, default="?")

    assert label == "?"


def test_demo_functions_execute_without_error_and_return_engine():
    engine = run_demo_compression()
    run_demo_long_context_retention()

    assert hasattr(engine, "process")
