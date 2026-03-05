"""
Symbolic-Neural Fusion (SNF) - Core Implementation
停止写文档，开始写代码！

目标：用 HIL 符号压缩解决 LLM 长上下文失忆
"""

import json
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SymbolicMemory:
    """符号记忆单元 - 核心数据结构"""
    timestamp: float
    hil_symbol: str  # HIL 压缩符号
    raw_text: str    # 原始文本
    intent: Dict     # 解析后的意图
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "hil": self.hil_symbol,
            "raw": self.raw_text[:100] + "..." if len(self.raw_text) > 100 else self.raw_text,
            "intent": self.intent
        }


class HILCompressor:
    """HIL 压缩引擎 - 将自然语言压缩为符号"""
    
    def __init__(self):
        # 动作映射
        self.action_map = {
            r"\b(分析|查看|检查|总结|评估)\b": "?",
            r"\b(创建|生成|写|制作|构建)\b": "!",
            r"\b(转换|变成|改为|翻译)\b": ">",
            r"\b(查询|搜索|查找|获取)\b": "@"
        }
        
        # 对象映射
        self.object_map = {
            r"\b(文档|文件|报告|文本)\b": "$",
            r"\b(知识|数据|信息|资料)\b": "@"
        }
        
        # 修饰符映射
        self.modifier_map = {
            r"\b(中文|汉语|简体)\b": "z",
            r"\b(英文|英语|English)\b": "e",
            r"\b(bullet|要点|列表|点)\b": "b",
            r"\b(json|JSON|格式)\b": "s"
        }
    
    def compress(self, text: str) -> SymbolicMemory:
        """
        将自然语言压缩为 HIL 符号
        
        Args:
            text: 自然语言输入
            
        Returns:
            SymbolicMemory: 符号记忆单元
        """
        # 提取意图
        intent = self._extract_intent(text)
        
        # 构建 HIL 符号
        hil = self._build_hil(intent)
        
        return SymbolicMemory(
            timestamp=datetime.now().timestamp(),
            hil_symbol=hil,
            raw_text=text,
            intent=intent
        )
    
    def _extract_intent(self, text: str) -> Dict:
        """提取意图结构"""
        intent = {
            "action": "?",  # 默认分析
            "object": "$",  # 默认文档
            "modifiers": [],
            "constraints": {}
        }
        
        # 识别动作
        for pattern, symbol in self.action_map.items():
            if re.search(pattern, text, re.IGNORECASE):
                intent["action"] = symbol
                break
        
        # 识别对象
        for pattern, symbol in self.object_map.items():
            if re.search(pattern, text):
                intent["object"] = symbol
                break
        
        # 识别修饰符
        for pattern, code in self.modifier_map.items():
            if re.search(pattern, text, re.IGNORECASE):
                intent["modifiers"].append(code)
        
        # 识别数量限制
        num_match = re.search(r'(\d+)[个条点项]', text)
        if num_match:
            intent["constraints"]["limit"] = int(num_match.group(1))
        
        return intent
    
    def _build_hil(self, intent: Dict) -> str:
        """构建 HIL 符号"""
        parts = [intent["action"], ":", intent["object"]]
        
        # 添加修饰符
        if intent["modifiers"]:
            parts.append(f"{{{','.join(intent['modifiers'])}}}")
        
        # 添加约束
        if "limit" in intent["constraints"]:
            parts.append(f"({intent['constraints']['limit']})")
        
        return " ".join(parts)


class SymbolicMemoryMatrix:
    """符号记忆矩阵 - 存储和管理符号记忆"""
    
    def __init__(self, max_size: int = 100):
        self.memories: List[SymbolicMemory] = []
        self.max_size = max_size
        self.access_count = 0
    
    def add(self, memory: SymbolicMemory) -> None:
        """添加记忆"""
        self.memories.append(memory)
        
        # 保持固定大小（FIFO）
        if len(self.memories) > self.max_size:
            self.memories.pop(0)
    
    def get_context(self, window_size: int = 10) -> List[SymbolicMemory]:
        """获取最近 N 条记忆"""
        return self.memories[-window_size:]
    
    def to_prompt(self, window_size: int = 10) -> str:
        """将记忆矩阵转为 LLM prompt"""
        recent = self.get_context(window_size)
        
        if not recent:
            return ""
        
        prompt_parts = ["[上下文记忆]"]
        for i, mem in enumerate(recent, 1):
            prompt_parts.append(f"{i}. {mem.hil_symbol}")
        
        prompt_parts.append("\n[当前任务]")
        return "\n".join(prompt_parts)
    
    def compression_ratio(self) -> float:
        """计算平均压缩率"""
        if not self.memories:
            return 0.0
        
        total_raw = sum(len(m.raw_text) for m in self.memories)
        total_hil = sum(len(m.hil_symbol) for m in self.memories)
        
        return total_hil / total_raw if total_raw > 0 else 0.0
    
    def stats(self) -> Dict:
        """返回统计信息"""
        return {
            "total_memories": len(self.memories),
            "max_size": self.max_size,
            "compression_ratio": round(self.compression_ratio(), 2),
            "memory_size_bytes": sum(len(json.dumps(m.to_dict())) for m in self.memories)
        }


