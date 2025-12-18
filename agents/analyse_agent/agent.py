"""
Analyse Agent - 分析和报告代理
负责 AI 分析和报告生成
"""
import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Dict, Any, Optional, List, Tuple
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
                 provider: str = None,
                 output_dir: str = "report"):
        """
        初始化 Analyse Agent
        
        Args:
            strategy_path: 分析策略文件路径
            model: 模型名称（Ollama 或火山方舟）
            base_url: 模型服务地址（Ollama base_url 或 ARK base_url）
            provider: LLM 提供方：ollama / ark
            output_dir: 报告输出目录
        """
        self.strategy_path = strategy_path
        self.provider = (provider or os.getenv("LLM_PROVIDER", "ollama") or "ollama").strip().lower()
        if self.provider == "ark":
            self.model = model or os.getenv("ARK_MODEL", "deepseek-v3-2-251201")
            self.base_url = base_url or os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
            self._api_key_env = "ARK_API_KEY"
        elif self.provider == "one":
            self.model = model or os.getenv("ONE_MODEL", "gpt-5.1")
            self.base_url = base_url or os.getenv("ONE_BASE_URL", "https://lboneapi.longbridge-inc.com")
            self._api_key_env = "ONE_API_KEY"
        else:
            self.provider = "ollama"
            self.model = model or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
            self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self._api_key_env = ""

        self.output_dir = output_dir or os.getenv("OUTPUT_DIR", "report")
        # 单股超时（秒）。0 表示不超时（默认保持兼容）；建议在本机较慢时设置如 180 或 300
        try:
            self.stock_timeout_s = float(os.getenv("ANALYSE_STOCK_TIMEOUT", "0") or 0)
        except Exception:
            self.stock_timeout_s = 0.0
        # 心跳间隔（秒）：等待 LLM 返回时定期打印，避免“看起来卡死”
        try:
            self.heartbeat_s = float(os.getenv("ANALYSE_HEARTBEAT", "5") or 5)
        except Exception:
            self.heartbeat_s = 5.0
        # 线程池用于超时/心跳包装（无法强杀底层请求，但可以避免主流程无限等待）
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        self.strategy = None
        self.llm = None              # ollama
        self.oa_client = None        # OpenAI SDK client (ark/one)
        self._initialize()
    
    def _initialize(self):
        """初始化 AI 模型和策略"""
        try:
            # 加载分析策略
            self.strategy = self._load_strategy()
            
            if self.provider in ("ark", "one"):
                try:
                    from openai import OpenAI
                except Exception as e:
                    raise ImportError(
                        "未安装 openai 依赖。请执行 `pip install openai` 或将其加入 requirements.txt 后安装。"
                    ) from e

                api_key = os.getenv(self._api_key_env)
                if not api_key:
                    raise ValueError(f"未配置 {self._api_key_env}（请在 .env 中设置对应 API Key）")

                self.oa_client = OpenAI(
                    base_url=self.base_url,
                    api_key=api_key,
                )
                print(f"✓ [AnalyseAgent] AI Provider: {self.provider}")
                print(f"✓ [AnalyseAgent] 模型已初始化: {self.model}")
                print(f"✓ [AnalyseAgent] Base URL: {self.base_url}")
            else:
                # 初始化 Ollama 模型
                self.llm = ChatOllama(
                    model=self.model,
                    base_url=self.base_url,
                    temperature=0.7,
                )
                print(f"✓ [AnalyseAgent] AI Provider: ollama")
                print(f"✓ [AnalyseAgent] Ollama 模型已初始化: {self.model}")
                print(f"✓ [AnalyseAgent] Ollama Base URL: {self.base_url}")

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
                raw_data: Dict[str, Any] = None,
                execution_id: Optional[str] = None) -> Dict[str, Any]:
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
            # 1. AI 分析（逐只股票结构化评分 → 代码汇总，避免输出截断导致漏股票）
            print("\n[AnalyseAgent] 步骤 1/2: 执行 AI 分析(逐只评分)...")
            analysis_result, per_stock, run_dir = self._analyze_portfolio_with_ai(
                stock_symbols=stock_symbols,
                raw_data=raw_data,
                execution_id=execution_id
            )

            if not analysis_result or "分析失败" in analysis_result:
                raise ValueError("AI 分析未能产生有效结果")
            
            print(f"✓ [AnalyseAgent] AI 分析完成 (覆盖 {len(per_stock)}/{len(stock_symbols)} 只股票, {len(analysis_result)} 字符)")
            
            # 2. 报告产出（增量写入已在评分过程中完成，这里只做最终确认/索引更新）
            print("\n[AnalyseAgent] 步骤 2/2: 生成分析报告(汇总)...")
            report_path = os.path.join(run_dir, "summary.md")
            if not os.path.exists(report_path):
                # 兜底：确保汇总文件存在
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(analysis_result)
            print(f"✓ [AnalyseAgent] 报告目录: {run_dir}")
            print(f"✓ [AnalyseAgent] 汇总报告: {report_path}")
            
            # 3. 更新报告索引
            self._update_report_index()
            
            return {
                "status": "success",
                "analysis": analysis_result,
                "report_path": report_path,
                "run_dir": run_dir,
                "timestamp": datetime.now().isoformat(),
                "symbols": stock_symbols,
                "per_stock": per_stock
            }
            
        except Exception as e:
            error_msg = f"分析失败: {e}"
            print(f"✗ [AnalyseAgent] {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }

    # ---------------------------
    # New analysis flow (robust)
    # ---------------------------
    def _analyze_portfolio_with_ai(
        self,
        stock_symbols: List[str],
        raw_data: Optional[Dict[str, Any]],
        execution_id: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        逐只股票进行结构化评分，然后在代码端生成综合评分表，避免 LLM 长输出截断导致漏股票。
        """
        # 运行目录：report/<execution_id 或 timestamp>/
        run_id = execution_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.output_dir, run_id)
        # NOTE: 这里不直接依赖 formatted_data，避免一次性长文本导致卡顿
        per_stock_results: List[Dict[str, Any]] = []
        # run_dir 延迟创建：一旦开始写文件就确保存在

        data_map = {}
        missing_symbols: List[str] = []
        if raw_data and raw_data.get("status") == "success":
            data_map = raw_data.get("data", {}) or {}
            missing_symbols = raw_data.get("missing", []) or []
        else:
            # raw_data 可能为空（单独使用 AnalyseAgent 时），退化为无法逐只评分
            data_map = {}

        for idx, symbol in enumerate(stock_symbols, start=1):
            # 确保输出目录存在
            if not os.path.exists(run_dir):
                os.makedirs(run_dir, exist_ok=True)

            print(f"[AnalyseAgent] 进度 {idx}/{len(stock_symbols)}: 开始评分 {symbol} ...")
            if symbol not in data_map:
                item = {
                    "symbol": symbol,
                    "ok": False,
                    "error": "未获取到行情数据" + ("（Fetch 阶段缺失）" if symbol in missing_symbols else ""),
                }
                per_stock_results.append(item)
                self._write_single_stock_md(run_dir, item)
                self._write_run_summary(run_dir, per_stock_results, stock_symbols)
                print(f"[AnalyseAgent] 进度 {idx}/{len(stock_symbols)}: {symbol} 无数据，已写入占位结果")
                continue

            try:
                scored = self._score_one_stock_with_ai(symbol=symbol, stock_info=data_map[symbol])
                item = {"ok": True, **scored}
                per_stock_results.append(item)
                self._write_single_stock_md(run_dir, item)
                self._write_run_summary(run_dir, per_stock_results, stock_symbols)
                print(f"[AnalyseAgent] 进度 {idx}/{len(stock_symbols)}: {symbol} 完成（{item.get('rating')} {item.get('overall_score')}/10）")
            except Exception as e:
                item = {
                    "symbol": symbol,
                    "ok": False,
                    "error": f"评分失败: {e}"
                }
                per_stock_results.append(item)
                self._write_single_stock_md(run_dir, item)
                self._write_run_summary(run_dir, per_stock_results, stock_symbols)
                print(f"[AnalyseAgent] 进度 {idx}/{len(stock_symbols)}: {symbol} 失败，已写入占位结果：{e}")

        # 生成报告主体 Markdown
        analysis_md = self._build_analysis_markdown(per_stock_results)
        # 最终写一次汇总，确保落盘
        if not os.path.exists(run_dir):
            os.makedirs(run_dir, exist_ok=True)
        self._write_run_summary(run_dir, per_stock_results, stock_symbols, final_markdown=analysis_md)
        return analysis_md, per_stock_results, run_dir

    def _write_single_stock_md(self, run_dir: str, item: Dict[str, Any]) -> str:
        """
        写入单只股票结果到 report/<run_dir>/<symbol>.md（增量产出）。
        """
        symbol = item.get("symbol", "UNKNOWN")
        safe_name = symbol.replace("/", "_")
        path = os.path.join(run_dir, f"{safe_name}.md")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"# 📄 单股分析：{symbol}\n\n- **生成时间**: {now_str}\n\n---\n\n"

        if not item.get("ok"):
            content = title + "## ⚠️ 结果\n\n" + f"- **状态**: 无法评分\n- **原因**: {item.get('error', '未知原因')}\n\n"
            content += self._get_disclaimer()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path

        price = item.get("price")
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "N/A"
        change_pct = item.get("change_pct")
        change_str = f"{change_pct:+.2f}%" if isinstance(change_pct, (int, float)) else "N/A"

        content = title
        content += "## 📊 评分摘要\n\n"
        content += f"- **名称**: {item.get('name', '')}\n"
        content += f"- **价格**: {price_str}\n"
        content += f"- **涨跌幅**: {change_str}\n"
        content += f"- **技术面**: {item.get('technical')}/10\n"
        content += f"- **基本面**: {item.get('fundamental')}/10\n"
        content += f"- **成长性**: {item.get('growth')}/10\n"
        content += f"- **市场情绪**: {item.get('sentiment')}/10\n"
        content += f"- **行业风险**: {item.get('industry_risk')}/10\n"
        content += f"- **综合评分**: {item.get('overall_score')}/10\n"
        content += f"- **评级**: {item.get('rating')} {item.get('signal')}\n\n"

        if item.get("reason"):
            content += "## 🧠 核心逻辑\n\n"
            content += f"{item.get('reason')}\n\n"

        if item.get("opportunities"):
            content += "## 🎯 机会点\n\n"
            for o in item["opportunities"][:8]:
                content += f"- {o}\n"
            content += "\n"

        if item.get("risks"):
            content += "## ⚠️ 风险点\n\n"
            for r in item["risks"][:8]:
                content += f"- {r}\n"
            content += "\n"

        if item.get("suggestion"):
            content += "## ✅ 建议\n\n"
            content += f"{item.get('suggestion')}\n\n"

        content += self._get_disclaimer()

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _write_run_summary(
        self,
        run_dir: str,
        per_stock_results: List[Dict[str, Any]],
        stock_symbols: List[str],
        final_markdown: Optional[str] = None
    ) -> str:
        """
        写入/更新本次任务的汇总 summary.md（每只股票完成后都会更新，便于实时查看）。
        """
        path = os.path.join(run_dir, "summary.md")

        # 为了实时性：表格按 stock_symbols 顺序输出，即使部分未完成也占位
        by_symbol = {x.get("symbol"): x for x in per_stock_results}
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"# 📊 任务汇总报告\n\n- **更新时间**: {now_str}\n- **分析标的**: {', '.join(stock_symbols)}\n\n---\n\n"
        md += "## ✅ 综合评分表\n\n"
        md += "| 代码 | 价格 | 技术面 | 基本面 | 成长性 | 综合评分 | 评级 | 信号 |\n"
        md += "|------|------|--------|--------|--------|----------|------|------|\n"

        done = 0
        for symbol in stock_symbols:
            item = by_symbol.get(symbol)
            code = symbol.split(".")[0] if symbol else symbol
            if item and item.get("ok"):
                done += 1
                price = item.get("price")
                price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "N/A"
                md += (
                    f"| {code} | {price_str} | {item['technical']}/10 | {item['fundamental']}/10 | {item['growth']}/10 | "
                    f"{item['overall_score']}/10 | {item['rating']} | {item['signal']} |\n"
                )
            elif item and not item.get("ok"):
                done += 1
                md += f"| {code} | N/A | N/A | N/A | N/A | N/A | 无法评分 | ⚠️ |\n"
            else:
                # 尚未处理到（仍在运行中）
                md += f"| {code} | ... | ... | ... | ... | ... | 进行中 | ⏳ |\n"

        md += "\n---\n\n"
        md += f"## 📌 进度\n\n- **已完成**: {done}/{len(stock_symbols)}\n\n"

        if final_markdown:
            # 任务结束时把更完整的洞察/详细说明附在后面
            # 注意：final_markdown 内部也会包含“综合评分表”，为避免 summary.md 出现两张表，这里剔除该段。
            md += "---\n\n## 🤖 AI 深度分析（最终版）\n\n"
            md += self._strip_rating_table_section(final_markdown)

        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        return path

    def _strip_rating_table_section(self, analysis_md: str) -> str:
        """
        去掉分析正文里重复的“综合评分表”段落，避免 summary.md 出现两张综合评分表。
        约定：_build_analysis_markdown() 的结构为：
          ### 综合评分表 ... \n---\n\n### 关键洞察 ...
        """
        if not analysis_md:
            return ""
        # 移除从“### 综合评分表”开始到第一个分隔线（---）结束（含分隔线）的内容
        pattern = r"###\s*综合评分表[\s\S]*?\n---\n\n"
        return re.sub(pattern, "", analysis_md, count=1)

    def _score_one_stock_with_ai(self, symbol: str, stock_info: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        对单只股票进行结构化评分，返回可解析的字典（尽量只依赖 raw_data 里已有字段）。
        """
        name = stock_info.get("name") or symbol
        price = (stock_info.get("price") or {})
        volume = stock_info.get("volume", 0)
        turnover = stock_info.get("turnover", 0)

        # 为模型提供尽量“短且完整”的输入，减少上下文压力
        data_brief = {
            "symbol": symbol,
            "name": name,
            "price": {
                "last_done": price.get("last_done"),
                "open": price.get("open"),
                "high": price.get("high"),
                "low": price.get("low"),
                "prev_close": price.get("prev_close"),
                "change_pct": price.get("change_pct"),
            },
            "volume": volume,
            "turnover": turnover,
            "timestamp": stock_info.get("timestamp"),
        }

        # 精简版评分规约（避免每只股票都塞整份 rating.md，显著降低 token 与耗时）
        rubric = (
            "评分维度与权重：基本面40%，技术面30%，成长性15%，市场情绪10%，行业风险5%。\n"
            "综合评分 = 基本面*0.4 + 技术面*0.3 + 成长性*0.15 + 市场情绪*0.1 + 行业风险*0.05。\n"
            "分值范围0-10，允许一位小数。缺失数据要基于可见的价格/涨跌幅/成交量/成交额做合理推断，并在 reason 说明假设。\n"
        )

        system_prompt = (
            "你是一位专业的股票分析师。"
            "你将依据评分规约与给定数据为单只股票打分。"
            "务必严格输出 JSON（不要 Markdown，不要解释文字）。\n"
            + rubric
        )

        user_prompt = f"""请依据评分规约与数据，为单只股票进行评分并输出 JSON。

【股票数据(JSON)】
{json.dumps(data_brief, ensure_ascii=False)}

【输出要求】
1) 只输出一个 JSON 对象（不要代码块围栏）。
2) 分值均为 0-10 的数值（允许一位小数）。
3) 字段必须完整，缺数据要给出合理推断并在 reason 里说明。
5) 严禁输出“思考过程/推理过程”，只输出最终 JSON，且尽量简洁（建议 < 1200 字符）。
4) 评级规则（按综合评分 overall_score）：
   - >=9.0: 强烈买入
   - >=7.5: 买入
   - >=6.0: 持有
   - >=4.0: 减持
   - <4.0: 卖出

【JSON Schema（必须包含这些 key）】
{{
  "symbol": "{symbol}",
  "name": "{name}",
  "price": <number|null>,
  "change_pct": <number|null>,
  "technical": <number>,
  "fundamental": <number>,
  "growth": <number>,
  "sentiment": <number>,
  "industry_risk": <number>,
  "overall_score": <number>,
  "rating": <string>,
  "signal": <string>,
  "reason": <string>,
  "risks": [<string>, ...],
  "opportunities": [<string>, ...],
  "suggestion": <string>
}}
"""

        last_err = None
        for attempt in range(max_retries):
            try:
                print(f"   - {symbol}: 第 {attempt + 1}/{max_retries} 次评分尝试...")
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
                text = self._invoke_with_heartbeat(
                    messages=messages,
                    symbol=symbol,
                    attempt=attempt + 1,
                    timeout_s=self.stock_timeout_s if self.stock_timeout_s and self.stock_timeout_s > 0 else None
                )
                parsed = self._parse_json_object(text)
                # 规范化数值与补齐
                parsed = self._normalize_score_payload(parsed, fallback_symbol=symbol, fallback_name=name, stock_info=stock_info)
                return parsed
            except Exception as e:
                last_err = e
                print(f"     ⚠️  {symbol} 评分解析失败: {e}")
                continue
        raise last_err or RuntimeError("评分失败：未知错误")

    def _invoke_with_heartbeat(
        self,
        messages: List[Any],
        symbol: str,
        attempt: int,
        timeout_s: Optional[float] = None
    ) -> str:
        """
        包装 LLM 调用：等待期间输出心跳，避免控制台长时间无输出。
        若设置 timeout_s，则超时抛出 TimeoutError 供上层记为失败并继续下一只。
        """
        start = time.time()
        future = self._executor.submit(self._invoke_provider, messages, timeout_s)
        next_heartbeat = start + max(1.0, float(self.heartbeat_s))

        while True:
            # 超时判断
            if timeout_s is not None and (time.time() - start) > timeout_s:
                raise TimeoutError(f"LLM 调用超时（>{timeout_s:.0f}s）。建议检查 Ollama 运行状态/首次加载模型/机器性能，或调大 ANALYSE_STOCK_TIMEOUT。")

            try:
                # 用很短的 wait 来实现心跳
                resp = future.result(timeout=0.2)
                return resp
            except FutureTimeoutError:
                pass

            now = time.time()
            if now >= next_heartbeat:
                waited = int(now - start)
                if timeout_s is not None:
                    print(f"     … {symbol} 等待模型响应中（第{attempt}次），已等待 {waited}s / 超时 {int(timeout_s)}s")
                else:
                    print(f"     … {symbol} 等待模型响应中（第{attempt}次），已等待 {waited}s")
                next_heartbeat = now + max(1.0, float(self.heartbeat_s))

    def _invoke_provider(self, messages: List[Any], timeout_s: Optional[float] = None) -> str:
        """
        根据 provider 调用不同的 LLM，并返回纯文本 content。
        """
        if self.provider in ("ark", "one"):
            if not self.oa_client:
                raise RuntimeError("OpenAI 兼容客户端未初始化")

            # LangChain message -> OpenAI message dict
            oa_messages: List[Dict[str, str]] = []
            for m in messages:
                role = "user"
                content = getattr(m, "content", None)
                # 兼容 SystemMessage/HumanMessage
                if isinstance(m, SystemMessage):
                    role = "system"
                elif isinstance(m, HumanMessage):
                    role = "user"
                oa_messages.append({"role": role, "content": content if content is not None else str(m)})

            # 更偏评分任务：默认更低温度，减少跑题
            try:
                temperature = float(os.getenv("LLM_TEMPERATURE", "0.2") or 0.2)
            except Exception:
                temperature = 0.2

            completion = self.oa_client.chat.completions.create(
                model=self.model,
                messages=oa_messages,
                temperature=temperature,
                timeout=timeout_s,
            )
            return (completion.choices[0].message.content or "").strip()

        # ollama
        if not self.llm:
            raise RuntimeError("Ollama 模型未初始化")
        resp = self.llm.invoke(messages)
        text = resp.content if hasattr(resp, "content") else str(resp)
        return text

    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        """
        从模型输出中提取并解析 JSON 对象（兼容偶发的围栏/前后多余文字）。
        """
        if not text or not isinstance(text, str):
            raise ValueError("模型返回为空")

        # 去掉常见的 Markdown 围栏
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        # 优先尝试整体解析
        try:
            obj = json.loads(cleaned)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        # 回退：提取第一个 {...} 块
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            raise ValueError("未找到 JSON 对象")
        obj = json.loads(m.group(0))
        if not isinstance(obj, dict):
            raise ValueError("JSON 不是对象")
        return obj

    def _normalize_score_payload(self, payload: Dict[str, Any], fallback_symbol: str, fallback_name: str, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        统一字段、数值范围，并用策略权重计算 overall_score（如果模型未给或不可信）。
        """
        def to_float(x, default=None):
            try:
                if x is None:
                    return default
                return float(x)
            except Exception:
                return default

        symbol = payload.get("symbol") or fallback_symbol
        name = payload.get("name") or fallback_name

        p = (stock_info.get("price") or {})
        price = to_float(payload.get("price"), default=to_float(p.get("last_done"), default=None))
        change_pct = to_float(payload.get("change_pct"), default=to_float(p.get("change_pct"), default=None))

        technical = to_float(payload.get("technical"), default=5.0)
        fundamental = to_float(payload.get("fundamental"), default=5.0)
        growth = to_float(payload.get("growth"), default=5.0)
        sentiment = to_float(payload.get("sentiment"), default=5.0)
        industry_risk = to_float(payload.get("industry_risk"), default=5.0)

        # clamp 0-10
        def clamp01(v):
            if v is None:
                return 5.0
            return max(0.0, min(10.0, v))

        technical = round(clamp01(technical), 1)
        fundamental = round(clamp01(fundamental), 1)
        growth = round(clamp01(growth), 1)
        sentiment = round(clamp01(sentiment), 1)
        industry_risk = round(clamp01(industry_risk), 1)

        overall = (fundamental * 0.4) + (technical * 0.3) + (growth * 0.15) + (sentiment * 0.1) + (industry_risk * 0.05)
        overall = round(overall, 2)

        rating, signal = self._rating_and_signal(overall)

        risks = payload.get("risks")
        if not isinstance(risks, list):
            risks = []
        opportunities = payload.get("opportunities")
        if not isinstance(opportunities, list):
            opportunities = []

        return {
            "symbol": symbol,
            "name": name,
            "price": price,
            "change_pct": change_pct,
            "technical": technical,
            "fundamental": fundamental,
            "growth": growth,
            "sentiment": sentiment,
            "industry_risk": industry_risk,
            "overall_score": overall,
            "rating": payload.get("rating") or rating,
            "signal": payload.get("signal") or signal,
            "reason": payload.get("reason") or "",
            "risks": risks,
            "opportunities": opportunities,
            "suggestion": payload.get("suggestion") or "",
        }

    def _rating_and_signal(self, overall_score: float) -> Tuple[str, str]:
        if overall_score >= 9.0:
            return "强烈买入", "🟢"
        if overall_score >= 7.5:
            return "买入", "🟡"
        if overall_score >= 6.0:
            return "持有", "🟠"
        if overall_score >= 4.0:
            return "减持", "🔴"
        return "卖出", "⚫"

    def _build_analysis_markdown(self, per_stock_results: List[Dict[str, Any]]) -> str:
        """
        把逐只评分结果拼成稳定的 Markdown（综合评分表一定覆盖全部股票）。
        """
        # 表头按策略模板（并增加信号列）
        md = "### 综合评分表\n\n"
        md += "| 代码 | 价格 | 技术面 | 基本面 | 成长性 | 综合评分 | 评级 | 信号 |\n"
        md += "|------|------|--------|--------|--------|----------|------|------|\n"

        ok_items: List[Dict[str, Any]] = []
        fail_items: List[Dict[str, Any]] = []

        # 关键点：严格保序输出（与用户 .env 列表一致），同时对失败项原位占位
        for item in per_stock_results:
            symbol = item.get("symbol", "")
            code = symbol.split(".")[0] if symbol else symbol
            if item.get("ok"):
                ok_items.append(item)
                price = item.get("price")
                price_str = f"${price:.2f}" if isinstance(price, (int, float)) else "N/A"
                md += (
                    f"| {code} | {price_str} | {item['technical']}/10 | {item['fundamental']}/10 | {item['growth']}/10 | "
                    f"{item['overall_score']}/10 | {item['rating']} | {item['signal']} |\n"
                )
            else:
                fail_items.append(item)
                md += f"| {code} | N/A | N/A | N/A | N/A | N/A | 无法评分 | ⚠️ |\n"

        md += "\n---\n\n"
        md += "### 关键洞察\n\n"
        md += self._build_key_insights(ok_items, fail_items)
        md += "\n---\n\n"
        md += "### 详细分析说明\n\n"

        for item in ok_items:
            md += f"#### {item.get('name', item.get('symbol'))}（{item.get('symbol')}）\n"
            md += f"- **评分**：技术面 {item['technical']}/10，基本面 {item['fundamental']}/10，成长性 {item['growth']}/10，综合 {item['overall_score']}/10（{item['rating']}）\n"
            if item.get("reason"):
                md += f"- **核心逻辑**：{item['reason']}\n"
            if item.get("opportunities"):
                md += "- **机会点**：\n"
                for o in item["opportunities"][:5]:
                    md += f"  - {o}\n"
            if item.get("risks"):
                md += "- **风险点**：\n"
                for r in item["risks"][:5]:
                    md += f"  - {r}\n"
            if item.get("suggestion"):
                md += f"- **建议**：{item['suggestion']}\n"
            md += "\n"

        if fail_items:
            md += "#### 未能完成评分的标的\n"
            for item in fail_items:
                md += f"- {item.get('symbol')}: {item.get('error', '未知原因')}\n"
            md += "\n"

        return md

    def _build_key_insights(self, ok_items: List[Dict[str, Any]], fail_items: List[Dict[str, Any]]) -> str:
        """
        关键洞察：优先用规则/排序生成（确定性），并可在未来扩展为再调用一次 LLM 进行润色。
        """
        if not ok_items and fail_items:
            return "本次未获得可用于评分的行情数据，无法生成洞察。\n"

        sorted_ok = sorted(ok_items, key=lambda x: x.get("overall_score", 0), reverse=True)
        top = sorted_ok[:3]
        bottom = list(reversed(sorted_ok[-3:])) if len(sorted_ok) >= 3 else list(reversed(sorted_ok))

        md = "#### 🎯 机会识别\n"
        if top:
            for item in top:
                md += f"- **优先关注**：{item.get('symbol')}（{item.get('rating')}，综合 {item.get('overall_score')}/10）\n"
        else:
            md += "- 暂无\n"

        md += "\n#### ⚠️ 风险预警\n"
        if bottom:
            for item in bottom:
                md += f"- **需要谨慎**：{item.get('symbol')}（综合 {item.get('overall_score')}/10）\n"
        else:
            md += "- 暂无\n"

        if fail_items:
            md += "\n#### 🧩 数据缺失\n"
            md += f"- 有 {len(fail_items)} 只股票未能完成评分（详见“未能完成评分的标的”）。\n"

        return md

    def __del__(self):
        # 避免线程池在解释器退出时报警
        try:
            if hasattr(self, "_executor") and self._executor:
                self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
    
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
        
        # 获取所有报告文件（旧版：report/stock_analysis_*.md）
        try:
            reports = [f for f in os.listdir(self.output_dir)
                      if f.startswith("stock_analysis_") and f.endswith(".md")]
            reports.sort(reverse=True)
        except:
            reports = []

        # 获取任务目录（新版：report/<execution_time>/summary.md）
        try:
            run_dirs = []
            for name in os.listdir(self.output_dir):
                p = os.path.join(self.output_dir, name)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, "summary.md")):
                    run_dirs.append(name)
            run_dirs.sort(reverse=True)
        except:
            run_dirs = []
        
        # 构建索引内容
        index_content = "# 📊 股票分析报告索引\n\n"
        index_content += f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        index_content += f"**报告总数**: {len(reports) + len(run_dirs)}\n\n"
        index_content += "---\n\n"
        index_content += "## 📁 报告列表\n\n"
        
        if run_dirs:
            index_content += "### 🆕 任务目录（按任务时间）\n\n"
            for d in run_dirs:
                # d 通常是 YYYYMMDD_HHMMSS
                try:
                    time_str = datetime.strptime(d, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = d
                index_content += f"- [{d}/summary]({d}/summary.md) - {time_str}\n"
            index_content += "\n"

        if reports:
            index_content += "### 📄 旧版单文件报告\n\n"
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
        if not reports and not run_dirs:
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
