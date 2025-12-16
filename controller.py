"""
全局控制器 - Controller
统一管理所有 Agent 的调用和业务流程
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from agents.fetch_agent import FetchAgent
from agents.analyse_agent import AnalyseAgent


class StockAnalysisController:
    """
    股票分析系统全局控制器
    职责：
    1. 管理 Agent 生命周期
    2. 协调 Agent 之间的数据流转
    3. 控制整体业务流程
    4. 统一的错误处理和日志记录
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化控制器
        
        Args:
            config: 配置字典，如果为 None 则从环境变量加载
        """
        # 加载环境变量
        load_dotenv()
        
        # 初始化配置
        self.config = config or self._load_config()
        
        # 初始化 Agents
        self.fetch_agent: Optional[FetchAgent] = None
        self.analyse_agent: Optional[AnalyseAgent] = None
        
        # 执行状态
        self.is_initialized = False
        self.execution_history = []
        
        self._print_banner()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        从环境变量加载配置
        
        Returns:
            配置字典
        """
        return {
            "stock_list": os.getenv("STOCK_LIST", "NVDA.US,AAPL.US"),
            "ollama_model": os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "output_dir": os.getenv("OUTPUT_DIR", "report"),
            "strategy_path": "strategies/rating.md",
        }
    
    def _print_banner(self):
        """打印系统横幅"""
        print("\n" + "=" * 70)
        print("📊 股票智能分析系统 - 全局控制器")
        print("=" * 70)
        print("架构模式: Agent-Based Architecture")
        print("控制器版本: v2.0")
        print("=" * 70 + "\n")
    
    def initialize(self) -> bool:
        """
        初始化所有 Agents
        
        Returns:
            是否初始化成功
        """
        print("[Controller] 正在初始化系统组件...\n")
        
        try:
            # 1. 初始化 Fetch Agent
            print("[Controller] 初始化 Fetch Agent...")
            self.fetch_agent = FetchAgent()
            
            # 2. 初始化 Analyse Agent
            print("[Controller] 初始化 Analyse Agent...")
            self.analyse_agent = AnalyseAgent(
                strategy_path=self.config["strategy_path"],
                model=self.config["ollama_model"],
                base_url=self.config["ollama_base_url"],
                output_dir=self.config["output_dir"]
            )
            
            self.is_initialized = True
            print("\n✓ [Controller] 所有组件初始化成功\n")
            return True
            
        except Exception as e:
            print(f"\n✗ [Controller] 初始化失败: {e}\n")
            self.is_initialized = False
            return False
    
    def execute_analysis(self, stock_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行完整的股票分析流程
        
        Args:
            stock_symbols: 股票代码列表，如果为 None 则从配置读取
            
        Returns:
            执行结果字典
        """
        # 检查初始化状态
        if not self.is_initialized:
            print("[Controller] 系统未初始化，正在初始化...")
            if not self.initialize():
                return {
                    "status": "error",
                    "error": "系统初始化失败",
                    "timestamp": datetime.now().isoformat()
                }
        
        # 获取股票列表
        if stock_symbols is None:
            stock_symbols = self._parse_stock_list()
        
        if not stock_symbols:
            return {
                "status": "error",
                "error": "股票列表为空",
                "timestamp": datetime.now().isoformat()
            }
        
        # 开始执行流程
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("\n" + "=" * 70)
        print(f"[Controller] 开始执行分析流程 (ID: {execution_id})")
        print(f"[Controller] 分析标的: {', '.join(stock_symbols)}")
        print("=" * 70)
        
        result = {
            "execution_id": execution_id,
            "symbols": stock_symbols,
            "stages": {},
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # ============ 阶段 1: 数据获取 ============
            print(f"\n{'>'*70}")
            print("阶段 1/2: 数据获取")
            print(f"{'>'*70}")
            
            fetch_result = self.fetch_agent.execute(stock_symbols)
            result["stages"]["fetch"] = fetch_result
            
            if fetch_result["status"] != "success":
                raise Exception(f"数据获取失败: {fetch_result.get('error')}")
            
            # 格式化数据供分析使用
            formatted_data = self.fetch_agent.format_for_analysis(fetch_result)
            
            # ============ 阶段 2: AI 分析和报告生成 ============
            print(f"\n{'>'*70}")
            print("阶段 2/2: AI 分析和报告生成")
            print(f"{'>'*70}")
            
            analyse_result = self.analyse_agent.execute(
                formatted_data=formatted_data,
                stock_symbols=stock_symbols,
                raw_data=fetch_result
            )
            result["stages"]["analyse"] = analyse_result
            
            if analyse_result["status"] != "success":
                raise Exception(f"分析失败: {analyse_result.get('error')}")
            
            # ============ 完成 ============
            result["status"] = "success"
            result["report_path"] = analyse_result.get("report_path")
            result["end_time"] = datetime.now().isoformat()
            
            # 记录到历史
            self.execution_history.append(result)
            
            # 打印成功摘要
            self._print_success_summary(result)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ [Controller] 执行失败: {error_msg}\n")
            
            result["status"] = "error"
            result["error"] = error_msg
            result["end_time"] = datetime.now().isoformat()
            
            self.execution_history.append(result)
            
            return result
    
    def _parse_stock_list(self) -> List[str]:
        """
        从配置解析股票列表
        
        Returns:
            股票代码列表
        """
        stock_list_str = self.config.get("stock_list", "")
        if not stock_list_str:
            print("⚠️  [Controller] 未配置股票列表")
            return []
        
        stocks = [s.strip() for s in stock_list_str.split(",") if s.strip()]
        return stocks
    
    def _print_success_summary(self, result: Dict[str, Any]):
        """
        打印成功执行摘要
        
        Args:
            result: 执行结果
        """
        print("\n" + "=" * 70)
        print("✅ 分析流程执行完成!")
        print("=" * 70)
        print(f"执行ID: {result['execution_id']}")
        print(f"分析标的: {', '.join(result['symbols'])}")
        print(f"数据获取: ✓ 成功 ({result['stages']['fetch']['count']} 只股票)")
        print(f"AI 分析: ✓ 成功")
        print(f"报告路径: {os.path.abspath(result['report_path'])}")
        print(f"总耗时: {self._calculate_duration(result)}")
        print("=" * 70 + "\n")
    
    def _calculate_duration(self, result: Dict[str, Any]) -> str:
        """
        计算执行耗时
        
        Args:
            result: 执行结果
            
        Returns:
            耗时字符串
        """
        try:
            start = datetime.fromisoformat(result["start_time"])
            end = datetime.fromisoformat(result["end_time"])
            duration = (end - start).total_seconds()
            return f"{duration:.2f} 秒"
        except:
            return "未知"
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Returns:
            执行历史列表
        """
        return self.execution_history
    
    def get_last_execution(self) -> Optional[Dict[str, Any]]:
        """
        获取最后一次执行结果
        
        Returns:
            最后一次执行结果，如果没有则返回 None
        """
        if self.execution_history:
            return self.execution_history[-1]
        return None
    
    def cleanup(self):
        """清理资源"""
        print("\n[Controller] 正在清理资源...")
        
        try:
            if self.fetch_agent:
                self.fetch_agent.close()
            
            print("✓ [Controller] 资源清理完成")
            
        except Exception as e:
            print(f"⚠️  [Controller] 清理资源时出错: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        return {
            "is_initialized": self.is_initialized,
            "config": self.config,
            "execution_count": len(self.execution_history),
            "agents": {
                "fetch_agent": "已初始化" if self.fetch_agent else "未初始化",
                "analyse_agent": "已初始化" if self.analyse_agent else "未初始化",
            }
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()


# 测试代码
if __name__ == "__main__":
    print("测试全局控制器\n")
    
    # 使用上下文管理器
    with StockAnalysisController() as controller:
        # 获取系统信息
        info = controller.get_system_info()
        print("\n系统信息:")
        print(f"初始化状态: {info['is_initialized']}")
        print(f"配置: {info['config']}")
        
        # 执行分析（使用较少的股票进行测试）
        result = controller.execute_analysis(["NVDA.US"])
        
        if result["status"] == "success":
            print("\n✓ 测试成功!")
            print(f"报告路径: {result['report_path']}")
        else:
            print("\n✗ 测试失败!")
            print(f"错误: {result.get('error')}")

