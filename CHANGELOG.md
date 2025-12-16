# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.0.0] - 2025-12-16

### 🎉 重大更新 - Agent 架构重构

本版本对系统进行了全面的架构升级，采用 Agent-Based Architecture，提升了代码的可维护性和可扩展性。

### 🗑️ 移除

- **旧模块文件已删除** - 功能已完全迁移到新的 Agent 架构
  - ❌ `stock_data_fetcher.py` (已被 `FetchAgent` 替代)
  - ❌ `ai_analyzer.py` (已被 `AnalyseAgent` 替代)
  - ❌ `report_generator.py` (功能已集成到 `AnalyseAgent`)

> ⚠️ **Breaking Change**: 如果你的代码直接导入了这些旧模块，需要迁移到新的 Agent API。详见 [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)

### ✨ 新增

#### 核心架构
- **全局控制器 (StockAnalysisController)** - `controller.py`
  - 统一管理所有 Agent 的生命周期
  - 协调数据流转和业务流程
  - 统一的错误处理机制
  - 执行历史记录功能
  - 支持上下文管理器（`with` 语句）

#### Agent 模块
- **FetchAgent (数据获取代理)** - `agents/fetch-agent/agent.py`
  - 专注于数据获取功能
  - 从 Longbridge API 获取股票行情
  - 数据预处理和格式化
  - 清晰的接口设计

- **AnalyseAgent (分析报告代理)** - `agents/analyse-agent/agent.py`
  - 专注于 AI 分析和报告生成
  - 集成 Ollama AI 调用
  - 自动生成和管理分析报告
  - 报告索引维护

#### 文档
- **架构文档** - `ARCHITECTURE.md`
  - 详细的系统架构说明
  - 数据流转图解
  - 扩展指南
  - 最佳实践

- **升级指南** - `UPGRADE_GUIDE.md`
  - v1.0 到 v2.0 的迁移指南
  - 代码示例对比
  - 常见问题解答

- **架构测试脚本** - `test_architecture.py`
  - 自动化测试新架构
  - 验证模块导入
  - 兼容性检查

### 🔄 变更

#### 主程序
- **main.py** - 重构为使用新的 Controller
  - 简化为主入口点
  - 保留 `StockAnalysisSystem` 作为兼容别名
  - 改进的命令行界面和帮助信息

- **app.py** - 更新为使用新架构
  - 导出新的 Controller 类
  - 保持向后兼容

#### 项目结构
```
新增目录结构:
agents/
├── fetch-agent/       # 数据获取代理
├── analyse-agent/     # 分析报告代理
└── trade-agent/       # 交易代理（预留）

新增配置文件:
├── controller.py      # 全局控制器
├── ARCHITECTURE.md    # 架构文档
├── UPGRADE_GUIDE.md   # 升级指南
└── CHANGELOG.md       # 本文件
```

### 🛠️ 改进

#### 日志输出
- 更清晰的阶段划分显示
- 详细的进度提示
- 友好的错误信息
- 统一的日志格式

#### 错误处理
- 统一的错误传播机制
- 标准化的返回格式
- 更详细的错误信息
- 优雅的失败处理

#### 代码质量
- 清晰的职责划分
- 更好的模块化设计
- 改进的类型提示
- 完善的文档字符串

### ⚡ 性能

- 执行效率保持不变（核心逻辑未变）
- 内存占用相似
- 启动时间略有增加（Agent 初始化）

### 🔧 技术细节

#### 新的数据格式

**Controller 执行结果**:
```python
{
    "status": "success",
    "execution_id": "20251216_100000",
    "symbols": ["NVDA.US"],
    "report_path": "...",
    "stages": {
        "fetch": {...},
        "analyse": {...}
    },
    "start_time": "...",
    "end_time": "..."
}
```

**Agent 统一返回格式**:
```python
{
    "status": "success|error",
    "data": {...},           # 或其他数据字段
    "timestamp": "...",
    "error": "..."           # 仅在失败时
}
```

### 🔒 向后兼容

#### ✅ 完全兼容
- 命令行使用方式
- 环境变量配置
- 报告格式
- 策略文件

#### ⚠️ 需要适配
- 直接导入旧模块的代码
- 依赖 `run_analysis()` 返回值格式的代码

详见 [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)

### 📝 已知问题

无

### 🙏 致谢

感谢所有使用和反馈的用户！

---

## [1.0.0] - 2025-12-15

### 🎉 初始发布

#### ✨ 核心功能
- 集成 Longbridge OpenAPI 获取股票数据
- 使用 Ollama AI 进行智能分析
- 基于五维度量化评级体系
- 自动生成 Markdown 分析报告

#### 📦 主要模块
- `stock_data_fetcher.py` - 数据获取
- `ai_analyzer.py` - AI 分析
- `report_generator.py` - 报告生成
- `main.py` - 主程序入口

#### 📚 文档
- `README.md` - 项目文档
- `QUICKSTART.md` - 快速入门
- `strategies/rating.md` - 分析策略

#### ⚙️ 配置
- 支持 `.env` 环境变量配置
- 灵活的股票列表配置
- 可自定义 AI 模型

---

## 格式说明

- `Added` ✨ - 新增功能
- `Changed` 🔄 - 功能变更
- `Deprecated` ⚠️ - 即将废弃的功能
- `Removed` 🗑️ - 已移除的功能
- `Fixed` 🐛 - 错误修复
- `Security` 🔒 - 安全相关更新

