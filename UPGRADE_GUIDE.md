# 🔄 v2.0 升级指南

## 概述

v2.0 采用全新的 Agent-Based Architecture，将原有的功能模块化为独立的 Agent，并引入全局控制器统一管理。

## 主要变更

### 架构变更

| 变更类型 | v1.0 | v2.0 |
|---------|------|------|
| **架构模式** | 函数式 / 类式混合 | Agent-Based Architecture |
| **主入口** | `StockAnalysisSystem` 类 | `StockAnalysisController` 类 |
| **数据获取** | `stock_data_fetcher.py` | `agents/fetch-agent/agent.py` |
| **AI 分析** | `ai_analyzer.py` | `agents/analyse-agent/agent.py` |
| **报告生成** | `report_generator.py` | 集成在 `AnalyseAgent` 中 |

### 新增功能

✨ **全局控制器 (Controller)**
- 统一管理所有 Agent 的生命周期
- 协调数据流转
- 统一错误处理
- 执行历史记录

✨ **Agent 架构**
- `FetchAgent`: 专注数据获取
- `AnalyseAgent`: 专注分析和报告
- 清晰的职责划分
- 易于扩展新的 Agent

✨ **改进的日志输出**
- 更清晰的阶段划分
- 详细的进度提示
- 友好的错误信息

## 迁移指南

### 1. 代码迁移

#### v1.0 代码

```python
from main import StockAnalysisSystem

# 创建系统
system = StockAnalysisSystem()

# 运行分析
report_path = system.run_analysis(['NVDA.US'])

# 清理
system.cleanup()
```

#### v2.0 代码（推荐）

```python
from controller import StockAnalysisController

# 使用上下文管理器（推荐）
with StockAnalysisController() as controller:
    result = controller.execute_analysis(['NVDA.US'])
    report_path = result.get('report_path')
```

#### v2.0 代码（兼容模式）

```python
# 方式1: 使用别名（完全兼容）
from main import StockAnalysisSystem

with StockAnalysisSystem() as system:
    result = system.execute_analysis(['NVDA.US'])

# 方式2: 直接使用 Controller
from controller import StockAnalysisController

controller = StockAnalysisController()
controller.initialize()
result = controller.execute_analysis(['NVDA.US'])
controller.cleanup()
```

### 2. 返回值变更

#### v1.0 返回值

```python
report_path: str  # 直接返回报告路径字符串
```

#### v2.0 返回值

```python
{
    "status": "success",
    "execution_id": "20251216_100000",
    "symbols": ["NVDA.US"],
    "report_path": "report/stock_analysis_NVDA_20251216_100000.md",
    "stages": {
        "fetch": {...},
        "analyse": {...}
    },
    "start_time": "...",
    "end_time": "..."
}
```

**迁移方法**:

```python
# v1.0
report_path = system.run_analysis(['NVDA.US'])

# v2.0
result = controller.execute_analysis(['NVDA.US'])
report_path = result.get('report_path')  # 获取报告路径
status = result.get('status')            # 检查执行状态
```

### 3. 环境变量（无变更）

v2.0 完全兼容 v1.0 的环境变量配置，无需修改 `.env` 文件。

```env
# 这些配置在 v2.0 中仍然有效
LONGBRIDGE_APP_KEY=...
LONGBRIDGE_APP_SECRET=...
LONGBRIDGE_ACCESS_TOKEN=...
STOCK_LIST=BABA.US,NVDA.US,TSLA.US
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
OUTPUT_DIR=report
```

### 4. 命令行使用（无变更）

```bash
# v1.0 和 v2.0 都支持
python main.py
python app.py

# 查看帮助
python main.py --help
```

## 新功能使用

### 1. 查看执行历史

```python
with StockAnalysisController() as controller:
    # 执行多次分析
    controller.execute_analysis(['NVDA.US'])
    controller.execute_analysis(['AAPL.US'])
    
    # 查看历史
    history = controller.get_execution_history()
    print(f"共执行 {len(history)} 次分析")
    
    # 查看最后一次执行
    last = controller.get_last_execution()
    print(f"最后执行: {last['execution_id']}")
```

### 2. 单独使用 Agent

```python
# 只获取数据，不分析
from agents.fetch_agent import FetchAgent

fetch_agent = FetchAgent()
result = fetch_agent.execute(['NVDA.US', 'AAPL.US'])

# 格式化数据
formatted = fetch_agent.format_for_analysis(result)
print(formatted)

fetch_agent.close()
```

