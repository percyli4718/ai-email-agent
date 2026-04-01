#!/usr/bin/env python3
"""
CEO Agent 端到端测试

测试 CEO Agent 的任务分解和执行功能：
1. 测试任务分解（decompose_inquiry）
2. 测试任务执行（execute_graph）
3. 测试数据库记录

注意：本测试文件设计为脚本运行，pytest 收集时跳过。
运行方式：python tests/agents/test_ceo_agent_e2e.py
"""
import asyncio
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from email_agent.config import settings
from email_agent.agents.ceo_agent import CEOAgent, DependencyGraph


# 标记这些函数为脚本函数，pytest 跳过
pytestmark = pytest.mark.skip(reason="Run as script: python tests/agents/test_ceo_agent_e2e.py")


async def test_decompose_inquiry():
    """测试任务分解功能"""
    print("=" * 60)
    print("测试 1: CEO Agent 任务分解")
    print("=" * 60)

    ceo = CEOAgent(settings)

    # 模拟分类结果
    classification = {
        "type": "inquiry",
        "products_mentioned": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "customer_region": "Europe",
        "priority_score": 0.8,
        "suggested_route": "quote_flow"
    }

    email_body = """
    Dear Supplier,

    We are interested in purchasing:
    - Paracetamol 500mg: 1000 boxes
    - Ibuprofen 400mg: 500 boxes

    Please provide quote for delivery to London, UK.

    Best regards,
    PharmaCom UK
    """

    # 执行任务分解
    graph = ceo.decompose_inquiry(email_body, classification)

    print(f"\n✓ 任务分解成功")
    print(f"  任务数量：{len(graph.tasks)}")

    # 打印任务详情
    print("\n任务列表:")
    for task_id, task in graph.tasks.items():
        print(f"  [{task_id}] {task.agent_name}")
        print(f"      预算：${task.budget:.2f}")
        print(f"      依赖：{task.dependencies if task.dependencies else '无'}")

    # 验证任务数量
    assert len(graph.tasks) == 4, "应该有 4 个任务"

    # 验证依赖关系
    tasks_list = list(graph.tasks.values())
    price_task = next(t for t in tasks_list if t.agent_name == "price_agent")
    compliance_task = next(t for t in tasks_list if t.agent_name == "compliance_agent")
    logistics_task = next(t for t in tasks_list if t.agent_name == "logistics_agent")
    reply_task = next(t for t in tasks_list if t.agent_name == "reply_agent")

    assert compliance_task.dependencies == [price_task.id], "合规任务应依赖价格任务"
    assert logistics_task.dependencies == [compliance_task.id], "物流任务应依赖合规任务"
    assert reply_task.dependencies == [logistics_task.id], "回复任务应依赖物流任务"

    print("\n✓ 依赖关系验证通过")

    return graph


async def test_execute_graph(graph, email_id="test_ceo_001"):
    """测试任务执行功能"""
    print("\n" + "=" * 60)
    print("测试 2: CEO Agent 任务执行")
    print("=" * 60)

    ceo = CEOAgent(settings)

    # 执行任务图
    results = await ceo.execute_graph(graph, email_id)

    print(f"\n✓ 任务执行成功")
    print(f"  完成的任务：{len(results)}")

    # 打印执行结果
    print("\n执行结果:")
    for task_id, result in results.items():
        task = graph.tasks[task_id]
        print(f"  [{task.agent_name}]")
        print(f"      状态：{task.status}")
        print(f"      预算：${task.budget:.2f}")
        print(f"      结果：{list(result.keys())}")

    # 验证所有任务完成
    assert graph.is_complete(), "所有任务应该已完成"

    # 验证结果数量
    assert len(results) == 4, "应该有 4 个结果"

    print("\n✓ 任务执行验证通过")

    return results


async def test_database_integration(email_id="test_ceo_001"):
    """测试数据库集成"""
    print("\n" + "=" * 60)
    print("测试 3: 数据库记录验证")
    print("=" * 60)

    from email_agent.storage.database import get_database

    db = get_database(settings)

    # 查询 Agent 执行记录
    executions = await db.get_agent_executions(email_id=email_id)

    print(f"\n✓ 数据库查询成功")
    print(f"  执行记录数量：{len(executions)}")

    # 打印执行记录
    print("\n执行记录:")
    for ex in executions:
        print(f"  [{ex['agent_name']}]")
        print(f"      任务 ID: {ex['task_id']}")
        print(f"      状态：{ex['status']}")
        print(f"      预算：${ex['budget_allocated']:.2f}")
        print(f"      实际成本：${ex['actual_cost']:.2f}")

    # 验证记录数量
    assert len(executions) == 4, "应该有 4 条执行记录"

    print("\n✓ 数据库记录验证通过")

    return executions


async def main():
    """主测试函数"""
    print("\n" + "█" * 60)
    print("█ CEO Agent 端到端测试")
    print("█" * 60)

    try:
        # 测试 1: 任务分解
        graph = await test_decompose_inquiry()

        # 测试 2: 任务执行
        results = await test_execute_graph(graph)

        # 测试 3: 数据库集成
        executions = await test_database_integration()

        # 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"  任务分解测试：✓ 通过")
        print(f"  任务执行测试：✓ 通过")
        print(f"  数据库集成测试：✓ 通过")
        print(f"\n  总结果：✓ 全部通过")

        return True

    except AssertionError as e:
        print(f"\n✗ 测试失败：{e}")
        return False
    except Exception as e:
        print(f"\n✗ 意外错误：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
