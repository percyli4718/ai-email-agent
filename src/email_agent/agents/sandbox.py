"""
Agent 沙箱模块

模块作用:
    本模块实现 Agent 执行沙箱环境，提供预算硬限制和隔离的数据库环境。
    沙箱确保子 Agent 在受控环境中执行，防止预算超支和数据库污染。

使用场景:
    - 执行子 Agent 任务时进行预算控制
    - 为子 Agent 提供隔离的数据库环境
    - 捕获 Agent 执行异常并返回结构化结果

在项目中的位置:
    位于 src/email_agent/agents/sandbox.py，
    是 Agent 系统的基础设施组件，
    被 CEO Agent 调用以执行子 Agent 任务。
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
import sqlite3

from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


@dataclass
class AgentResult:
    """
    Agent 执行结果的数据结构

    作用:
        封装 Agent 执行的完整结果，包括成功状态、输出、成本和错误信息。
        使用 dataclass 提供简洁的数据容器。

    字段说明:
        success: bool 类型，执行是否成功
            True 表示成功完成，False 表示失败

        output: Any 类型，Agent 输出
            Agent 执行的结果数据，可以是任意类型

        actual_cost: float 类型，实际成本
            Agent 执行消耗的 API 成本 (美元)

        error: Optional[str] 类型，错误信息 (可选)
            执行失败时的错误描述，成功时为 None

    使用场景:
        - 作为 AgentSandbox.execute() 的返回值类型
        - 在 CEO Reviewer 中评估 Agent 执行质量
        - 在预算追踪器中记录实际支出
    """
    success: bool
    output: Any
    actual_cost: float
    error: Optional[str] = None


class WriteIsolatedDB:
    """
    隔离的 SQLite 数据库

    作用:
        为 Agent 沙箱提供内存级隔离的数据库环境。
        子 Agent 的所有数据库写操作都在内存数据库中进行，
        不会影响主数据库，确保数据隔离。

    使用场景:
        - 为子 Agent 提供临时数据存储
        - 防止子 Agent 污染主数据库
        - 测试 Agent 的数据库操作

    主要方法:
        _init_schema: 初始化数据库模式
        query: 执行查询操作
        execute: 执行写入操作 (隔离)

    属性:
        conn: sqlite3.Connection 类型，内存数据库连接
    """

    def __init__(self):
        """
        初始化隔离数据库

        参数:
            无

        返回值:
            无

        异常:
            无

        说明:
            使用 ":memory:" 创建内存数据库，
            数据仅存在于内存中，进程结束后自动销毁
        """
        # 创建内存数据库连接
        self.conn = sqlite3.connect(":memory:")
        # 初始化数据库模式
        self._init_schema()

    def _init_schema(self) -> None:
        """
        初始化数据库模式

        功能描述:
            在内存数据库中创建必要的表结构。
            包含价格表和合规表，供子 Agent 使用。

        参数:
            无

        返回值:
            无

        异常:
            无

        表结构:
            prices: 价格表
                - product_code: 产品代码 (主键)
                - base_price: 基础价格
                - currency: 货币类型

            compliance: 合规表
                - product_code: 产品代码
                - region: 区域
                - requirements: 合规要求
                - 主键：(product_code, region)
        """
        # 执行 SQL 脚本创建表结构
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS prices (
                product_code TEXT PRIMARY KEY,
                base_price REAL,
                currency TEXT
            );
            CREATE TABLE IF NOT EXISTS compliance (
                product_code TEXT,
                region TEXT,
                requirements TEXT,
                PRIMARY KEY (product_code, region)
            );
        """)

    def query(self, sql: str, params: tuple = ()) -> list:
        """
        执行数据库查询

        功能描述:
            执行只读查询操作，返回查询结果。
            使用参数化查询防止 SQL 注入。

        参数:
            sql: str 类型，SQL 查询语句
            params: tuple 类型，查询参数 (默认为空元组)

        返回值:
            list: 查询结果列表，每行是一个元组

        异常:
            sqlite3.Error: 当查询执行失败时抛出

        使用场景:
            - 子 Agent 查询价格信息
            - 子 Agent 查询合规要求
        """
        # 创建游标
        cursor = self.conn.cursor()
        # 执行参数化查询
        cursor.execute(sql, params)
        # 返回所有结果
        return cursor.fetchall()

    def execute(self, sql: str, params: tuple = ()) -> None:
        """
        执行数据库写入操作

        功能描述:
            执行写入操作 (INSERT/UPDATE/DELETE)，自动提交。
            所有写入都在内存数据库中，不影响主数据库。

        参数:
            sql: str 类型，SQL 写入语句
            params: tuple 类型，SQL 参数 (默认为空元组)

        返回值:
            无

        异常:
            sqlite3.Error: 当写入操作失败时抛出

        使用场景:
            - 子 Agent 临时存储中间结果
            - 子 Agent 更新状态信息
        """
        # 执行 SQL 语句
        self.conn.execute(sql, params)
        # 提交事务
        self.conn.commit()