```python
# 只分析数据，不获取
from agents.analyse_agent import AnalyseAgent

analyse_agent = AnalyseAgent()

# 使用自定义数据
custom_data = """
# 股票实时数据
...
"""

result = analyse_agent.execute(
    formatted_data=custom_data,
    stock_symbols=['NVDA.US']
)

print(result['report_path'])
```

### 3. 获取系统信息

```python
with StockAnalysisController() as controller:
    info = controller.get_system_info()
    
    print(f"初始化状态: {info['is_initialized']}")
    print(f"执行次数: {info['execution_count']}")
    print(f"Agent 状态: {info['agents']}")
```

## 向后兼容性

### 完全兼容

✅ 命令行使用方式保持不变  
✅ 环境变量配置保持不变  
✅ 报告格式保持不变  
✅ 策略文件 (`rating.md`) 保持不变

### ⚠️ 破坏性变更

❌ 旧模块文件已删除，无法直接导入  
❌ 必须迁移到新的 Agent API  
❌ `run_analysis()` 方法已改为 `execute_analysis()`

### 需要适配

⚠️ **如果你在代码中直接导入使用了旧模块**:

```python
# 旧代码（v1.0，已移除）
# from stock_data_fetcher import StockDataFetcher
# from ai_analyzer import AIAnalyzer
# from report_generator import ReportGenerator

# v2.0 新代码
from agents.fetch_agent import FetchAgent
from agents.analyse_agent import AnalyseAgent
from controller import StockAnalysisController
```

> ⚠️ **重要**: 旧模块文件已在 v2.0 中移除，请使用新的 Agent 架构。

⚠️ **如果你依赖了 `run_analysis()` 的返回值格式**:

```python
# 旧代码
report_path = system.run_analysis(['NVDA.US'])
if report_path:
    print(f"成功: {report_path}")

# 新代码
result = controller.execute_analysis(['NVDA.US'])
if result['status'] == 'success':
    print(f"成功: {result['report_path']}")
```

## 性能对比

| 指标 | v1.0 | v2.0 | 说明 |
|-----|------|------|------|
| 执行时间 | ≈ N 秒 | ≈ N 秒 | 相同（核心逻辑未变） |
| 内存占用 | ~ M MB | ~ M MB | 相似 |
| 代码复杂度 | 中 | 低 | 更清晰的模块划分 |
| 可扩展性 | 低 | 高 | Agent 架构易于扩展 |
| 错误处理 | 基础 | 增强 | 统一的错误处理机制 |

## 常见问题

### Q1: 我必须升级到 v2.0 吗？

**不必须**。v1.0 的旧模块仍然保留在代码库中，你可以继续使用。但我们强烈推荐升级以获得：
- 更清晰的代码结构
- 更好的可维护性
- 更强的扩展能力
- 更详细的日志输出

### Q2: 升级会破坏我的现有代码吗？

**不会**。如果你只是通过命令行使用（`python main.py`），无需任何修改。

如果你在代码中导入使用，查看上面的"迁移指南"进行简单调整即可。

### Q3: 旧的报告还能查看吗？

**能**。报告格式没有改变，所有旧报告仍然可以正常查看。

### Q4: 旧模块文件已删除，如何迁移？

**必须迁移到新 API**。旧模块文件已被移除，所有功能已整合到新的 Agent 架构中。

```python
# v2.0 API
from agents.fetch_agent import FetchAgent
from agents.analyse_agent import AnalyseAgent
from controller import StockAnalysisController

# 使用 Controller 统一管理
with StockAnalysisController() as controller:
    result = controller.execute_analysis(['NVDA.US'])
```

### Q5: 如何扩展新的功能？

查看 [ARCHITECTURE.md](ARCHITECTURE.md) 中的"扩展指南"部分，了解如何添加新的 Agent。

## 下一步

1. ✅ 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解新架构
2. ✅ 查看 [README.md](README.md) 了解新功能
3. ✅ 运行 `python main.py` 体验 v2.0
4. ✅ 根据需要迁移你的自定义代码

## 反馈

如果你在升级过程中遇到任何问题，请：
- 提交 Issue
- 查看文档
- 参考示例代码

---

*感谢使用本系统！祝投资顺利！* 📈

