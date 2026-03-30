"""
CEO Agent 模块

模块作用:
    本模块实现 CEO Agent，负责将复杂的邮件处理任务分解为多个子 Agent 任务。
    CEO Agent 创建任务依赖图，协调价格查询、合规检查、物流计算和回复生成等子任务。

使用场景:
    - 收到复杂询价邮件时分解任务
    - 协调多个子 Agent 协同工作
    - 管理任务依赖关系和执行顺序

在项目中的位置:
    位于 src/email_agent/agents/ceo_agent.py，
    是 Agent 系统的最高层级协调者，
    依赖 sandbox 模块执行子 Agent 任务，
    依赖 reviewer 模块评审执行结果。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


@dataclass
class Task:
    """
    子 Agent 任务的数据结构

    作用:
        封装子 Agent 任务的完整信息，包括任务 ID、执行 Agent、输入数据、
        预算、依赖关系、输出结果和状态。

    字段说明:
        id: str 类型，任务唯一标识符
            使用 UUID 的前 8 位字符

        agent_name: str 类型，执行 Agent 名称
            例如："price_agent", "compliance_agent"

        input_data: Dict[str, Any] 类型，输入数据
            Agent 执行所需的参数

        budget: float 类型，预算上限
            该任务允许的最大支出 (美元)

        dependencies: List[str] 类型，依赖任务 ID 列表
            必须先完成的的任务 ID 列表

        output: Optional[Any] 类型，输出结果 (可选)
            任务完成后的输出数据

        status: str 类型，任务状态
            - "pending": 等待执行
            - "running": 执行中
            - "completed": 已完成
            - "failed": 执行失败

    使用场景:
        - 作为 DependencyGraph 的基本组成单元
        - 在 CEO Agent 中管理任务执行顺序
    """
    id: str
    agent_name: str
    input_data: Dict[str, Any]
    budget: float
    dependencies: List[str] = field(default_factory=list)
    output: Optional[Any] = None
    status: str = "pending"


@dataclass
class DependencyGraph:
    """
    任务依赖图

    作用:
        管理子 Agent 任务及其依赖关系。
        支持任务添加、依赖关系建立和就绪任务查询。

    使用场景:
        - CEO Agent 分解目标时创建任务图
        - 调度器根据依赖关系执行任务
        - 追踪任务执行进度

    主要方法:
        add_task: 添加任务到图中
        add_dependency: 添加任务间的依赖关系
        get_ready_tasks: 获取就绪可执行的任务
        is_complete: 检查所有任务是否完成

    属性:
        tasks: Dict[str, Task] 类型，任务字典
            键为任务 ID，值为 Task 对象
    """

    tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        budget: float,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """
        添加任务到依赖图

        功能描述:
            创建新任务并添加到图中。
            自动生成任务 ID，设置初始状态为 pending。

        参数:
            agent_name: str 类型，执行 Agent 名称
            input_data: Dict[str, Any] 类型，Agent 输入数据
            budget: float 类型，任务预算上限
            dependencies: Optional[List[str]] 类型，依赖任务 ID 列表 (可选)

        返回值:
            str: 新创建的任务 ID

        异常:
            无

        使用场景:
            - CEO Agent 分解目标时添加子任务
            - 动态添加依赖任务
        """
        # 生成任务 ID (UUID 前 8 位)
        task_id = str(uuid.uuid4())[:8]
        # 创建任务对象
        self.tasks[task_id] = Task(
            id=task_id,
            agent_name=agent_name,
            input_data=input_data,
            budget=budget,
            dependencies=dependencies or []  # 如果没有依赖，使用空列表
        )
        return task_id

    def add_dependency(self, from_task: str, to_task: str) -> None:
        """
        添加任务间的依赖关系

        功能描述:
            建立 from_task 到 to_task 的依赖关系。
            to_task 必须等待 from_task 完成后才能执行。

        参数:
            from_task: str 类型，前置任务 ID
            to_task: str 类型，后置任务 ID

        返回值:
            无

        异常:
            无

        使用场景:
            - 动态添加任务依赖
            - 调整任务执行顺序

        示例:
            # 价格查询必须在合规检查之前完成
            graph.add_dependency(price_task_id, compliance_task_id)
        """
        # 检查后置任务是否存在
        if to_task in self.tasks:
            # 添加前置任务到依赖列表
            self.tasks[to_task].dependencies.append(from_task)

    def get_ready_tasks(self) -> List[Task]:
        """
        获取就绪可执行的任务

        功能描述:
            返回所有状态为 pending 且依赖已满足的任务。
            依赖满足意味着所有前置任务都已完成。

        参数:
            无

        返回值:
            List[Task]: 就绪任务列表

        异常:
            无

        使用场景:
            - 调度器轮询可执行任务
            - 并行执行多个就绪任务

        执行逻辑:
            1. 遍历所有任务，筛选 pending 状态的任务
            2. 检查每个任务的所有依赖是否 completed
            3. 返回依赖已满足的任务列表
        """
        ready = []
        for task in self.tasks.values():
            # 跳过非 pending 状态的任务
            if task.status != "pending":
                continue
            # 检查所有依赖是否已完成
            deps_satisfied = all(
                self.tasks[dep].status == "completed"
                for dep in task.dependencies
            )
            # 依赖已满足，添加到就绪列表
            if deps_satisfied:
                ready.append(task)
        return ready

    def is_complete(self) -> bool:
        """
        检查所有任务是否完成

        功能描述:
            检查图中所有任务的状态是否为 completed 或 failed。
            只要有任务处于 pending 或 running 状态，返回 False。

        参数:
            无

        返回值:
            bool: True 表示所有任务完成，False 表示仍有任务在执行

        异常:
            无

        使用场景:
            - 检查 CEO 任务分解是否全部完成
            - 决定是否继续进行下一步处理
        """
        # 检查所有任务是否都处于终态 (completed 或 failed)
        return all(
            t.status in ("completed", "failed")
            for t in self.tasks.values()
        )


class CEOAgent:
    """
    CEO Agent

    作用:
        CEO Agent 是任务分解和协调的核心。
        它将复杂的邮件处理目标分解为多个子 Agent 任务，
        并建立任务间的依赖关系。

    使用场景:
        - 处理复杂询价邮件
        - 协调价格、合规、物流等多个子任务
        - 生成任务依赖图供调度器执行

    主要方法:
        decompose_inquiry: 将询价分解为子 Agent 任务

    属性:
        无 (无状态，每次调用 decompose_inquiry 创建新的 DependencyGraph)

    任务分解说明:
        CEO Agent 将询价邮件分解为以下任务:
        1. Price Agent: 查询产品价格
        2. Compliance Agent: 检查目的地合规要求 (仅国际订单)
        3. Logistics Agent: 计算物流成本
        4. Reply Agent: 生成回复邮件
    """

    def decompose_inquiry(
        self,
        email_body: str,
        classification: dict
    ) -> DependencyGraph:
        """
        将询价邮件分解为子 Agent 任务

        功能描述:
            根据邮件内容和分类结果，创建任务依赖图。
            包括价格查询、合规检查、物流计算和回复生成任务。

        参数:
            email_body: str 类型，邮件正文内容
            classification: dict 类型，Layer 1 生成的分类结果
                - products_mentioned: 提及的产品列表
                - customer_region: 客户所在区域

        返回值:
            DependencyGraph: 任务依赖图，包含 4 个任务及其依赖关系

        异常:
            无

        处理流程:
            1. 创建价格查询任务 (无依赖)
            2. 如果是国际订单，创建合规检查任务 (依赖价格任务)
            3. 创建物流计算任务 (依赖合规任务)
            4. 创建回复生成任务 (依赖物流任务)
            5. 记录分解日志并返回任务图

        任务依赖关系:
            price_task -> compliance_task -> logistics_task -> reply_task
        """
        # 创建新的依赖图
        graph = DependencyGraph()
        # 从分类结果中提取产品和区域信息
        products = classification.get("products_mentioned", [])
        region = classification.get("customer_region", "other")

        # 任务 1: 价格查询
        # 查询提及产品的基准价格
        price_task = graph.add_task(
            agent_name="price_agent",
            input_data={"products": products},
            budget=0.10  # 预算 0.10 美元
        )

        # 任务 2: 合规检查 (仅国际订单)
        # 如果不是国内订单，需要检查目的地合规要求
        if region != "domestic":
            compliance_task = graph.add_task(
                agent_name="compliance_agent",
                input_data={"products": products, "destination": region},
                budget=0.15,  # 预算 0.15 美元
                dependencies=[price_task]  # 依赖价格查询完成
            )
        else:
            # 国内订单不需要合规检查，直接使用价格任务
            compliance_task = price_task

        # 任务 3: 物流计算
        # 计算产品和目的地的物流成本
        logistics_task = graph.add_task(
            agent_name="logistics_agent",
            input_data={"products": products, "destination": region},
            budget=0.12,  # 预算 0.12 美元
            dependencies=[compliance_task]  # 依赖合规检查完成
        )

        # 任务 4: 回复生成
        # 基于所有前置任务的结果生成回复
        graph.add_task(
            agent_name="reply_agent",
            input_data={"email_body": email_body, "classification": classification},
            budget=0.08,  # 预算 0.08 美元
            dependencies=[logistics_task]  # 依赖物流计算完成
        )

        # 记录任务分解日志
        logger.info(
            "ceo_decomposed_goal",
            task_count=len(graph.tasks)
        )

        return graph
