# Symbolic-Neural Fusion (SNF)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Research](https://img.shields.io/badge/Status-Research-blue.svg)]()

> Using structured symbolic compression to solve LLM long-context amnesia
> 用结构化符号压缩解决 LLM 长上下文失忆问题

---

## 🎯 核心问题

LLM 在 10+ 轮对话后开始出现"失忆"：
- 忘记早期对话内容
- 长文档中间信息提取失败
- 复杂推理中前提条件丢失

**根本原因**: Transformer 软注意力随序列长度平方级稀释

---

## 💡 核心洞察

**HIL (Human-Instruction Language)** 的压缩特性：
```
自然语言: "分析文档，中文输出，bullet格式，3个要点"
HIL 压缩: "? : $ {z,b} (3)"
压缩率: 35-62%
信息保持: 意图完整，可还原
```

---

## 🔧 解决方案：符号神经融合 (SNF)

### 架构
```
用户输入
    ↓
HIL 压缩引擎 → 提取关键意图，压缩为符号
    ↓
符号记忆矩阵 → 固定长度结构化表示（硬锚点）
    ↓
神经融合层 → 注入 LLM 上下文
    ↓
LLM 推理 → 保持完整上下文感知
```

### 核心创新
| 特性 | 说明 |
|------|------|
| **硬锚点** | 符号矩阵不随对话长度稀释 |
| **软硬结合** | 符号硬注意力 + Transformer 软注意力 |
| **高密度** | 固定长度表示，O(1) 空间复杂度 |
| **可解释** | 显式意图结构，可阅读调试 |

---

## 🚀 应用场景

1. **长对话保持** - 20+ 轮后仍记得最初需求
2. **长文档理解** - 100页后准确定位第30页细节
3. **复杂推理链** - 多步证明中记住初始假设

---

## 📊 与现有方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **RAG** | 精确召回 | 需向量库、检索延迟 |
| **Streaming** | 简单 | 丢失窗口外信息 |
| **SNF (本框架)** | 轻量、高密度、软硬结合 | 压缩有信息损失 |

---

## 🔬 研究状态

**当前阶段**: 概念验证 (PoC)

- [x] 框架设计
- [ ] 原型实现
- [ ] 基准测试
- [ ] 论文发表

---

## 📁 项目结构

```
symbolic-neural-fusion/
├── docs/           # 设计文档
├── prototype/      # 原型实现
├── tests/          # 测试用例
├── benchmarks/     # 性能评估
└── papers/         # 研究论文
```

---

## 🤝 贡献

欢迎参与研究讨论和贡献代码！

- [Discussions](../../discussions) - 研究讨论
- [Issues](../../issues) - 问题反馈
- [Projects](../../projects) - 开发计划

---

## 📄 许可

MIT License - 详见 [LICENSE](LICENSE)

---

**基于 HIL-Gateway 项目的延伸研究**

*Created by CJ + OpenClaw AI | 2026-03-05*