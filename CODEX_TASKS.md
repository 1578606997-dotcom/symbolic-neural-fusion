# SNF 项目 - Codex 外包任务清单

## 项目概述

**Symbolic-Neural Fusion (SNF)**  
用 HIL 符号压缩解决 LLM 长上下文失忆问题。

**当前状态**: 核心原型已完成 (474 行代码)  
**外包目标**: 完善功能、增加测试、优化性能

**仓库**: https://github.com/1578606997-dotcom/symbolic-neural-fusion

---

## 当前代码架构

```
symbolic-neural-fusion/
├── snf_core.py          # 核心实现 (314行)
│   ├── SymbolicMemory       # 符号记忆单元
│   ├── HILCompressor        # HIL 压缩引擎
│   ├── SymbolicMemoryMatrix # 符号记忆矩阵
│   └── SNFEngine            # 融合引擎
├── benchmark.py         # 性能测试 (160行)
├── README.md            # 快速开始
└── archive/             # 设计文档归档
```

**当前性能**:
- 压缩率: 35%
- 压缩速度: 0.11ms/轮
- 内存: 恒定 12KB (100轮)

---

## 外包任务列表 (按优先级)

### P0: 核心功能完善

#### 任务 1: 改进 HIL 压缩器准确率
**现状**: 基于关键词匹配，准确率待提升  
**目标**: 使用轻量级 LLM 或更好的模式匹配
**输入**: `snf_core.py::HILCompressor`  
**输出**: 改进后的压缩器，准确率 > 80%

```python
# 当前: 关键词匹配
if re.search(r"\b(分析|查看)\b", text):
    intent["action"] = "?"

# 目标: 更智能的意图识别
# 可考虑: 小型分类模型、更好的正则、或 LLM API
```

#### 任务 2: 实现对比语法 @vs()
**需求**: 支持对比两个对象  
**示例**: `@vs(productA,productB){price,quality}`  
**输入**: 扩展 `HILCompressor` 和 `SymbolicMemory`  
**输出**: 支持对比语法的完整实现

#### 任务 3: 添加记忆检索功能
**现状**: 只能获取最近 N 条  
**目标**: 支持语义相似度检索  
**方法**: 简单向量相似度或关键词匹配

---

### P1: 测试与质量

#### 任务 4: 单元测试覆盖
**目标**: 为所有核心类添加单元测试  
**文件**: `tests/test_snf_core.py`  
**覆盖率**: > 80%

#### 任务 5: 集成测试
**场景**: 20轮对话完整流程测试  
**验证**: 信息保持率、上下文完整性

#### 任务 6: 性能回归测试
**目标**: 确保修改不降低性能  
**基准**: 当前 benchmark.py 数据

---

### P2: 功能扩展

#### 任务 7: 多语言支持
**目标**: 支持英文、日文、韩文压缩  
**方法**: 扩展 `modifier_map` 和 `action_map`

#### 任务 8: 导出/导入记忆
**功能**: 保存对话历史到文件，支持恢复  
**格式**: JSON / SQLite

#### 任务 9: 与真实 LLM 集成示例
**目标**: 展示 SNF 如何与 OpenAI/Moonshot 集成  
**文件**: `examples/llm_integration.py`

---

### P3: 文档与示例

#### 任务 10: API 文档
**工具**: docstring + 自动生成  
**格式**: Markdown 或 Sphinx

#### 任务 11: 使用示例
**场景**:
- 客服对话保持
- 长文档分析
- 代码审查助手

---

## Codex 工作指南

### 开发流程
1. 从任务列表选择任务
2. 创建分支: `git checkout -b feature/task-name`
3. 开发并测试
4. 提交 PR: 包含测试和性能数据

### 代码规范
- Python 3.8+
- 类型提示 (typing)
- Docstring (Google style)
- 单元测试 (pytest)

### 性能要求
任何修改必须通过 benchmark.py 测试，不得降低:
- 压缩率 (< 30%)
- 速度 (> 0.5ms/轮)
- 内存 (< 20KB/100轮)

---

## 交付物

### 每个任务的交付物
- [ ] 实现代码
- [ ] 单元测试
- [ ] 性能测试数据
- [ ] 更新 README (如需要)

### 最终交付物
- [ ] 所有 P0 任务完成
- [ ] 测试覆盖率 > 80%
- [ ] 性能不低于基准
- [ ] 完整 API 文档
- [ ] 3 个使用示例

---

## 联系方式

**项目 Owner**: CJ (Jhong Cai)  
**Review**: 通过 GitHub PR  
**沟通**: GitHub Issues / Discussions

---

**开始开发！**
```bash
git clone https://github.com/1578606997-dotcom/symbolic-neural-fusion.git
cd symbolic-neural-fusion
python3 snf_core.py  # 验证运行
python3 benchmark.py # 查看基准
```