class AgentSandbox:
    """
    Agent 沙箱

    作用:
        为子 Agent 提供隔离的执行环境，包括预算硬限制和数据库隔离。
        确保 Agent 在受控环境中运行，防止资源滥用。

    使用场景:
        - 执行 CEO Agent 分解的子任务
        - 控制每个 Agent 的预算支出
        - 隔离 Agent 的数据库操作

    主要方法:
        execute: 在沙箱中执行 Agent 函数

    属性:
        budget: float 类型，预算上限 (美元)
        spent: float 类型，已花费金额 (美元)
        isolated_db: WriteIsolatedDB 类型，隔离数据库实例

    预算控制说明:
        - 执行前检查预算是否已用尽
        - 如果预算用尽，直接返回失败结果 (硬限制)
        - 执行后更新已花费金额
    """

    def __init__(self, budget: float):
        """
        初始化 Agent 沙箱

        参数:
            budget: float 类型，预算上限 (美元)

        返回值:
            无

        异常:
            无
        """
        self.budget = budget  # 设置预算上限
        self.spent = 0.0  # 初始化已花费金额
        self.isolated_db = WriteIsolatedDB()  # 创建隔离数据库

    async def execute(
        self,
        agent_fn: Callable,
        input_data: Dict[str, Any],
        agent_name: str = "unknown"
    ) -> AgentResult:
        """
        在沙箱中执行 Agent 函数

        功能描述:
            在受控环境中执行 Agent 函数，进行预算检查和隔离数据库访问。
            捕获所有异常并返回结构化的执行结果。

        参数:
            agent_fn: Callable 类型，Agent 函数 (异步)
            input_data: Dict[str, Any] 类型，Agent 输入数据
            agent_name: str 类型，Agent 名称 (用于日志)

        返回值:
            AgentResult: Agent 执行结果
                - success: 执行是否成功
                - output: Agent 输出
                - actual_cost: 实际成本
                - error: 错误信息 (如果有)

        异常:
            无 (所有异常都被捕获并记录在结果中)

        执行流程:
            1. 检查预算是否已用尽 (硬限制)
            2. 如果预算充足，调用 Agent 函数
            3. 获取实际成本并更新花费
            4. 记录执行日志
            5. 返回执行结果
        """
        try:
            # 预算硬限制检查
            if self.spent >= self.budget:
                logger.warning(
                    "budget_hard_kill",
                    agent=agent_name,
                    budget=self.budget,
                    spent=self.spent
                )
                # 预算已用尽，直接返回失败结果
                return AgentResult(
                    success=False,
                    output=None,
                    actual_cost=self.spent,
                    error=f"Budget exceeded: {self.spent} >= {self.budget}"
                )

            # 执行 Agent 函数，传入输入数据和隔离数据库
            result = await agent_fn(
                input_data=input_data,
                db=self.isolated_db
            )

            # 获取实际成本 (默认 0.01 美元)
            actual_cost = getattr(result, 'cost', 0.01)
            # 更新已花费金额
            self.spent += actual_cost

            # 记录执行成功的日志
            logger.info(
                "agent_executed",
                agent=agent_name,
                cost=actual_cost,
                total_spent=self.spent
            )

            return AgentResult(
                success=True,
                output=result,
                actual_cost=self.spent
            )

        except Exception as e:
            # 捕获所有异常，记录错误日志
            logger.error("agent_execution_error", agent=agent_name, error=str(e))
            return AgentResult(
                success=False,
                output=None,
                actual_cost=self.spent,
                error=str(e)
            )
