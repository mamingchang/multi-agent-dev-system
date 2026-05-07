#!/usr/bin/env python3
"""
环境检查和系统初始化脚本
"""
import os
import sys
from pathlib import Path

def print_status(message, status):
    """打印状态信息"""
    symbols = {"ok": "✓", "fail": "✗", "warn": "⚠"}
    colors = {"ok": "\033[92m", "fail": "\033[91m", "warn": "\033[93m"}
    reset = "\033[0m"

    symbol = symbols.get(status, "?")
    color = colors.get(status, "")
    print(f"{color}{symbol}{reset} {message}")

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "ok")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} (需要3.8+)", "fail")
        return False

def check_dependencies():
    """检查依赖包"""
    required = [
        "sqlalchemy",
        "fastapi",
        "uvicorn",
        "pydantic",
        "jose",
        "passlib"
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print_status(f"Package: {package}", "ok")
        except ImportError:
            print_status(f"Package: {package}", "fail")
            missing.append(package)

    return len(missing) == 0, missing

def check_env_file():
    """检查环境变量文件"""
    env_file = Path(".env")
    if env_file.exists():
        print_status(".env file exists", "ok")
        return True
    else:
        print_status(".env file missing", "warn")
        return False

def check_database():
    """检查数据库"""
    db_file = Path("multi_agent_dev.db")
    if db_file.exists():
        print_status("Database exists", "ok")
        return True
    else:
        print_status("Database not initialized", "warn")
        return False

def check_frontend():
    """检查前端"""
    node_modules = Path("frontend/node_modules")
    if node_modules.exists():
        print_status("Frontend dependencies installed", "ok")
        return True
    else:
        print_status("Frontend dependencies missing", "warn")
        return False

def init_database():
    """初始化数据库"""
    try:
        from sqlalchemy import create_engine
        from src.database.models import Base

        engine = create_engine('sqlite:///./multi_agent_dev.db')
        Base.metadata.create_all(engine)
        print_status("Database initialized", "ok")
        return True
    except Exception as e:
        print_status(f"Database initialization failed: {e}", "fail")
        return False

def create_env_template():
    """创建环境变量模板"""
    template = """# Multi-Agent Dev System Configuration

# Claude API (可选，用于AI Agent)
ANTHROPIC_API_KEY=your_api_key_here

# 数据库
DATABASE_URL=sqlite:///./multi_agent_dev.db

# JWT认证
SECRET_KEY=change-this-to-a-random-secret-key-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务器
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
"""

    try:
        with open(".env", "w") as f:
            f.write(template)
        print_status("Created .env template", "ok")
        return True
    except Exception as e:
        print_status(f"Failed to create .env: {e}", "fail")
        return False

def main():
    print("\n" + "="*60)
    print("Multi-Agent Dev System - 环境检查")
    print("="*60 + "\n")

    # 检查Python版本
    print("1. Python版本:")
    python_ok = check_python_version()
    print()

    # 检查依赖
    print("2. Python依赖:")
    deps_ok, missing = check_dependencies()
    print()

    # 检查环境变量
    print("3. 环境配置:")
    env_ok = check_env_file()
    print()

    # 检查数据库
    print("4. 数据库:")
    db_ok = check_database()
    print()

    # 检查前端
    print("5. 前端:")
    frontend_ok = check_frontend()
    print()

    # 总结
    print("="*60)
    print("总结:")
    print("="*60)

    if not python_ok:
        print("\n❌ Python版本不满足要求，请升级到3.8+")
        return 1

    if not deps_ok:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing)}")
        print("   运行: pip install -r requirements.txt")

    if not env_ok:
        print("\n⚠️  .env文件不存在")
        response = input("   是否创建模板? (y/n): ")
        if response.lower() == 'y':
            create_env_template()
            print("   请编辑.env文件，填入正确的配置")

    if not db_ok and deps_ok:
        print("\n⚠️  数据库未初始化")
        response = input("   是否立即初始化? (y/n): ")
        if response.lower() == 'y':
            init_database()

    if not frontend_ok:
        print("\n⚠️  前端依赖未安装")
        print("   运行: cd frontend && npm install")

    # 启动建议
    print("\n" + "="*60)
    print("下一步:")
    print("="*60)

    if deps_ok and db_ok and env_ok:
        print("\n✓ 环境就绪！可以启动服务:")
        print("\n  后端:")
        print("    cd backend")
        print("    uvicorn main:app --reload")
        print("\n  前端:")
        print("    cd frontend")
        print("    npm run dev")
        print("\n  访问: http://localhost:3000")
    else:
        print("\n请先完成上述配置步骤")

    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
