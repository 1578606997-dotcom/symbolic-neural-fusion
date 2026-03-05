import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from snf_core import HILCompressor


def test_comparison_syntax_for_products_and_dimensions():
    compressor = HILCompressor()
    text = "对比产品A和产品B的价格和质量"

    actual = compressor.compress(text).hil_symbol

    assert actual == "@vs(productA,productB){price,quality}"


def test_non_comparison_keeps_original_hil_shape():
    compressor = HILCompressor()

    actual = compressor.compress("请分析这份文档")

    assert actual.hil_symbol == "? : $"
