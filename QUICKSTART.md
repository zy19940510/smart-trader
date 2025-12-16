# 🚀 快速入门指南

## 第一步：安装依赖

```bash
# 激活虚拟环境（如果有）
source .venv/bin/activate

# 安装所需的 Python 包
pip install -r requirements.txt
```

## 第二步：配置 Longbridge API

1. 访问 [Longbridge 开放平台](https://open.longbridgeapp.com/)
2. 登录并获取 API 密钥：
   - App Key
   - App Secret
   - Access Token

## 第三步：创建配置文件

```bash
# 复制配置模板
cp config.example.env .env

# 编辑配置文件
nano .env  # 或使用您喜欢的编辑器
```

在 `.env` 文件中填写：

```env
# 填写您的 Longbridge API 信息
LONGBRIDGE_APP_KEY=实际的app_key
LONGBRIDGE_APP_SECRET=实际的app_secret
LONGBRIDGE_ACCESS_TOKEN=实际的access_token

# 设置要分析的股票列表（用逗号分隔）
STOCK_LIST=BABA.US,NVDA.US,TSLA.US

# Ollama 配置（通常保持默认即可）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b

# 输出目录（通常保持默认即可）
OUTPUT_DIR=report
```

## 第四步：安装和启动 Ollama

### macOS / Linux

```bash
# 下载并安装 Ollama（如果还没有安装）
# 访问 https://ollama.ai/ 下载安装包

# 启动 Ollama 服务
ollama serve

# 在另一个终端窗口，拉取模型
ollama pull deepseek-r1:8b
```

### Windows

请访问 [Ollama 官网](https://ollama.ai/) 下载 Windows 版本并按照说明安装。

## 第五步：测试配置

```bash
# 运行配置测试脚本
python test_setup.py
```

这个脚本会检查：
- ✓ Python 版本
- ✓ 依赖包安装
- ✓ 配置文件
- ✓ Ollama 服务
- ✓ 策略文件
- ✓ 输出目录

如果所有检查都通过，您就可以开始使用了！

## 第六步：运行分析

```bash
# 运行主程序
python main.py

# 或者
python app.py
```

程序会：
1. 📡 从 Longbridge API 获取股票数据
2. 🤖 使用 AI 进行深度分析
3. 📄 生成分析报告（保存在 `report/` 目录）

## 第七步：查看报告

分析完成后，您可以在 `report/` 目录中找到生成的 Markdown 报告：

```bash
# 查看报告列表
ls -la report/

# 使用 Markdown 阅读器查看报告
# 或在文本编辑器中打开
```

报告包含：
- 📊 综合评分表
- 🎯 机会识别
- ⚠️ 风险预警
- 💡 投资建议

## 常见问题

### Q1: 提示 "无法连接到 Ollama"

**解决方案**：
```bash
# 在新终端窗口运行
ollama serve
```

### Q2: Longbridge API 认证失败

**解决方案**：
- 检查 `.env` 文件中的 API 密钥是否正确
- 确认 API 密钥未过期
- 访问 Longbridge 控制台查看 API 状态

### Q3: 找不到某个 Python 包

**解决方案**：
```bash
# 重新安装依赖
pip install -r requirements.txt --upgrade
```

### Q4: 模型下载速度慢

**解决方案**：
- 使用更小的模型：`ollama pull qwen2.5:3b`
- 修改 `.env` 中的 `OLLAMA_MODEL=qwen2.5:3b`

## 进阶使用

### 自定义股票列表

编辑 `.env` 文件中的 `STOCK_LIST`：

```env
# 美股示例
STOCK_LIST=AAPL.US,MSFT.US,GOOGL.US,AMZN.US

# 港股示例
STOCK_LIST=00700.HK,09988.HK,03690.HK

# 混合示例
STOCK_LIST=AAPL.US,00700.HK,BABA.US
```

### 作为 Python 模块使用

```python
from main import StockAnalysisSystem

# 创建实例
system = StockAnalysisSystem()

# 分析指定股票
report = system.run_analysis(['NVDA.US', 'TSLA.US'])

print(f"报告已生成: {report}")
```

### 修改分析策略

编辑 `strategies/rating.md` 文件来自定义分析策略和评分标准。

## 需要帮助？

- 📖 查看完整文档：`README.md`
- 🐛 遇到问题：在 GitHub 上提交 Issue
- 💬 技术交流：查看项目讨论区

---

**提示**：首次运行可能需要较长时间，因为 AI 模型需要加载。请耐心等待。

**免责声明**：本系统生成的分析仅供参考，不构成投资建议。投资有风险，入市需谨慎！

