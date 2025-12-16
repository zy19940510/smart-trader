"""
股票智能分析系统 - 应用入口
此文件提供了一个简化的入口点，可以直接运行或作为模块导入

新架构 (v2.0):
- Controller: 全局控制器，统一管理业务流程
- FetchAgent: 数据获取代理
- AnalyseAgent: 分析报告代理
"""
import sys
from controller import StockAnalysisController
from main import main

# 导出主要接口
__all__ = ['StockAnalysisController', 'main']

# 如果直接运行此文件，调用主函数
if __name__ == "__main__":
    sys.exit(main())

