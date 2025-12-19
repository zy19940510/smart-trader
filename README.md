# 📊 股票智能分析系统 v2.0

[English](README_EN.md) | 简体中文

基于 Longbridge OpenAPI、Ollama AI 和 LangChain 的股票智能分析系统，提供多维度量化评级和深度分析。

> 🆕 **v2.0 架构升级**: 采用 Agent-Based Architecture，模块化设计，易于扩展！

## ✨ 功能特点

- 🔄 **实时数据获取**: 使用 Longbridge OpenAPI 获取最新股票行情数据
- 🤖 **AI 深度分析**: 基于 Ollama 大语言模型进行智能分析
- 📈 **多维度评级**: 五大维度量化评级体系（基本面、技术面、成长性、市场情绪、行业风险）
- 📝 **自动报告生成**: 自动生成专业的 Markdown 格式分析报告
- ⚙️ **灵活配置**: 通过 .env 文件轻松配置股票列表和系统参数
- 🏗️ **Agent 架构**: 模块化设计，各组件职责清晰，易于维护和扩展

## 🏗️ 系统架构

```
┌──────────────────────────────────────────┐
│         StockAnalysisController          │  ← 全局控制器
│         (统一管理业务流程)               │
└────────────┬─────────────────┬───────────┘
             │                 │
             ▼                 ▼
    ┌─────────────┐   ┌─────────────┐
    │ FetchAgent  │   │AnalyseAgent │
    │ (数据获取)   │   │ (AI分析)     │
    └─────────────┘   └─────────────┘
```

**详细架构说明**: 查看 [ARCHITECTURE.md](ARCHITECTURE.md)

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Ollama (需要本地运行)
- Longbridge 账户和 API 密钥

### 2. 激活虚拟环境

```bash
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置系统

复制配置模板并填写您的信息:

```bash
cp config.example.env .env
```

编辑 `.env` 文件，填写以下配置:

```env
# Longbridge OpenAPI 配置
LONGBRIDGE_APP_KEY=your_app_key_here
LONGBRIDGE_APP_SECRET=your_app_secret_here
LONGBRIDGE_ACCESS_TOKEN=your_access_token_here

# 股票列表（多个股票用逗号分隔）
STOCK_LIST=BABA.US,NVDA.US,TSLA.US,AAPL.US,GOOGL.US

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# 输出配置
OUTPUT_DIR=report
```

### 5. 启动 Ollama

确保 Ollama 服务正在运行:

```bash
# 启动 Ollama
ollama serve

# 在另一个终端拉取模型（如果还没有）
ollama pull deepseek-r1:8b
```

### 6. 运行分析

```bash
python3 main.py
```

或者:

```bash
python3 app.py
```

### 7. 查看报告

分析完成后，报告将生成在 `report/` 目录下。

## 📁 项目结构

```
langchain-demo/
├── main.py                         # 主程序入口
├── app.py                          # 应用入口
├── controller.py                   # 🆕 全局控制器
│
├── agents/                         # 🆕 Agent 模块目录
│   ├── fetch-agent/               # 🆕 数据获取代理
│   │   ├── __init__.py
│   │   └── agent.py               #     FetchAgent 实现
│   │
│   ├── analyse-agent/             # 🆕 分析报告代理
│   │   ├── __init__.py
│   │   └── agent.py               #     AnalyseAgent 实现
│   │
│   └── trade-agent/               # 交易代理（预留）
│       └── agent.py
│
├── strategies/                     # 分析策略
│   └── rating.md                  # 量化评级策略
│
├── report/                         # 报告输出目录
│   ├── .gitkeep
│   └── README.md                  # 报告索引（自动生成）
│
├── config.example.env             # 配置文件模板
├── requirements.txt               # Python 依赖
│
├── README.md                      # 项目文档（本文件）
├── QUICKSTART.md                  # 快速入门指南
├── ARCHITECTURE.md                # 🆕 架构设计文档
└── test_setup.py                  # 配置测试脚本
```

## 🎯 分析策略

系统采用五大维度量化评级体系:

| 维度 | 权重 | 核心指标 |
|------|------|----------|
| **基本面** | 40% | PE/PEG、毛利率、负债率、ROE |
| **技术面** | 30% | MACD、RSI、价格/MA位置 |
| **成长性** | 15% | 营收增长率、资本支出效率 |
| **市场情绪** | 10% | 机构目标价空间、资金流向 |
| **行业风险** | 5% | 政策敏感性、竞争格局 |

详细策略说明请查看 `strategies/rating.md`。

## 📊 报告示例

生成的报告包含以下内容:

1. **报告信息**: 生成时间、分析标的、数据来源
2. **数据快照**: 实时价格、涨跌幅、成交量等
3. **AI 深度分析**:
   - 综合评分表（0-10分制）
   - 关键洞察（机会识别、风险预警）
   - 投资建议
4. **免责声明**: 风险提示
5. **技术说明**: 系统架构说明

## 🔧 高级使用

### 作为 Python 模块使用

```python
from controller import StockAnalysisController

