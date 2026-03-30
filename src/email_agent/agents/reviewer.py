"""
CEO 评审器模块

模块作用:
    本模块实现 CEO Reviewer，负责评审子 Agent 的交付成果。
    通过质量评估决定子 Agent 的输出是否可以被接受，或者需要重新执行。

使用场景:
    - 子 Agent 任务完成后进行质量评审
    - 根据质量评分决定 promote/redelegate/reject
    - 记录评审历史用于后续分析

在项目中的位置:
    位于 src/email_agent/agents/reviewer.py，
    是 Agent 系统的质量控制组件，
    与 ceo_agent.py 和 sandbox.py 配合使用。
"""
from enum import Enum
from typing import Any

from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class Decision(str, Enum):
    """
    CEO 评审决策枚举

    作用:
        定义 CEO Reviewer 可能的评审决策。
        使用 Enum 确保类型安全和代码可读性。

    成员:
        PROMOTE: 通过评审
            - 质量评分 >= 阈值 (默认 0.8)
            - 输出可被接受，进入下一环节

        REDELEGATE: 重新执行
            - 质量评分 >= 0.5 但 < 阈值
            - 输出需要改进，重新分配任务

        REJECT: 拒绝
            - 质量评分 < 0.5
            - 输出质量太差，需要人工干预

    使用场景:
        - 作为 CEOReviewer.review() 的返回值类型
        - 在任务调度器中决定下一步操作
    """
    PROMOTE = "promote"      # 通过，接受输出
    REDELEGATE = "redelegate"  # 重新执行
    REJECT = "reject"        # 拒绝，需要人工干预


class CEOReviewer:
    """
    CEO 评审器

    作用:
        评审子 Agent 的交付成果，根据质量评估做出决策。
        确保只有符合质量标准的输出才能被接受。

    使用场景:
        - 子 Agent 任务完成后进行质量评审
        - 根据评审结果决定任务流转
        - 记录评审历史用于性能分析

    主要方法:
        review: 评审子 Agent 的交付成果
        _evaluate_quality: 评估输出质量

    属性:
        review_history: list 类型，评审历史记录
            记录每次评审的质量评分和决策

    评审流程:
        1. 调用 _evaluate_quality 评估输出质量
        2. 根据质量评分做出决策:
           - >= 0.8: PROMOTE (通过)
           - 0.5-0.8: REDELEGATE (重新执行)
           - < 0.5: REJECT (拒绝)
        3. 记录评审历史
        4. 返回决策结果
    """

    def __init__(self):
        """
        初始化 CEO 评审器

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        # 初始化评审历史记录列表
        self.review_history = []

    def review(self, task_result: Any, quality_threshold: float = 0.8) -> Decision:
        """
        评审子 Agent 的交付成果

        功能描述:
            评估子 Agent 输出质量，根据评分做出评审决策。
            默认质量阈值为 0.8 (80 分)。

        参数:
            task_result: Any 类型，子 Agent 的执行结果
                通常是 AgentResult 对象

            quality_threshold: float 类型，质量阈值 (默认 0.8)
                高于此分数为 PROMOTE，低于 0.5 为 REJECT

        返回值:
            Decision: 评审决策
                - PROMOTE: 通过，质量 >= 阈值
                - REDELEGATE: 重新执行，0.5 <= 质量 < 阈值
                - REJECT: 拒绝，质量 < 0.5

        异常:
            无

        评审流程:
            1. 调用 _evaluate_quality 评估质量
            2. 根据评分选择决策
            3. 记录评审历史
            4. 返回决策

        使用场景:
            - 子 Agent 任务完成后调用
            - 决定任务是否可以进入下一环节
        """
        # 评估输出质量 (0.0-1.0)
        quality_score = self._evaluate_quality(task_result)

        # 根据质量评分做出决策
        if quality_score >= quality_threshold:
            # 质量达标，通过评审
            decision = Decision.PROMOTE
        elif quality_score >= 0.5:
            # 质量中等，需要重新执行
            decision = Decision.REDELEGATE
        else:
            # 质量太差，拒绝
            decision = Decision.REJECT

        # 记录评审历史
        self.review_history.append({
            "quality_score": quality_score,
            "decision": decision.value
        })

        # 记录评审完成日志
        logger.info(
            "ceo_review_completed",
            quality=quality_score,
            decision=decision.value
        )

        return decision

    def _evaluate_quality(self, result: Any) -> float:
        """
        评估输出质量

        功能描述:
            根据 AgentResult 的属性计算质量评分。
            从 1.0 开始，根据问题逐项扣分。

        参数:
            result: Any 类型，Agent 执行结果
                通常具有 output, error, success 属性

        返回值:
            float: 质量评分 (0.0-1.0)

        异常:
            无

        评分规则:
            - 基础分：1.0
            - output 为 None: -0.5
            - 有 error: -0.3
            - success 为 False: -0.4
            - 最低分：0.0

        评分示例:
            - 成功且有输出：1.0
            - 成功但无输出：0.5
            - 失败但有输出：0.6
            - 失败且无输出：0.0
        """
        # 空结果直接返回 0 分
        if result is None:
            return 0.0

        # 从满分开始扣分
        score = 1.0

        # 检查 output 属性
        if hasattr(result, 'output'):
            # output 为 None 扣 0.5 分
            if result.output is None:
                score -= 0.5
            # 有 error 扣 0.3 分
            if hasattr(result, 'error') and result.error:
                score -= 0.3

        # 检查 success 属性
        if hasattr(result, 'success'):
            # 执行失败扣 0.4 分
            if not result.success:
                score -= 0.4

        # 确保分数不低于 0.0
        return max(0.0, score)
