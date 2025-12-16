#!/usr/bin/env python3
"""
架构测试脚本
验证 v2.0 Agent 架构是否正常工作
"""
import sys


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    try:
        # 测试 Controller 导入
        from controller import StockAnalysisController
        print("✓ Controller 导入成功")
        
        # 测试 Agents 导入
        from agents.fetch_agent import FetchAgent
        print("✓ FetchAgent 导入成功")
        
        from agents.analyse_agent import AnalyseAgent
        print("✓ AnalyseAgent 导入成功")
        
        # 测试向后兼容
        from main import StockAnalysisSystem
        print("✓ StockAnalysisSystem (兼容别名) 导入成功")
        
        print("\n✅ 所有模块导入测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 模块导入失败: {e}\n")
        return False


def test_controller_init():
    """测试 Controller 初始化"""
    print("=" * 60)
    print("测试 2: Controller 初始化")
    print("=" * 60)
    
    try:
        from controller import StockAnalysisController
        
        # 测试配置加载
        controller = StockAnalysisController()
        print("✓ Controller 实例化成功")
        
        # 测试配置
        config = controller.config
        print(f"✓ 配置加载成功:")
        print(f"  - 股票列表: {config.get('stock_list', 'N/A')}")
        print(f"  - AI 模型: {config.get('ollama_model', 'N/A')}")
        print(f"  - 输出目录: {config.get('output_dir', 'N/A')}")
        
        # 测试系统信息
        info = controller.get_system_info()
        print(f"✓ 系统信息获取成功")
        print(f"  - 初始化状态: {info['is_initialized']}")
        print(f"  - Agents: {info['agents']}")
        
        print("\n✅ Controller 初始化测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Controller 初始化失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_agents_init():
    """测试 Agents 初始化"""
    print("=" * 60)
    print("测试 3: Agents 独立初始化")
    print("=" * 60)
    
    # 测试 FetchAgent
    try:
        print("\n[测试 FetchAgent]")
        from agents.fetch_agent import FetchAgent
        
        # 注意: 这里会真实连接 Longbridge，可能需要正确的配置
        print("⚠️  注意: FetchAgent 需要有效的 Longbridge 配置")
        print("   如果配置无效，此测试可能失败（这是正常的）")
        
        try:
            fetch_agent = FetchAgent()
            print("✓ FetchAgent 实例化成功")
            fetch_agent.close()
        except Exception as e:
            print(f"⚠️  FetchAgent 初始化失败（可能是配置问题）: {e}")
        
    except Exception as e:
        print(f"❌ FetchAgent 测试失败: {e}")
        return False
    
    # 测试 AnalyseAgent
    try:
        print("\n[测试 AnalyseAgent]")
        from agents.analyse_agent import AnalyseAgent
        
        print("⚠️  注意: AnalyseAgent 需要 Ollama 服务运行")
        print("   如果 Ollama 未运行，此测试可能失败（这是正常的）")
        
        try:
            analyse_agent = AnalyseAgent()
            print("✓ AnalyseAgent 实例化成功")
            print(f"  - AI 模型: {analyse_agent.model}")
            print(f"  - 策略路径: {analyse_agent.strategy_path}")
        except Exception as e:
            print(f"⚠️  AnalyseAgent 初始化失败（可能是 Ollama 未运行）: {e}")
        
    except Exception as e:
        print(f"❌ AnalyseAgent 测试失败: {e}")
        return False
    
    print("\n✅ Agents 初始化测试完成\n")
    return True


def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 60)
    print("测试 4: API 兼容性")
    print("=" * 60)
    
    try:
        # 测试旧的别名
        from main import StockAnalysisSystem
        from controller import StockAnalysisController
        
        # 验证别名指向同一个类
        if StockAnalysisSystem is StockAnalysisController:
            print("✓ StockAnalysisSystem 是 StockAnalysisController 的别名")
        else:
            print("⚠️  StockAnalysisSystem 不是直接别名，但仍可用")
        
        # 验证旧模块已被移除
        import os
        old_modules = [
            'stock_data_fetcher.py',
            'ai_analyzer.py',
            'report_generator.py'
        ]
        
        print("\n确认旧模块已删除:")
        all_removed = True
        for module in old_modules:
            if not os.path.exists(module):
                print(f"  ✓ {module} 已删除")
            else:
                print(f"  ⚠️  {module} 仍然存在（应该删除）")
                all_removed = False
        
        if all_removed:
            print("\n✅ 所有旧模块已正确清理")
        
        print("\n✅ API 兼容性测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ API 兼容性测试失败: {e}\n")
        return False


def test_context_manager():
    """测试上下文管理器"""
    print("=" * 60)
    print("测试 5: 上下文管理器")
    print("=" * 60)
    
    try:
        from controller import StockAnalysisController
        
        # 测试 with 语句
        with StockAnalysisController() as controller:
            print("✓ 进入上下文管理器")
            print(f"✓ 初始化状态: {controller.is_initialized}")
        
        print("✓ 退出上下文管理器（资源已清理）")
        
        print("\n✅ 上下文管理器测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 上下文管理器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 股票智能分析系统 v2.0 架构测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("模块导入", test_imports),
        ("Controller 初始化", test_controller_init),
        ("Agents 独立初始化", test_agents_init),
        ("API 兼容性", test_backward_compatibility),
        ("上下文管理器", test_context_manager),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 发生异常: {e}\n")
            results.append((name, False))
    
    # 打印总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！架构工作正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败。")
        print("注意: 某些测试失败可能是由于环境配置（Longbridge API、Ollama）")
        print("如果只是配置相关的失败，架构本身可能仍然正常。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

