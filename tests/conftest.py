"""
Pytest configuration for SNF tests
共享 fixtures 和路径设置
"""

import sys
from pathlib import Path

# 将项目根目录添加到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# 导出供测试使用的公共 fixtures
import pytest
from snf_core import SymbolicMemory, SymbolicMemoryMatrix, HILCompressor, SNFEngine


@pytest.fixture
def compressor():
    """提供 HILCompressor 实例"""
    return HILCompressor()


@pytest.fixture
def engine():
    """提供 SNFEngine 实例"""
    return SNFEngine()


@pytest.fixture
def sample_memory():
    """提供示例 SymbolicMemory"""
    return SymbolicMemory(
        timestamp=1234567890.0,
        hil_symbol="? : $",
        raw_text="分析文档",
        intent={"action": "?", "object": "$"}
    )


@pytest.fixture
def empty_matrix():
    """提供空的 SymbolicMemoryMatrix"""
    return SymbolicMemoryMatrix(max_size=10)


@pytest.fixture
def filled_matrix():
    """提供填充了数据的 SymbolicMemoryMatrix"""
    matrix = SymbolicMemoryMatrix(max_size=5)
    for i in range(3):
        matrix.add(SymbolicMemory(
            timestamp=float(i),
            hil_symbol=f"action{i}",
            raw_text=f"text{i}",
            intent={}
        ))
    return matrix
