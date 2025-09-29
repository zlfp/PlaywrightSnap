#!/usr/bin/env python3
"""
测试运行脚本
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print("STDOUT:")
        print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print(f"返回码: {result.returncode}")

    if result.returncode != 0:
        print(f"❌ {description} 失败")
        return False
    else:
        print(f"✅ {description} 成功")
        return True


def main():
    """主函数"""
    print("🚀 开始运行测试套件...")

    # 确保在虚拟环境中
    if not os.path.exists("venv"):
        print("❌ 虚拟环境不存在，请先创建虚拟环境")
        return False

    # 激活虚拟环境并安装依赖
    activate_cmd = "source venv/bin/activate && pip install -r requirements.txt"
    if not run_command(activate_cmd.split(), "安装依赖"):
        return False

    tests_passed = 0
    total_tests = 0

    # 运行单元测试
    total_tests += 1
    if run_command([
        "source", "venv/bin/activate", "&&",
        "python", "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "--cov=tests/unit",
        "--cov-report=term-missing",
        "--cov-report=html"
    ], "运行单元测试"):
        tests_passed += 1

    # 运行集成测试
    total_tests += 1
    if run_command([
        "source", "venv/bin/activate", "&&",
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ], "运行集成测试"):
        tests_passed += 1

    # 运行端到端测试（可能需要更长时间）
    total_tests += 1
    if run_command([
        "source", "venv/bin/activate", "&&",
        "python", "-m", "pytest",
        "tests/e2e/",
        "-v",
        "--tb=short",
        "-s"  # 显示输出
    ], "运行端到端测试"):
        tests_passed += 1

    # 运行所有测试
    total_tests += 1
    if run_command([
        "source", "venv/bin/activate", "&&",
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=tests",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml"
    ], "运行所有测试并生成覆盖率报告"):
        tests_passed += 1

    # 显示总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    print(f"通过测试: {tests_passed}/{total_tests}")
    print(f"成功率: {(tests_passed/total_tests)*100:.1f}%")

    if tests_passed == total_tests:
        print("🎉 所有测试都通过了！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)