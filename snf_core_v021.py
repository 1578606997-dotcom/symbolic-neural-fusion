"""
Symbolic-Neural Fusion (SNF) - Core Implementation v0.2.1
Bug fixes and improvements based on code review

Changes:
- Add complete type annotations
- Fix entity extraction hardcoding
- Add error handling
- Add thread safety
- Add logging
"""

import json
import re
import logging
import threading
from typing import List, Dict, Tuple, Optional, TypedDict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_MAX_MEMORY_SIZE = 50
DEFAULT_WINDOW_SIZE = 10
MIN_COMPRESSION_RATIO = 0.1
MAX_COMPRESSION_RATIO = 0.9


class ComparisonResult(TypedDict):
    """对比结果类型定义"""
    entities: List[str]
    dimensions: List[str]


class IntentDict(TypedDict, total=False):
    """意图字典类型定义"""
    action: str
    object: str
    modifiers: List[str]
    constraints: Dict[str, Any]
    comparison: Optional[ComparisonResult]


@dataclass
class SymbolicMemory:
    """符号记忆单元 - 核心数据结构
    
    Attributes:
        timestamp: 创建时间戳
        hil_symbol: HIL 压缩符号
        raw_text: 原始文本
        intent: 解析后的意图字典
    """
    timestamp: float
    hil_symbol: str
    raw_text: str
    intent: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，长文本自动截断"""
        try:
            raw_display = self.raw_text[:100] + "..." if len(self.raw_text) > 100 else self.raw_text
            return {
                "timestamp": self.timestamp,
                "hil": self.hil_symbol,
                "raw": raw_display,
                "intent": self.intent
            }
        except Exception as e:
            logger.error(f"Failed to convert SymbolicMemory to dict: {e}")
            return {"error": str(e), "hil": self.hil_symbol}


class HILCompressor:
    """HIL 压缩引擎 - 将自然语言压缩为符号"""
    
    def __init__(self):
        # 轻量级加权分类器（预编译正则，兼顾准确率与速度）
        self.action_features: Dict[str, List[Tuple[re.Pattern, float]]] = {
            "?": [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in [
                    (r"\b(分析|查看|检查|总结|评估|解释|说明|审查|review|analy[sz]e|summari[sz]e)\b", 2.0),
                    (r"\b(为什么|原因|解读|诊断)\b", 1.0)
                ]
            ],
            "!": [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in [
                    (r"\b(创建|生成|写|制作|构建|起草|产出|输出|做一份|撰写|create|generate|draft|build)\b", 2.0),
                    (r"\b(报告|邮件|方案|计划|总结)\b", 1.0)
                ]
            ],
            ">": [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in [
                    (r"\b(转换|变成|改为|翻译|改写|重写|转为|转成|convert|translate|rewrite|transform)\b", 2.0),
                    (r"\b(格式|语言|风格)\b", 1.0)
                ]
            ],
            "@": [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in [
                    (r"\b(查询|搜索|查找|获取|检索|找出|定位|query|search|find|lookup|fetch)\b", 2.0),
                    (r"\b(数据库|记录|日志|资料)\b", 1.0)
                ]
            ]
        }

        self.object_features: Dict[str, List[Tuple[re.Pattern, float]]] = {
            "$": [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in [
                    (r"\b(文档|文件|报告|文本|文章|邮件|合同|代码|脚本|计划书|pdf|doc)\b", 2.0),
                    (r"\b(这份|该文|内容)\b", 0.5)
                ]
            ],
            "@": [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in [
                    (r"\b(知识|数据|信息|资料|指标|日志|统计|记录|数据库|dataset|data)\b", 2.0),
                    (r"\b(趋势|反馈|明细)\b", 0.5)
                ]
            ]
        }

        self.modifier_map: List[Tuple[re.Pattern, str]] = [
            (re.compile(r"\b(中文|汉语|简体)\b", re.IGNORECASE), "z"),
            (re.compile(r"\b(英文|英语|english)\b", re.IGNORECASE), "e"),
            (re.compile(r"\b(bullet|要点|列表|条目|分点)\b", re.IGNORECASE), "b"),
            (re.compile(r"\b(json|yaml|xml|结构化|格式)\b", re.IGNORECASE), "s")
        ]

        self.limit_pattern = re.compile(r"(\d+)[个条点项份段]?", re.IGNORECASE)
        # 改进：添加词边界避免误匹配 "vs code"
        # 使用简单模式，避免 variable-length look-behind
        self.comparison_trigger = re.compile(r"\b(对比|比较|vs)\b", re.IGNORECASE)
        self.entity_split_pattern = re.compile(r"和|与|及|vs|VS", re.IGNORECASE)

        self.comparison_dimension_map: Dict[str, str] = {
            "价格": "price",
            "价钱": "price",
            "成本": "price",
            "费用": "price",
            "质量": "quality",
            "品质": "quality",
            "性能": "performance",
            "功能": "feature",
            "服务": "service",
            "速度": "speed",
            "效率": "efficiency"
        }
        
        # 改进：支持更多实体模式
        self.entity_patterns: List[re.Pattern] = [
            re.compile(r"产品\s*([A-Za-z0-9]+)", re.IGNORECASE),
            re.compile(r"([A-Za-z]+[0-9]*)\s*(?:和|与|及|vs|VS)"),
            re.compile(r"(?:和|与|及|vs|VS)\s*([A-Za-z]+[0-9]*)")
        ]
    
    def compress(self, text: str) -> SymbolicMemory:
        """将自然语言压缩为 HIL 符号
        
        Args:
            text: 自然语言输入
            
        Returns:
            SymbolicMemory: 符号记忆单元
            
        Raises:
            ValueError: 如果输入为空
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        
        try:
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
        except Exception as e:
            logger.error(f"Compression failed for text '{text[:50]}...': {e}")
            # 返回默认结果而不是抛出异常
            return SymbolicMemory(
                timestamp=datetime.now().timestamp(),
                hil_symbol="? : $",
                raw_text=text,
                intent={"action": "?", "object": "$", "error": str(e)}
            )
    
    def _extract_intent(self, text: str) -> IntentDict:
        """提取意图结构"""
        comparison = self._extract_comparison(text)
        intent: IntentDict = {
            "action": "?",
            "object": "$",
            "modifiers": [],
            "constraints": {},
            "comparison": comparison
        }
        
        intent["action"] = self._predict_label(text, self.action_features, default="?")
        intent["object"] = self._predict_label(text, self.object_features, default="$")

        for pattern, code in self.modifier_map:
            if pattern.search(text):
                intent["modifiers"].append(code)

        num_match = self.limit_pattern.search(text)
        if num_match:
            intent["constraints"]["limit"] = int(num_match.group(1))
        
        return intent
    
    def _build_hil(self, intent: IntentDict) -> str:
        """构建 HIL 符号"""
        parts = [intent["action"], ":", intent["object"]]

        comparison = intent.get("comparison")
        if comparison:
            entities = ",".join(comparison["entities"])
            dimensions = ",".join(comparison["dimensions"])
            return f"@vs({entities}){{{dimensions}}}"
        
        # 添加修饰符
        if intent["modifiers"]:
            parts.append(f"{{{','.join(intent['modifiers'])}}}")
        
        # 添加约束
        if "limit" in intent["constraints"]:
            parts.append(f"({intent['constraints']['limit']})")
        
        return " ".join(parts)

    @staticmethod
    def _predict_label(text: str, feature_map: Dict[str, List[Tuple[re.Pattern, float]]], default: str) -> str:
        """基于加权关键特征的轻量分类器"""
        best_label = default
        best_score = 0.0  # 改为0，避免负权重问题

        for label, features in feature_map.items():
            score = 0.0
            for pattern, weight in features:
                if pattern.search(text):
                    score += weight
            if score > best_score:
                best_label = label
                best_score = score

        return best_label if best_score > 0 else default

    def _extract_comparison(self, text: str) -> Optional[ComparisonResult]:
        """提取对比语法，生成 @vs(A,B){dimensions} 结构"""
        if not self.comparison_trigger.search(text):
            return None

        try:
            entities = self._extract_entities_for_comparison(text)
            dimensions = self._extract_dimensions_for_comparison(text)

            if len(entities) < 2 or not dimensions:
                return None

            return {
                "entities": entities[:2],
                "dimensions": dimensions
            }
        except Exception as e:
            logger.warning(f"Failed to extract comparison from '{text[:50]}...': {e}")
            return None

    def _extract_entities_for_comparison(self, text: str) -> List[str]:
        """提取对比实体，支持多种模式"""
        entities: List[str] = []
        
        # 尝试多种实体提取模式
        for pattern in self.entity_patterns:
            matches = pattern.findall(text)
            if matches:
                entities.extend(matches)
                break
        
        # 如果没有匹配到特定模式，使用通用分割
        if len(entities) < 2:
            if "对比" in text:
                base = text.split("对比", 1)[1]
            elif "比较" in text:
                base = text.split("比较", 1)[1]
            else:
                base = text

            base = re.split(r"的", base, maxsplit=1)[0]
            candidates = [c.strip() for c in self.entity_split_pattern.split(base) if c.strip()]
            
            # 清理实体名称
            for c in candidates[:2]:
                # 去除标点和多余空格
                clean = re.sub(r'[，。！？.,!?]', '', c).strip()
                if clean and clean not in entities:
                    entities.append(clean)
        
        # 标准化实体名称
        normalized = []
        for e in entities[:2]:
            # 转换为合法标识符
            safe = re.sub(r'[^\w]', '', e)
            if safe:
                normalized.append(safe)
        
        return normalized

    def _extract_dimensions_for_comparison(self, text: str) -> List[str]:
        """提取对比维度"""
        dimensions: List[str] = []
        for zh_key, dim in self.comparison_dimension_map.items():
            if zh_key in text and dim not in dimensions:
                dimensions.append(dim)
        return dimensions