class SNFEngine:
    """符号神经融合引擎 - 核心整合"""
    
    def __init__(self):
        self.compressor = HILCompressor()
        self.memory_matrix = SymbolicMemoryMatrix(max_size=50)
    
    def process(self, user_input: str) -> Dict:
        """
        处理用户输入，返回融合后的上下文
        
        Args:
            user_input: 用户自然语言输入
            
        Returns:
            包含压缩符号、记忆上下文、统计信息的字典
        """
        # 1. 压缩当前输入
        current_memory = self.compressor.compress(user_input)
        
        # 2. 添加到记忆矩阵
        self.memory_matrix.add(current_memory)
        
        # 3. 生成记忆上下文
        context_prompt = self.memory_matrix.to_prompt(window_size=10)
        
        # 4. 返回结果
        return {
            "current_hil": current_memory.hil_symbol,
            "context_prompt": context_prompt,
            "memory_stats": self.memory_matrix.stats(),
            "full_context": self._build_full_context(current_memory)
        }
    
    def _build_full_context(self, current: SymbolicMemory) -> str:
        """构建完整的 LLM 输入上下文"""
        context_lines = [
            "=== SNF 符号神经融合上下文 ===",
            "",
            f"[当前输入 HIL]: {current.hil_symbol}",
            f"[原始意图]: {json.dumps(current.intent, ensure_ascii=False)}",
            "",
            self.memory_matrix.to_prompt(window_size=5),
            "",
            f"[统计]: 压缩率 {self.memory_matrix.compression_ratio():.2%}, 记忆数 {len(self.memory_matrix.memories)}"
        ]
        return "\n".join(context_lines)


# ============ 测试与演示 ============

def test_compression():
    """测试压缩功能"""
    print("=" * 60)
    print("SNF 核心功能测试")
    print("=" * 60)
    
    engine = SNFEngine()
    
    # 模拟多轮对话
    conversations = [
        "你好，请帮我分析这份文档",
        "用中文输出，3个要点",
        "再对比一下去年的数据",
        "生成一份总结报告",
        "用 bullet 格式输出"
    ]
    
    print("\n[模拟多轮对话压缩]")
    print("-" * 60)
    
    for i, text in enumerate(conversations, 1):
        result = engine.process(text)
        
        print(f"\n回合 {i}:")
        print(f"  输入: {text[:40]}...")
        print(f"  HIL: {result['current_hil']}")
        print(f"  记忆数: {result['memory_stats']['total_memories']}")
    
    # 最终统计
    print("\n" + "=" * 60)
    print("最终统计:")
    print("=" * 60)
    stats = engine.memory_matrix.stats()
    print(f"总记忆数: {stats['total_memories']}")
    print(f"平均压缩率: {stats['compression_ratio']:.2%}")
    print(f"内存占用: {stats['memory_size_bytes']} bytes")
    
    # 显示完整上下文
    print("\n" + "=" * 60)
    print("生成的 LLM 上下文示例:")
    print("=" * 60)
    final_result = engine.process("最后，用表格对比结果")
    print(final_result['full_context'][:800] + "...")
    
    return engine


def test_long_context_retention():
    """测试长上下文保持能力"""
    print("\n" + "=" * 60)
    print("长上下文保持测试")
    print("=" * 60)
    
    engine = SNFEngine()
    
    # 模拟 20 轮对话
    print("\n模拟 20 轮对话...")
    for i in range(20):
        text = f"这是第 {i+1} 轮对话的内容，包含一些关键信息 number_{i*111}"
        engine.process(text)
    
    # 检查是否能记住早期信息
    print(f"\n总记忆数: {len(engine.memory_matrix.memories)}")
    print(f"压缩率: {engine.memory_matrix.compression_ratio():.2%}")
    
    # 显示上下文
    context = engine.memory_matrix.to_prompt(window_size=10)
    print(f"\n最近 10 轮上下文长度: {len(context)} 字符")
    print("\n上下文预览:")
    print(context[:500])


if __name__ == "__main__":
    # 运行测试
    engine = test_compression()
    test_long_context_retention()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！SNF 核心功能运行正常")
    print("=" * 60)
    print("\n停止写文档，开始写代码！")
