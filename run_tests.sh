"""
测试运行脚本

提供便捷的测试运行命令。
"""

#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# 测试函数
# ============================================================================

run_unit_tests() {
    print_info "运行单元测试..."
    pytest tests/ -m unit -v --cov=src --cov-report=html --cov-report=term-missing
}

run_integration_tests() {
    print_info "运行集成测试..."
    pytest tests/ -m integration -v
}

run_all_tests() {
    print_info "运行所有测试..."
    pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
}

run_stress_tests() {
    print_info "运行压力测试..."
    print_warning "请确保API服务已启动"

    # 检查locust是否安装
    if ! command -v locust &> /dev/null; then
        print_error "Locust未安装，请运行: pip install locust"
        exit 1
    fi

    # 运行压力测试
    locust -f tests/test_stress.py --users 100 --spawn-rate 10 --run-time 5m --headless
}

check_coverage() {
    print_info "检查测试覆盖率..."
    pytest tests/ -m unit --cov=src --cov-report=term-missing --cov-fail-under=90

    if [ $? -eq 0 ]; then
        print_info "✓ 覆盖率达标（≥90%）"
    else
        print_error "✗ 覆盖率不足（<90%）"
        exit 1
    fi
}

run_code_quality() {
    print_info "运行代码质量检查..."

    # flake8
    print_info "运行flake8..."
    flake8 src/ --count --max-complexity=10 --max-line-length=127 --statistics

    # black
    print_info "检查代码格式..."
    black --check src/

    # isort
    print_info "检查导入排序..."
    isort --check-only src/

    print_info "✓ 代码质量检查通过"
}

run_security_scan() {
    print_info "运行安全扫描..."

    # safety
    print_info "检查依赖安全性..."
    pip freeze | safety check --stdin || true

    # bandit
    print_info "运行代码安全扫描..."
    bandit -r src/ -f screen

    print_info "✓ 安全扫描完成"
}

generate_test_report() {
    print_info "生成测试报告..."

    # 运行测试并生成报告
    pytest tests/ -v \
        --cov=src \
        --cov-report=html \
        --cov-report=xml \
        --html=test-report.html \
        --self-contained-html

    print_info "✓ 测试报告已生成:"
    print_info "  - HTML覆盖率报告: htmlcov/index.html"
    print_info "  - XML覆盖率报告: coverage.xml"
    print_info "  - HTML测试报告: test-report.html"
}

clean_test_artifacts() {
    print_info "清理测试产物..."

    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -f coverage.xml
    rm -f test-report.html

    print_info "✓ 清理完成"
}

# ============================================================================
# 主函数
# ============================================================================

show_help() {
    cat << EOF
测试运行脚本

用法: ./run_tests.sh [命令]

命令:
  unit              运行单元测试
  integration       运行集成测试
  all               运行所有测试
  stress            运行压力测试
  coverage          检查测试覆盖率
  quality           运行代码质量检查
  security          运行安全扫描
  report            生成测试报告
  clean             清理测试产物
  ci                运行CI流程（质量检查+所有测试+覆盖率）
  help              显示此帮助信息

示例:
  ./run_tests.sh unit           # 运行单元测试
  ./run_tests.sh all            # 运行所有测试
  ./run_tests.sh ci             # 运行完整CI流程

EOF
}

run_ci_pipeline() {
    print_info "运行CI流程..."

    # 1. 代码质量检查
    run_code_quality

    # 2. 安全扫描
    run_security_scan

    # 3. 运行所有测试
    run_all_tests

    # 4. 检查覆盖率
    check_coverage

    print_info "✓ CI流程完成"
}

# 主逻辑
case "${1:-help}" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    all)
        run_all_tests
        ;;
    stress)
        run_stress_tests
        ;;
    coverage)
        check_coverage
        ;;
    quality)
        run_code_quality
        ;;
    security)
        run_security_scan
        ;;
    report)
        generate_test_report
        ;;
    clean)
        clean_test_artifacts
        ;;
    ci)
        run_ci_pipeline
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
