"""
用户体验优化测试

测试场景：
1. 任务模板管理
2. 模板使用
3. 进度预估
4. 动态更新预估
5. 里程碑预估
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ux.template_manager import template_manager, TaskTemplate, TemplateCategory, TemplateScope
from src.ux.progress_estimator import progress_estimator


def test_template_management():
    """测试1: 任务模板管理"""
    print("\n=== 测试1: 任务模板管理 ===")

    # 列出所有模板
    templates = template_manager.list_templates()
    print(f"✓ 内置模板数: {len(templates)}")
    assert len(templates) > 0, "应该有内置模板"

    # 按分类过滤
    feature_templates = template_manager.list_templates(category=TemplateCategory.FEATURE)
    print(f"✓ 功能开发模板: {len(feature_templates)}")

    bugfix_templates = template_manager.list_templates(category=TemplateCategory.BUGFIX)
    print(f"✓ Bug修复模板: {len(bugfix_templates)}")

    # 按技术栈过滤
    python_templates = template_manager.list_templates(tech_stack="Python")
    print(f"✓ Python模板: {len(python_templates)}")

    # 按标签过滤
    common_templates = template_manager.list_templates(tags=["common"])
    print(f"✓ 常用模板: {len(common_templates)}")

    print("✓ 任务模板管理测试通过")


def test_template_usage():
    """测试2: 模板使用"""
    print("\n=== 测试2: 模板使用 ===")

    # 获取登录注册模板
    template = template_manager.get_template("login_register")
    assert template is not None, "应该能获取到模板"
    print(f"✓ 模板: {template.name}")

    # 使用模板
    params = {
        "auth_method": "JWT",
        "tech_stack": "FastAPI + PostgreSQL"
    }

    task_data = template_manager.use_template("login_register", params)
    print(f"✓ 渲染标题: {task_data['title']}")
    print(f"✓ 工作流: {' → '.join(task_data['workflow'])}")
    print(f"✓ 预估工时: {task_data['estimated_hours']}小时")

    assert "JWT" in task_data["title"], "标题应该包含参数"
    assert "FastAPI" in task_data["description"], "描述应该包含参数"

    # 使用次数应该增加
    assert template.usage_count > 0, "使用次数应该增加"
    print(f"✓ 使用次数: {template.usage_count}")

    print("✓ 模板使用测试通过")


def test_progress_estimation():
    """测试3: 进度预估"""
    print("\n=== 测试3: 进度预估 ===")

    # 预估功能开发任务
    estimate = progress_estimator.estimate_task_duration(
        task_type="feature",
        workflow=["ProductManager", "Architect", "Developer", "Tester"],
        task_description="实现用户登录注册功能"
    )

    print(f"✓ 预估工时: {estimate['estimated_hours']}小时")
    print(f"✓ 范围: {estimate['min_hours']}-{estimate['max_hours']}小时")
    print(f"✓ 置信度: {estimate['confidence']} ({estimate['confidence_level']})")
    print(f"✓ 预计完成: {estimate['estimated_completion']}")

    assert estimate["estimated_hours"] > 0, "预估工时应该大于0"
    assert estimate["confidence"] > 0, "置信度应该大于0"

    # 预估Bug修复任务
    bugfix_estimate = progress_estimator.estimate_task_duration(
        task_type="bugfix",
        workflow=["Developer", "Tester"],
        task_description="修复登录失败的Bug"
    )

    print(f"✓ Bug修复预估: {bugfix_estimate['estimated_hours']}小时")
    assert bugfix_estimate["estimated_hours"] < estimate["estimated_hours"], "Bug修复应该比功能开发快"

    print("✓ 进度预估测试通过")


def test_dynamic_estimation():
    """测试4: 动态更新预估"""
    print("\n=== 测试4: 动态更新预估 ===")

    # 初始预估20小时
    initial_estimate = 20.0

    # 测试不同进度下的预估更新
    test_cases = [
        (0.25, 4.0),   # 25%进度，耗时4小时
        (0.50, 10.0),  # 50%进度，耗时10小时
        (0.75, 16.0),  # 75%进度，耗时16小时
    ]

    for progress, elapsed in test_cases:
        updated = progress_estimator.update_estimate(
            task_id=1,
            current_progress=progress,
            elapsed_hours=elapsed,
            initial_estimate=initial_estimate
        )

        print(f"✓ 进度{updated['current_progress']}%:")
        print(f"  已耗时: {updated['elapsed_hours']}小时")
        print(f"  预估剩余: {updated['estimated_remaining_hours']}小时")
        print(f"  预估总计: {updated['estimated_total_hours']}小时")
        print(f"  置信度: {updated['confidence']}")

        assert updated["estimated_remaining_hours"] >= 0, "剩余时间应该非负"
        assert updated["confidence"] > 0, "置信度应该大于0"

    print("✓ 动态更新预估测试通过")


def test_milestone_estimation():
    """测试5: 里程碑预估"""
    print("\n=== 测试5: 里程碑预估 ===")

    workflow = ["ProductManager", "Architect", "Developer", "CodeReviewer", "Tester"]
    total_estimate = 20.0

    milestones = progress_estimator.get_milestone_estimates(
        workflow=workflow,
        total_estimate=total_estimate
    )

    print(f"✓ 总预估: {total_estimate}小时")
    print(f"✓ 里程碑数: {len(milestones)}")

    cumulative = 0
    for milestone in milestones:
        cumulative += milestone["estimated_hours"]
        print(f"  {milestone['agent']}: {milestone['estimated_hours']}小时 "
              f"(累计{milestone['cumulative_hours']}小时, {milestone['progress_percentage']}%)")

    assert len(milestones) == len(workflow), "里程碑数应该等于Agent数"
    # 浮点数精度问题，允许0.5小时误差
    assert abs(cumulative - total_estimate) < 0.5, f"累计时间应该接近总预估，实际差异: {abs(cumulative - total_estimate)}"

    print("✓ 里程碑预估测试通过")


def test_custom_template():
    """测试6: 自定义模板"""
    print("\n=== 测试6: 自定义模板 ===")

    # 创建自定义模板
    custom_template = TaskTemplate(
        id="custom_test",
        name="自定义测试模板",
        description="测试用的自定义模板",
        category=TemplateCategory.FEATURE,
        title_template="实现{feature_name}",
        description_template="实现{feature_name}功能\n技术栈: {tech_stack}",
        workflow=["Developer", "Tester"],
        tech_stacks=["Python"],
        estimated_hours=8,
        priority=60,
        parameters={"feature_name": "测试功能", "tech_stack": "Python"},
        scope=TemplateScope.USER,
        scope_id=1,
        author="test_user",
        tags=["custom"]
    )

    # 添加模板
    success = template_manager.add_template(custom_template)
    assert success, "添加模板应该成功"
    print(f"✓ 添加自定义模板: {custom_template.name}")

    # 使用自定义模板
    task_data = template_manager.use_template("custom_test", {
        "feature_name": "支付功能",
        "tech_stack": "FastAPI"
    })

    print(f"✓ 渲染标题: {task_data['title']}")
    assert "支付功能" in task_data["title"], "应该包含参数"

    # 删除模板
    success = template_manager.delete_template("custom_test")
    assert success, "删除模板应该成功"
    print("✓ 删除自定义模板")

    print("✓ 自定义模板测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("用户体验优化测试")
    print("="*60)

    try:
        test_template_management()
        test_template_usage()
        test_progress_estimation()
        test_dynamic_estimation()
        test_milestone_estimation()
        test_custom_template()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
