#!/usr/bin/env python3
"""
配置测试脚本
用于验证系统配置是否正确
"""
import sys
import os

def check_python_version():
    """检查 Python 版本"""
    print("1. 检查 Python 版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要 Python 3.8 或更高版本")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n2. 检查依赖包...")
    required_packages = [
        ('dotenv', 'python-dotenv'),
        ('longport', 'longport'),
        ('langchain', 'langchain'),
        ('langchain_ollama', 'langchain-ollama'),
        ('langchain_core', 'langchain-core'),
    ]
    
    all_ok = True
    for package, pip_name in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {pip_name}")
        except ImportError:
            print(f"   ✗ {pip_name} (未安装)")
            all_ok = False
    
    return all_ok

def check_env_file():
    """检查 .env 文件"""
    print("\n3. 检查配置文件...")
    if os.path.exists('.env'):
        print("   ✓ .env 文件存在")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        # 检查必需的环境变量
        required_vars = [
            'LONGBRIDGE_APP_KEY',
            'LONGBRIDGE_APP_SECRET',
            'LONGBRIDGE_ACCESS_TOKEN',
            'STOCK_LIST',
        ]
        
        all_ok = True
        for var in required_vars:
            value = os.getenv(var)
            if value and value != f"your_{var.lower()}_here":
                print(f"   ✓ {var} 已配置")
            else:
                print(f"   ✗ {var} 未配置或使用默认值")
                all_ok = False
        
        return all_ok
    else:
        print("   ✗ .env 文件不存在")
        print("   请复制 config.example.env 为 .env 并填写配置")
        return False

def check_ollama():
    """检查 Ollama 服务"""
    print("\n4. 检查 Ollama 服务...")
    try:
        import urllib.request
        import json
        
        url = "http://localhost:11434/api/tags"
        req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            models = data.get('models', [])
            
            print(f"   ✓ Ollama 服务运行中")
            print(f"   ✓ 已安装 {len(models)} 个模型:")
            for model in models[:5]:  # 只显示前5个
                print(f"      - {model.get('name', 'unknown')}")
            
            return True
            
    except Exception as e:
        print(f"   ✗ Ollama 服务未运行或无法连接")
        print(f"   错误: {e}")
        print("   请运行: ollama serve")
        return False

def check_strategy_file():
    """检查策略文件"""
    print("\n5. 检查策略文件...")
    strategy_path = "strategies/rating.md"
    if os.path.exists(strategy_path):
        print(f"   ✓ 策略文件存在: {strategy_path}")
        return True
    else:
        print(f"   ✗ 策略文件不存在: {strategy_path}")
        return False

def check_output_dir():
    """检查输出目录"""
    print("\n6. 检查输出目录...")
    output_dir = "report"
    if os.path.exists(output_dir):
        print(f"   ✓ 输出目录存在: {output_dir}")
    else:
        print(f"   ! 输出目录不存在，将在运行时自动创建")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("股票智能分析系统 - 配置检查")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Python 版本", check_python_version()))
    results.append(("依赖包", check_dependencies()))
    results.append(("配置文件", check_env_file()))
    results.append(("Ollama 服务", check_ollama()))
    results.append(("策略文件", check_strategy_file()))
    results.append(("输出目录", check_output_dir()))
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过！系统已准备就绪。")
        print("\n运行以下命令开始分析:")
        print("  python main.py")
    else:
        print("⚠️  部分检查未通过，请根据上述提示进行配置。")
        print("\n常见问题解决:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 配置环境: cp config.example.env .env && nano .env")
        print("3. 启动 Ollama: ollama serve")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

