"""
Analyse Agent - 分析和报告代理
负责 AI 分析和报告生成
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


class AnalyseAgent:
    """
    分析代理
    职责：使用 AI 进行股票分析并生成报告
    """
    
    def __init__(self, 
                 strategy_path: str = "strategies/rating.md",
                 model: str = None,
                 base_url: str = None,
                 output_dir: str = "report"):
        """
        初始化 Analyse Agent
        
        Args:
            strategy_path: 分析策略文件路径
            model: Ollama 模型名称
            base_url: Ollama 服务地址
            output_dir: 报告输出目录
        """
        self.strategy_path = strategy_path
        self.model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.output_dir = output_dir or os.getenv("OUTPUT_DIR", "report")
        
        self.strategy = None
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """初始化 AI 模型和策略"""
        try:
            # 加载分析策略
            self.strategy = self._load_strategy()
            
            # 初始化 AI 模型
            self.llm = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=0.7,
            )
            
            print(f"✓ [AnalyseAgent] AI 模型已初始化: {self.model}")
            print(f"✓ [AnalyseAgent] 分析策略已加载: {self.strategy_path}")
            
        except Exception as e:
            print(f"✗ [AnalyseAgent] 初始化失败: {e}")
            raise
    
    def _load_strategy(self) -> str:
        """
        加载分析策略
        
        Returns:
            策略内容
        """
        try:
            with open(self.strategy_path, 'r', encoding='utf-8') as f:
                strategy = f.read()
            return strategy
        except Exception as e:
            print(f"✗ [AnalyseAgent] 加载策略失败: {e}")
            raise
    
    def execute(self, formatted_data: str, stock_symbols: list, 
                raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行分析任务
        
        Args:
            formatted_data: 格式化的股票数据文本
            stock_symbols: 股票代码列表
            raw_data: 原始股票数据（用于报告生成）
            
        Returns:
            包含分析结果和报告路径的字典
        """
        print(f"\n{'='*60}")
        print(f"[AnalyseAgent] 开始分析 {len(stock_symbols)} 只股票")
        print(f"{'='*60}")
        
        try:
            # 1. AI 分析
            print("\n[AnalyseAgent] 步骤 1/2: 执行 AI 分析...")
            analysis_result = self._analyze_with_ai(formatted_data)
            
            if not analysis_result or "分析失败" in analysis_result:
                raise ValueError("AI 分析未能产生有效结果")
            
            print(f"✓ [AnalyseAgent] AI 分析完成 ({len(analysis_result)} 字符)")
            
            # 2. 生成报告
            print("\n[AnalyseAgent] 步骤 2/2: 生成分析报告...")
            report_path = self._generate_report(
                analysis_result, 
                stock_symbols, 
                raw_data
            )
            
            if not report_path:
                raise ValueError("报告生成失败")
            
            print(f"✓ [AnalyseAgent] 报告已生成: {report_path}")
            
            # 3. 更新报告索引
            self._update_report_index()
            
            return {
                "status": "success",
                "analysis": analysis_result,
                "report_path": report_path,
                "timestamp": datetime.now().isoformat(),
                "symbols": stock_symbols
            }
            
        except Exception as e:
            error_msg = f"分析失败: {e}"
            print(f"✗ [AnalyseAgent] {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_with_ai(self, formatted_data: str, max_retries: int = 3) -> str:
        """
        使用 AI 进行分析（带重试机制）
        
        Args:
            formatted_data: 格式化的数据
            max_retries: 最大重试次数
            
        Returns:
            分析结果
        """
        # 构建系统提示
        system_prompt = """你是一位专业的股票分析师，擅长根据量化指标和市场数据进行深度分析。
请严格按照提供的分析策略框架，对给定的股票数据进行全面评估。

注意事项：
1. 严格按照策略中的评分标准进行量化评分
2. 提供具体的数据支撑和逻辑推理
3. 识别潜在的投资机会和风险点
4. 使用清晰的 Markdown 格式输出
5. 由于数据有限，对于无法获取的指标，请根据价格走势、成交量等可获得的数据进行合理推断
6. 重点分析技术面指标：价格走势、涨跌幅、成交量等
7. 输出完整的分析报告，包括综合评分表和关键洞察"""

        # 构建用户提示
        user_prompt = f"""# 分析任务

## 分析策略框架
{self.strategy}

## 股票实时数据
{formatted_data}

请根据以上策略和数据，生成完整的股票分析报告。报告需要包括：
1. 综合评分表（包含每只股票的技术面、基本面、成长性评分和综合评级）
2. 关键洞察（机会识别、风险预警、投资建议）
3. 详细分析说明

请开始分析："""

        # 重试逻辑
        for attempt in range(max_retries):
            try:
                print(f"   第 {attempt + 1}/{max_retries} 次尝试...")
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = self.llm.invoke(messages)
                
                if hasattr(response, 'content') and response.content:
                    return response.content
                else:
                    print(f"   ⚠️  响应格式异常，重试...")
                    
            except Exception as e:
                print(f"   ⚠️  尝试失败: {e}")
                if attempt == max_retries - 1:
                    raise
        
        return "分析失败：已达到最大重试次数"
    
    def _generate_report(self, analysis_result: str, stock_symbols: list,
                        raw_data: Dict[str, Any] = None) -> str:
        """
        生成分析报告
        
        Args:
            analysis_result: AI 分析结果
            stock_symbols: 股票代码列表
            raw_data: 原始数据
            
        Returns:
            报告文件路径
        """
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbols_str = "_".join([s.split('.')[0] for s in stock_symbols[:3]])
        filename = f"stock_analysis_{symbols_str}_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # 构建报告内容
        report_content = self._build_report_content(
            analysis_result,
            stock_symbols,
            raw_data,
            timestamp
        )
        
        # 保存报告
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return filepath
        except Exception as e:
            print(f"✗ [AnalyseAgent] 保存报告失败: {e}")
            return ""
    
    def _build_report_content(self, analysis_result: str, stock_symbols: list,
                             raw_data: Dict[str, Any], timestamp: str) -> str:
        """
        构建报告内容
        
        Args:
            analysis_result: AI 分析结果
            stock_symbols: 股票代码列表
            raw_data: 原始数据
            timestamp: 时间戳
            
        Returns:
            完整的报告内容
        """
        # 格式化时间
        formatted_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime(
            "%Y年%m月%d日 %H:%M:%S"
        )
        
        report = f"""# 📊 股票智能分析报告

---

## 📋 报告信息

- **生成时间**: {formatted_time}
- **分析标的**: {', '.join(stock_symbols)}
- **分析模型**: 基于多维度量化评级体系
- **数据来源**: Longbridge OpenAPI
- **AI 引擎**: {self.model}

---

"""
        
        # 添加数据快照
        if raw_data and raw_data.get("status") == "success":
            report += "## 📈 数据快照\n\n"
            for symbol, data in raw_data.get("data", {}).items():
                price = data.get('price', {})
                report += f"### {data.get('name', symbol)} ({symbol})\n\n"
                report += f"- **当前价格**: ${price.get('last_done', 0):.2f}\n"
                report += f"- **涨跌幅**: {price.get('change_pct', 0):+.2f}%\n"
                report += f"- **成交量**: {data.get('volume', 0):,}\n"
                report += f"- **成交额**: ${data.get('turnover', 0):,.2f}\n\n"
            report += "---\n\n"
        
        # 添加 AI 分析结果
        report += "## 🤖 AI 深度分析\n\n"
        report += analysis_result
        report += "\n\n---\n\n"
        
        # 添加免责声明
        report += self._get_disclaimer()
        
        # 添加页脚
        report += self._get_footer()
        
        return report
    
    def _get_disclaimer(self) -> str:
        """获取免责声明"""
        return """## ⚠️ 免责声明

本报告由 AI 系统自动生成，仅供参考，不构成投资建议。报告内容基于：
1. 实时市场数据（可能存在延迟）
2. 量化分析模型（存在局限性）
3. AI 推理结果（可能存在偏差）

**投资有风险，入市需谨慎。** 请结合自身风险承受能力和投资目标，独立做出投资决策。
建议在做出任何投资决定前咨询专业的金融顾问。

"""
    
    def _get_footer(self) -> str:
        """获取报告页脚"""
        return f"""---

## 📌 技术说明

- **数据接口**: Longbridge OpenAPI
- **AI 引擎**: Ollama ({self.model})
- **分析框架**: LangChain
- **评级体系**: 五维度量化评级（基本面、技术面、成长性、市场情绪、行业风险）

---

*本报告由股票智能分析系统自动生成 - Powered by AnalyseAgent*
"""
    
    def _update_report_index(self):
        """更新报告索引"""
        index_path = os.path.join(self.output_dir, "README.md")
        
        # 获取所有报告文件
        try:
            reports = [f for f in os.listdir(self.output_dir)
                      if f.startswith("stock_analysis_") and f.endswith(".md")]
            reports.sort(reverse=True)
        except:
            reports = []
        
        # 构建索引内容
        index_content = "# 📊 股票分析报告索引\n\n"
        index_content += f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        index_content += f"**报告总数**: {len(reports)}\n\n"
        index_content += "---\n\n"
        index_content += "## 📁 报告列表\n\n"
        
        if reports:
            for report in reports:
                parts = report.replace("stock_analysis_", "").replace(".md", "").split("_")
                if len(parts) >= 3:
                    symbols = "_".join(parts[:-2])
                    timestamp = parts[-2] + "_" + parts[-1]
                    try:
                        time_str = datetime.strptime(
                            timestamp,
                            "%Y%m%d_%H%M%S"
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        time_str = timestamp
                    
                    index_content += f"- [{symbols}]({report}) - {time_str}\n"
                else:
                    index_content += f"- [{report}]({report})\n"
        else:
            index_content += "*暂无报告*\n"
        
        # 保存索引
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            print(f"✓ [AnalyseAgent] 报告索引已更新")
        except Exception as e:
            print(f"⚠️  [AnalyseAgent] 更新索引失败: {e}")


# 测试代码
if __name__ == "__main__":
    print("测试 Analyse Agent\n")
    
    agent = AnalyseAgent()
    
    # 测试数据
    test_data = """# 股票实时数据

## 英伟达 (NVDA.US)

### 💰 价格信息
- **当前价格**: $850.50
- **涨跌幅**: +2.35%
- **开盘价**: $835.00

### 📊 成交信息
- **成交量**: 45,234,567
"""
    
    result = agent.execute(
        formatted_data=test_data,
        stock_symbols=["NVDA.US"],
        raw_data=None
    )
    
    print(f"\n执行结果:")
    print(f"状态: {result['status']}")
    if result['status'] == 'success':
        print(f"报告路径: {result['report_path']}")
