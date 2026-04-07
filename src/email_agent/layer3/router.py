"""
Layer 3: 模型路由器模块

模块作用:
    本模块实现智能模型路由功能，根据请求的复杂度自动选择使用 Sonnet 或 Opus 模型。
    根据 JD 要求，80% 的请求应该路由到成本更低的 Sonnet 模型以控制成本。
    复杂度评估基于产品数量、合规要求、客户等级和订单价值估算。

使用场景:
    - 报价生成前选择合适的模型
    - 根据上下文复杂度动态调整模型选择
    - 平衡响应质量和 API 成本

在项目中的位置:
    位于 src/email_agent/layer3/router.py，
    是 Layer 3 生成器模块的辅助组件，
    被 generator.py 调用以决定使用哪个模型。
"""
from enum import Enum
from typing import Dict, Any

from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class ModelChoice(str, Enum):
    """
    可用的 Anthropic 模型枚举

    作用:
        定义可用的 Anthropic Claude 模型选项。
        使用 Enum 确保类型安全和 IDE 代码补全。

    成员:
        SONNET: Claude Sonnet 模型
            - 成本较低，适合常规任务
            - 目标处理 80% 的请求
            - 模型名：claude-sonnet-20241022

        OPUS: Claude Opus 模型
            - 成本较高，适合复杂任务
            - 处理约 20% 的高复杂度请求
            - 模型名：claude-opus-20241022

    使用场景:
        - 作为 ModelRouter.route() 的返回值类型
        - 在代码中进行模型选择判断
    """
    SONNET = "claude-sonnet-20241022"
    OPUS = "claude-opus-20241022"


class ModelRouter:
    """
    智能模型路由器

    作用:
        根据上下文复杂度智能选择使用 Sonnet 或 Opus 模型。
        通过复杂度评分实现成本优化，确保约 80% 的请求使用 Sonnet。

    使用场景:
        - 报价生成前选择模型
        - 根据产品数量、合规要求等因素评估复杂度
        - 平衡响应质量和 API 成本

    主要方法:
        route: 根据上下文决定使用哪个模型
        _calculate_complexity: 计算复杂度评分

    属性:
        target_sonnet_rate: float 类型，目标 Sonnet 路由率 (默认 0.80)

    复杂度评估因素:
        1. 产品数量：>5 个产品增加 0.2 分，>2 个增加 0.1 分
        2. 合规要求：特殊许可增加 0.3 分，限制增加 0.2 分
        3. 客户等级：新客户增加 0.2 分，C 级客户增加 0.1 分
        4. 阈值：<0.4 使用 Sonnet，>=0.4 使用 Opus
    """

    def __init__(self):
        """
        初始化模型路由器

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        # 目标 Sonnet 路由率为 80%，符合 JD 要求
        self.target_sonnet_rate = 0.80

    def route(self, context: Dict[str, Any]) -> ModelChoice:
        """
        根据上下文复杂度决定使用哪个模型

        功能描述:
            计算上下文的复杂度评分，根据评分选择合适的模型。
            评分<0.4 时使用 Sonnet(目标 80%)，否则使用 Opus。

        参数:
            context: Dict[str, Any] 类型，Layer 2 检索的上下文信息
                - pricing_policy: 定价政策 (包含产品列表)
                - compliance: 合规要求
                - customer_history: 客户历史记录

        返回值:
            ModelChoice: 选择的模型 (SONNET 或 OPUS)

        异常:
            无

        处理流程:
            1. 调用 _calculate_complexity 计算复杂度评分
            2. 评分<0.4: 返回 SONNET
            3. 评分>=0.4: 返回 OPUS
            4. 记录路由决策日志

        示例:
            >>> router = ModelRouter()
            >>> context = {"pricing_policy": {"products": ["drug_a"]}}
            >>> router.route(context)
            ModelChoice.SONNET
        """
        # 计算上下文复杂度评分 (0.0-1.0)
        complexity_score = self._calculate_complexity(context)

        # 根据复杂度评分选择模型
        # 评分<0.4 时使用 Sonnet (目标 80% 的请求)
        if complexity_score < 0.4:
            logger.info("model_routed", model="sonnet", complexity=complexity_score)
            return ModelChoice.SONNET
        else:
            logger.info("model_routed", model="opus", complexity=complexity_score)
            return ModelChoice.OPUS

    def _calculate_complexity(self, context: Dict[str, Any]) -> float:
        """
        计算上下文复杂度评分

        功能描述:
            基于多个因素计算 0.0-1.0 的复杂度评分。
            评分越高表示任务越复杂，越需要强大的模型。

        参数:
            context: Dict[str, Any] 类型，上下文信息
                - pricing_policy: 定价政策 (包含产品列表)
                - compliance: 合规要求 (special_permits, restrictions)
                - customer_history: 客户历史记录 (tier)

        返回值:
            float: 复杂度评分 (0.0-1.0)

        异常:
            无

        评分因素:
            1. 产品数量 (最高 +0.2):
               - >5 个产品：+0.2
               - >2 个产品：+0.1

            2. 合规要求 (最高 +0.5):
               - 特殊许可：+0.3
               - 出口限制：+0.2

            3. 客户历史 (最高 +0.2):
               - 新客户 (无历史记录): +0.2
               - C 级客户：+0.1

            4. 订单价值估算 (最高 +0.1):
               - 高价值订单：+0.1

            最终评分 = min(所有因素之和，1.0)
        """
        score = 0.0

        # 因素 1: 产品数量
        # 从定价政策中获取产品列表
        products = context.get("pricing_policy", {}).get("products", [])
        if len(products) > 5:
            score += 0.2  # 产品数量多，复杂度高
        elif len(products) > 2:
            score += 0.1  # 产品数量中等

        # 因素 2: 合规要求
        compliance = context.get("compliance", {})
        if compliance.get("special_permits"):
            score += 0.3  # 需要特殊许可，复杂度高
        if compliance.get("restrictions"):
            score += 0.2  # 有出口限制，复杂度中等

        # 因素 3: 客户历史记录
        customer = context.get("customer_history", {})
        if not customer:
            score += 0.2  # 新客户，需要更多谨慎
        elif customer.get("tier") == "C":
            score += 0.1  # C 级客户，略微增加复杂度

        # 返回最小值 (确保不超过 1.0)
        return min(score, 1.0)
