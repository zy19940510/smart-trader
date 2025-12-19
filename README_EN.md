# 📊 Stock Intelligent Analysis System v2.0

English | [简体中文](README.md)

An agent-based stock analysis system built with **Longbridge OpenAPI**, **Ollama**, and **LangChain**. It fetches real-time market data, runs multi-dimensional AI analysis, and generates professional Markdown reports.

> 🆕 **v2.0 Architecture Upgrade**: Agent-Based Architecture — modular, extensible, and easier to maintain.

## ✨ Features

- **Real-time data**: Fetch latest quotes and basic info via Longbridge OpenAPI
- **AI deep analysis**: Run LLM analysis locally via Ollama
- **Multi-dimensional rating**: 5-dimension quantitative scoring (Fundamentals / Technicals / Growth / Sentiment / Industry risk)
- **Auto report generation**: Generate Markdown reports automatically
- **Flexible config**: Configure stock list and parameters via `.env`
- **Modular agent architecture**: Clear responsibilities, easy to extend

## 🏗️ Architecture (High-level)

```
┌──────────────────────────────────────────┐
│         StockAnalysisController          │
│     (workflow orchestration & lifecycle) │
└────────────┬─────────────────┬───────────┘
             │                 │
             ▼                 ▼
    ┌─────────────┐   ┌─────────────┐
    │ FetchAgent   │   │ AnalyseAgent│
    │ (data fetch) │   │ (AI report) │
    └─────────────┘   └─────────────┘
```

- Detailed design: see [ARCHITECTURE.md](ARCHITECTURE.md) (Chinese)

## 🚀 Quick Start

### 1) Requirements

- Python 3.8+
- Ollama (running locally)
- A Longbridge account + API credentials

### 2) Create/activate virtual environment (optional but recommended)

```bash
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure `.env`

Copy the template and edit it:

```bash
cp config.example.env .env
```

Example:

```env
# Longbridge OpenAPI
LONGBRIDGE_APP_KEY=your_app_key_here
LONGBRIDGE_APP_SECRET=your_app_secret_here
LONGBRIDGE_ACCESS_TOKEN=your_access_token_here

# Stock list (comma-separated)
STOCK_LIST=BABA.US,NVDA.US,TSLA.US,AAPL.US,GOOGL.US

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# Output
OUTPUT_DIR=report
```

### 5) Start Ollama and pull the model

```bash
ollama serve
```

In another terminal:

```bash
ollama pull deepseek-r1:8b
```

### 6) Run analysis

```bash
python3 main.py
```

Or:

```bash
python3 app.py
```

### 7) View reports

Reports will be generated under `report/`.

## 📁 Project Structure

```
smart-trader/
├── main.py                         # Main entry
├── app.py                          # App entry
├── controller.py                   # Global controller
│
├── agents/                         # Agents
│   ├── fetch_agent/                # FetchAgent implementation
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── analyse_agent/              # AnalyseAgent implementation
│   │   ├── __init__.py
│   │   └── agent.py
│   └── trade_agent/                # Trade agent (reserved)
│       └── agent.py
│
├── strategies/
│   └── rating.md                   # Quantitative rating strategy
│
├── report/                         # Report output directory
│   ├── README.md                   # Report index (auto-generated)
│   └── ...
│
├── config.example.env              # Config template
├── requirements.txt                # Python dependencies
│
├── README.md                       # Chinese README
├── README_EN.md                    # English README (this file)
└── QUICKSTART.md                   # Quickstart guide (Chinese)
```

## 🎯 Rating Strategy

The system uses a 5-dimension rating framework:

| Dimension | Weight | Key Metrics |
|---|---:|---|
| **Fundamentals** | 40% | PE/PEG, gross margin, debt ratio, ROE |
| **Technicals** | 30% | MACD, RSI, price vs MA |
| **Growth** | 15% | revenue growth, capex efficiency |
| **Sentiment** | 10% | analyst target upside, fund flow |
| **Industry Risk** | 5% | policy sensitivity, competitive landscape |

See `strategies/rating.md` for details.

## 🔧 Advanced Usage

### Use as a Python module

```python
from controller import StockAnalysisController

with StockAnalysisController() as controller:
    result = controller.execute_analysis(["NVDA.US", "AAPL.US"])
    if result["status"] == "success":
        print(f"Report generated: {result['report_path']}")
```

### Use individual agents

```python
from agents.fetch_agent import FetchAgent
from agents.analyse_agent import AnalyseAgent

fetch_agent = FetchAgent()
fetch_result = fetch_agent.execute(["NVDA.US"])

analyse_agent = AnalyseAgent()
formatted_data = "..."  # formatted text input for AI
analyse_result = analyse_agent.execute(
    formatted_data=formatted_data,
    stock_symbols=["NVDA.US"],
)
print(analyse_result["report_path"])
```

## 🐛 Troubleshooting

### Cannot connect to Ollama

```bash
curl http://localhost:11434/api/tags
ollama serve
```

### Longbridge authentication failed

- Verify credentials in `.env`
- Ensure the token is valid and not expired
- Check API permissions/settings in Longbridge console

### Report generation failed

- Ensure `report/` is writable
- Check disk space
- Review console errors

## 📚 Resources

- [Longbridge OpenAPI Docs](https://open.longbridgeapp.com/docs)
- [Ollama](https://ollama.ai/)
- [LangChain Docs](https://python.langchain.com/)

## 📄 License & Disclaimer

This project is for learning and research only.

**Disclaimer**: AI-generated analysis is for reference only and does not constitute investment advice. Investing involves risk.