class SymbolicMemoryMatrix:
    """符号记忆矩阵 - 存储和管理符号记忆（线程安全）"""
    
    def __init__(self, max_size: int = DEFAULT_MAX_MEMORY_SIZE):
        self._memories: List[SymbolicMemory] = []
        self._max_size = max_size
        self._access_count = 0
        self._lock = threading.Lock()  # 线程锁
    
    def add(self, memory: SymbolicMemory) -> None:
        """添加记忆（线程安全）"""
        with self._lock:
            self._memories.append(memory)
            
            # 保持固定大小（FIFO）
            if len(self._memories) > self._max_size:
                self._memories.pop(0)
    
    def get_context(self, window_size: int = DEFAULT_WINDOW_SIZE) -> List[SymbolicMemory]:
        """获取最近 N 条记忆（线程安全）"""
        with self._lock:
            return self._memories[-window_size:]
    
    def to_prompt(self, window_size: int = DEFAULT_WINDOW_SIZE) -> str:
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
        with self._lock:
            if not self._memories:
                return 0.0
            
            total_raw = sum(len(m.raw_text) for m in self._memories)
            total_hil = sum(len(m.hil_symbol) for m in self._memories)
            
            if total_raw == 0:
                return 0.0
                
            ratio = total_hil / total_raw
            return max(MIN_COMPRESSION_RATIO, min(ratio, MAX_COMPRESSION_RATIO))
    
    def stats(self) -> Dict[str, Any]:
        """返回统计信息（带错误处理）"""
        try:
            with self._lock:
                return {
                    "total_memories": len(self._memories),
                    "max_size": self._max_size,
                    "compression_ratio": round(self.compression_ratio(), 2),
                    "memory_size_bytes": sum(
                        len(json.dumps(m.to_dict(), ensure_ascii=False).encode('utf-8')) 
                        for m in self._memories
                    )
                }
        except Exception as e:
            logger.error(f"Failed to calculate stats: {e}")
            return {
                "total_memories": 0,
                "max_size": self._max_size,
                "compression_ratio": 0.0,
                "memory_size_bytes": 0,
                "error": str(e)
            }
    
    @property
    def memories(self) -> List[SymbolicMemory]:
        """获取记忆副本（线程安全）"""
        with self._lock:
            return self._memories.copy()
    
    @property
    def max_size(self) -> int:
        """获取最大容量"""
        return self._max_size