# 方式1: 使用上下文管理器（推荐）
with StockAnalysisController() as controller:
    result = controller.execute_analysis(['NVDA.US', 'AAPL.US'])
    if result['status'] == 'success':
        print(f"报告已生成: {result['report_path']}")

# 方式2: 手动管理
controller = StockAnalysisController()
controller.initialize()
result = controller.execute_analysis(['NVDA.US', 'AAPL.US'])
controller.cleanup()

# 查看执行历史
history = controller.get_execution_history()
print(f"共执行 {len(history)} 次分析")
```

### 单独使用 Agent

```python
# 使用 FetchAgent 获取数据
from agents.fetch_agent import FetchAgent

fetch_agent = FetchAgent()
result = fetch_agent.execute(['NVDA.US'])
print(result['data'])

# 使用 AnalyseAgent 进行分析
from agents.analyse_agent import AnalyseAgent

analyse_agent = AnalyseAgent()
formatted_data = "..."  # 格式化的数据
result = analyse_agent.execute(
    formatted_data=formatted_data,
    stock_symbols=['NVDA.US']
)
print(result['report_path'])
```

### 自定义分析策略

您可以修改 `strategies/rating.md` 来自定义分析策略，系统会自动加载最新的策略文件。

### 更换 AI 模型

在 `.env` 文件中修改 `OLLAMA_MODEL` 参数:

```env
# 使用其他模型
OLLAMA_MODEL=llama3:8b
# 或
OLLAMA_MODEL=qwen2.5:7b
```

## ⚠️ 注意事项

1. **API 限制**: Longbridge API 可能有调用频率限制，请合理安排分析频率
2. **数据延迟**: 实时数据可能存在一定延迟
3. **AI 准确性**: AI 分析结果仅供参考，不构成投资建议
4. **网络要求**: 需要稳定的网络连接来访问 API 和 Ollama 服务

## 🐛 故障排查

### 问题: 无法连接到 Ollama

**解决方案**:
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 如果没有运行，启动 Ollama
ollama serve
```

### 问题: Longbridge API 认证失败

**解决方案**:
- 检查 `.env` 文件中的 API 密钥是否正确
- 确认 API 密钥是否有效且未过期
- 查看 Longbridge 控制台的 API 权限设置

### 问题: 报告生成失败

**解决方案**:
- 检查 `report/` 目录是否有写入权限
- 确认磁盘空间充足
- 查看控制台错误信息

## 📚 相关资源

- [Longbridge OpenAPI 文档](https://open.longbridgeapp.com/docs)
- [Ollama 官方网站](https://ollama.ai/)
- [LangChain 文档](https://python.langchain.com/)

## 📄 许可证

本项目仅供学习和研究使用。

---

**免责声明**: 本系统生成的分析报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。