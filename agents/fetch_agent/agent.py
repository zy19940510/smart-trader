"""
Fetch Agent - 数据获取代理
负责从 Longbridge OpenAPI 获取股票数据
"""
import os
from typing import List, Dict, Any, Optional
from longport.openapi import Config, QuoteContext
from datetime import datetime


class FetchAgent:
    """
    数据获取代理
    职责：从外部 API 获取股票数据并进行预处理
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化 Fetch Agent
        
        Args:
            config: Longbridge 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        self.quote_ctx = None
        self._initialize()
    
    def _initialize(self):
        """初始化连接"""
        try:
            self.quote_ctx = QuoteContext(self.config)
            print("✓ [FetchAgent] 已连接到 Longbridge API")
        except Exception as e:
            print(f"✗ [FetchAgent] 连接失败: {e}")
            raise
    
    def execute(self, symbols: List[str]) -> Dict[str, Any]:
        """
        执行数据获取任务
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            包含股票数据的字典
        """
        print(f"\n{'='*60}")
        print(f"[FetchAgent] 开始获取 {len(symbols)} 只股票的数据")
        print(f"{'='*60}")
        
        try:
            # 获取实时行情
            stock_data = self._fetch_quotes(symbols)
            
            # 数据验证
            if not stock_data:
                raise ValueError("未能获取任何股票数据")

            # 标记缺失的股票（API 可能返回子集，例如代码无效/暂不可交易）
            requested_set = set(symbols)
            returned_set = set(stock_data.keys())
            missing = [s for s in symbols if s in requested_set and s not in returned_set]
            if missing:
                print(f"⚠️  [FetchAgent] 有 {len(missing)} 只股票未返回行情数据: {', '.join(missing)}")
            
            print(f"✓ [FetchAgent] 成功获取 {len(stock_data)} 只股票的数据")
            
            return {
                "status": "success",
                "data": stock_data,
                "timestamp": datetime.now().isoformat(),
                "count": len(stock_data),
                "requested": symbols,
                "missing": missing
            }
            
        except Exception as e:
            error_msg = f"数据获取失败: {e}"
            print(f"✗ [FetchAgent] {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "data": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _fetch_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        获取股票行情数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            股票数据字典
        """
        stock_data = {}
        
        # 获取实时行情
        quotes = self.quote_ctx.quote(symbols)
        
        for quote in quotes:
            symbol = quote.symbol
            
            # 基础价格信息
            stock_info = {
                "symbol": symbol,
                "name": self._get_stock_name(symbol),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price": {
                    "last_done": float(quote.last_done) if quote.last_done else 0,
                    "open": float(quote.open) if quote.open else 0,
                    "high": float(quote.high) if quote.high else 0,
                    "low": float(quote.low) if quote.low else 0,
                    "prev_close": float(quote.prev_close) if quote.prev_close else 0,
                },
                "volume": int(quote.volume) if quote.volume else 0,
                "turnover": float(quote.turnover) if quote.turnover else 0,
            }
            
            # 计算涨跌幅
            if quote.prev_close and quote.last_done:
                change_pct = ((float(quote.last_done) - float(quote.prev_close)) / 
                             float(quote.prev_close) * 100)
                stock_info["price"]["change_pct"] = round(change_pct, 2)
            else:
                stock_info["price"]["change_pct"] = 0
            
            # 获取静态信息
            try:
                static_info = self.quote_ctx.static_info([symbol])
                if static_info and len(static_info) > 0:
                    info = static_info[0]
                    stock_info["fundamentals"] = {
                        "name_cn": info.name_cn if hasattr(info, 'name_cn') else "",
                        "name_en": info.name_en if hasattr(info, 'name_en') else "",
                    }
            except Exception as e:
                print(f"⚠️  [FetchAgent] 获取 {symbol} 静态信息失败: {e}")
                stock_info["fundamentals"] = {}
            
            stock_data[symbol] = stock_info
            print(f"   ✓ {symbol}: ${stock_info['price']['last_done']:.2f} ({stock_info['price']['change_pct']:+.2f}%)")
        
        return stock_data
    
    def _get_stock_name(self, symbol: str) -> str:
        """
        获取股票名称
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票名称
        """
        # 简单的名称映射
        name_map = {
            "BABA.US": "阿里巴巴",
            "NVDA.US": "英伟达",
            "TSLA.US": "特斯拉",
            "AAPL.US": "苹果",
            "GOOGL.US": "谷歌",
            "MSFT.US": "微软",
            "AMZN.US": "亚马逊",
            "META.US": "Meta",
            "00700.HK": "腾讯控股",
            "09988.HK": "阿里巴巴-SW",
        }
        return name_map.get(symbol, symbol)
    
    def format_for_analysis(self, fetch_result: Dict[str, Any]) -> str:
        """
        将获取的数据格式化为适合分析的文本格式
        
        Args:
            fetch_result: execute() 方法的返回结果
            
        Returns:
            格式化的文本
        """
        if fetch_result["status"] != "success":
            return f"数据获取失败: {fetch_result.get('error', '未知错误')}"
        
        stock_data = fetch_result["data"]
        formatted_text = "# 股票实时数据\n\n"
        formatted_text += f"**数据获取时间**: {fetch_result['timestamp']}\n\n"
        formatted_text += "---\n\n"
        
        for symbol, data in stock_data.items():
            formatted_text += f"## {data['name']} ({symbol})\n\n"
            
            # 价格信息
            price = data['price']
            formatted_text += "### 💰 价格信息\n\n"
            formatted_text += f"- **当前价格**: ${price['last_done']:.2f}\n"
            formatted_text += f"- **涨跌幅**: {price['change_pct']:+.2f}%\n"
            formatted_text += f"- **开盘价**: ${price['open']:.2f}\n"
            formatted_text += f"- **最高价**: ${price['high']:.2f}\n"
            formatted_text += f"- **最低价**: ${price['low']:.2f}\n"
            formatted_text += f"- **昨收价**: ${price['prev_close']:.2f}\n\n"
            
            # 成交信息
            formatted_text += "### 📊 成交信息\n\n"
            formatted_text += f"- **成交量**: {data['volume']:,}\n"
            formatted_text += f"- **成交额**: ${data['turnover']:,.2f}\n\n"
            
            formatted_text += "---\n\n"
        
        return formatted_text
    
    def close(self):
        """关闭连接"""
        # Longbridge SDK 会自动管理连接
        print("✓ [FetchAgent] 连接已关闭")


# 测试代码
if __name__ == "__main__":
    print("测试 Fetch Agent\n")
    
    agent = FetchAgent()
    
    # 测试数据获取
    result = agent.execute(["NVDA.US", "AAPL.US"])
    
    print("\n获取结果:")
    print(f"状态: {result['status']}")
    print(f"数据数量: {result['count']}")
    
    if result['status'] == 'success':
        # 测试格式化
        formatted = agent.format_for_analysis(result)
        print("\n格式化数据（前500字符）:")
        print(formatted[:500] + "...")
    
    agent.close()

