#!/usr/bin/env python3
"""
股票智能分析系统 - 主程序入口
使用新的 Agent 架构和全局控制器
"""
import sys
from controller import StockAnalysisController


# 保留旧的类名以保持向后兼容
StockAnalysisSystem = StockAnalysisController


def print_usage():
    """打印使用说明"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         📊 股票智能分析系统 v2.0 - Agent 架构版              ║
╚═══════════════════════════════════════════════════════════════╝

🚀 使用说明:
─────────────────────────────────────────────────────────────────
1. 配置环境变量:
   cp config.example.env .env
   
   然后编辑 .env 文件填写:
   - LONGBRIDGE_APP_KEY: Longbridge API Key
   - LONGBRIDGE_APP_SECRET: Longbridge API Secret
   - LONGBRIDGE_ACCESS_TOKEN: Longbridge Access Token
   - STOCK_LIST: 股票列表，如 "BABA.US,NVDA.US,TSLA.US"

2. 运行分析:
   python main.py
   
3. 查看报告:
   报告将生成在 report/ 目录下

📐 系统架构:
─────────────────────────────────────────────────────────────────
  Controller (全局控制器)
      ├── FetchAgent (数据获取代理)
      └── AnalyseAgent (分析报告代理)

⚙️ 环境要求:
─────────────────────────────────────────────────────────────────
- Python 3.8+
- Ollama 服务运行在 localhost:11434
- 已安装所需依赖: pip install -r requirements.txt

📖 更多信息请参考:
─────────────────────────────────────────────────────────────────
- 完整文档: README.md
- 快速开始: QUICKSTART.md
- 配置测试: python test_setup.py
""")


def main():
    """主函数"""
    import os
    
    # 检查是否需要帮助
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        return 0
    
    # 检查环境变量
    if not os.path.exists('.env'):
        print("\n⚠️  警告: 未找到 .env 配置文件")
        print("请复制 config.example.env 为 .env 并配置相关参数\n")
        
        try:
            response = input("是否继续使用默认配置运行? (y/N): ")
            if response.lower() != 'y':
                print("程序退出")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\n程序退出")
            return 1
    
    # 使用上下文管理器运行分析
    try:
        with StockAnalysisController() as controller:
            # 执行分析
            result = controller.execute_analysis()
            
            if result["status"] == "success":
                print("\n💡 提示: 您可以使用 Markdown 阅读器查看报告")
                return 0
            else:
                print(f"\n❌ 分析失败: {result.get('error', '未知错误')}")
                return 1
                
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
        return 1
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