class SNFEngine:
    """符号神经融合引擎 - 核心整合"""
    
    def __init__(self, max_memory_size: int = DEFAULT_MAX_MEMORY_SIZE):
        self.compressor = HILCompressor()
        self.memory_matrix = SymbolicMemoryMatrix(max_size=max_memory_size)
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入，返回融合后的上下文
        
        Args:
            user_input: 用户自然语言输入
            
        Returns:
            包含压缩符号、记忆上下文、统计信息的字典
        """
        try:
            # 1. 压缩当前输入
            current_memory = self.compressor.compress(user_input)
            
            # 2. 添加到记忆矩阵
            self.memory_matrix.add(current_memory)
            
            # 3. 生成记忆上下文
            context_prompt = self.memory_matrix.to_prompt(window_size=DEFAULT_WINDOW_SIZE)
            
            # 4. 返回结果
            return {
                "current_hil": current_memory.hil_symbol,
                "context_prompt": context_prompt,
                "memory_stats": self.memory_matrix.stats(),
                "full_context": self._build_full_context(current_memory),
                "success": True
            }
        except Exception as e:
            logger.error(f"Process failed for input '{user_input[:50]}...': {e}")
            return {
                "current_hil": "? : $",
                "context_prompt": "",
                "memory_stats": {},
                "full_context": f"Error: {e}",
                "success": False,
                "error": str(e)
            }
    
    def _build_full_context(self, current: SymbolicMemory) -> str:
        """构建完整的 LLM 输入上下文"""
        try:
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
        except Exception as e:
            logger.error(f"Failed to build full context: {e}")
            return f"Error building context: {e}"


# 保持向后兼容的导出
__all__ = [
    'SymbolicMemory',
    'HILCompressor',
    'SymbolicMemoryMatrix',
    'SNFEngine',
    'ComparisonResult',
    'IntentDict',
    'DEFAULT_MAX_MEMORY_SIZE',
    'DEFAULT_WINDOW_SIZE'
]
