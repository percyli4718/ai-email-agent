"""
Prompt 进化模块 (Karpathy Autoresearch 模式)

模块作用:
    本模块实现 Prompt 自动进化系统，通过 Ground Truth 数据集自动评估和优化 Prompt 模板。
    参考 Andrej Karpathy 的 autoresearch 模式，使用变异 - 评估 - 选择循环不断改进 Prompt。

使用场景:
    - 自动优化 Layer 1 分类器 Prompt 模板
    - 自动优化 Layer 3 生成器 Prompt 模板
    - 追踪 Prompt 版本历史和准确率变化
    - A/B 测试不同 Prompt 变体

在项目中的位置:
    位于 src/email_agent/evolution/prompt_evolution.py，
    是 AI Email Agent 系统的自优化组件，
    依赖 metrics 模块追踪准确率指标。
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


class MutationStrategy(str, Enum):
    """Prompt 变异策略"""
    ADD_CONSTRAINT = "add_constraint"
    ADD_EXAMPLE = "add_example"
    REPHRASE = "rephrase"
    SIMPLIFY = "simplify"
    EXPAND = "expand"


@dataclass
class PromptVersion:
    """Prompt 版本记录"""
    version: int
    template: str
    accuracy: float
    evaluated_at: datetime
    ground_truth_size: int
    changes_description: str
    parent_version: Optional[int] = None
    mutation_strategy: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "template": self.template,
            "accuracy": self.accuracy,
            "evaluated_at": self.evaluated_at.isoformat(),
            "ground_truth_size": self.ground_truth_size,
            "changes_description": self.changes_description,
            "parent_version": self.parent_version,
            "mutation_strategy": self.mutation_strategy,
        }


@dataclass
class GroundTruthSample:
    """Ground Truth 样本"""
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    sample_id: str = field(default_factory=lambda: "")

    def __post_init__(self):
        if not self.sample_id:
            # 自动生成 ID
            content = json.dumps(self.input_data, sort_keys=True)
            self.sample_id = hashlib.md5(content.encode()).hexdigest()[:12]


class PromptEvolution:
    """
    Prompt 进化器

    作用:
        实现 Karpathy autoresearch 模式的 Prompt 自动进化系统。
        通过变异 - 评估 - 选择循环，持续优化 Prompt 模板的准确率。

    使用场景:
        - 优化 Layer 1 分类器 Prompt
        - 优化 Layer 3 生成器 Prompt
        - A/B 测试不同 Prompt 变体

    属性:
        name: str 类型，Prompt 名称 (用于标识不同用途的 Prompt)
        ground_truth: List[GroundTruthSample] 类型，Ground Truth 数据集
        current_version: Optional[PromptVersion] 类型，当前版本
        version_history: List[PromptVersion] 类型，版本历史
    """

    def __init__(self, name: str, ground_truth_path: Optional[str] = None):
        """
        初始化 Prompt 进化器

        参数:
            name: str 类型，Prompt 名称
            ground_truth_path: Optional[str] 类型，Ground Truth 数据集路径 (可选)
        """
        self.name = name
        self.ground_truth: List[GroundTruthSample] = []
        self.current_version: Optional[PromptVersion] = None
        self.version_history: List[PromptVersion] = []
        self.current_accuracy = 0.0

        # 如果有 Ground Truth 路径，加载数据集
        if ground_truth_path:
            self.load_ground_truth(ground_truth_path)

        logger.info(f"prompt_evolution_initialized", name=name)

    def load_ground_truth(self, file_path: str) -> int:
        """
        加载 Ground Truth 数据集

        参数:
            file_path: str 类型，JSON 文件路径

        返回:
            int: 加载的样本数量

        数据格式:
            [
                {
                    "input": {"subject": "...", "body": "..."},
                    "expected": {"type": "inquiry", "urgency": "high", ...}
                },
                ...
            ]
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.ground_truth = [
                GroundTruthSample(
                    input_data=item["input"],
                    expected_output=item["expected"],
                    sample_id=item.get("id", "")
                )
                for item in data
            ]

            logger.info(
                "ground_truth_loaded",
                path=file_path,
                samples=len(self.ground_truth)
            )
            return len(self.ground_truth)

        except Exception as e:
            logger.error(f"ground_truth_load_failed", path=file_path, error=str(e))
            return 0

    def add_ground_truth_sample(
        self,
        input_data: Dict[str, Any],
        expected_output: Dict[str, Any],
        sample_id: Optional[str] = None
    ) -> str:
        """
        添加单个 Ground Truth 样本

        参数:
            input_data: Dict 类型，输入数据
            expected_output: Dict 类型，期望输出
            sample_id: Optional[str] 类型，样本 ID (可选，自动生成)

        返回:
            str: 样本 ID
        """
        sample = GroundTruthSample(
            input_data=input_data,
            expected_output=expected_output,
            sample_id=sample_id or ""
        )
        self.ground_truth.append(sample)
        logger.info("ground_truth_sample_added", sample_id=sample.sample_id)
        return sample.sample_id

    def mutate(self, template: str, strategy: Optional[MutationStrategy] = None) -> List[str]:
        """
        生成 Prompt 变体

        参数:
            template: str 类型，当前 Prompt 模板
            strategy: Optional[MutationStrategy] 类型，变异策略 (可选，随机选择)

        返回:
            List[str]: Prompt 变体列表 (通常 3-5 个)

        变异策略:
            1. ADD_CONSTRAINT: 添加新的约束条件
            2. ADD_EXAMPLE: 添加示例输出
            3. REPHRASE: 调整措辞
            4. SIMPLIFY: 简化表达
            5. EXPAND: 扩展说明
        """
        variants = []

        # 如果未指定策略，生成所有变体
        strategies = [strategy] if strategy else list(MutationStrategy)

        for strat in strategies:
            variant = self._apply_mutation(template, strat)
            if variant:
                variants.append(variant)

        logger.info(
            "prompt_variants_generated",
            parent_version=self.current_version.version if self.current_version else 0,
            variants_count=len(variants)
        )
        return variants

    def _apply_mutation(
        self,
        template: str,
        strategy: MutationStrategy
    ) -> Optional[str]:
        """
        应用单个变异策略

        参数:
            template: str 类型，当前 Prompt 模板
            strategy: MutationStrategy 类型，变异策略

        返回:
            Optional[str]: 变异后的模板，如果失败返回 None
        """
        try:
            if strategy == MutationStrategy.ADD_CONSTRAINT:
                return self._add_constraint(template)
            elif strategy == MutationStrategy.ADD_EXAMPLE:
                return self._add_example(template)
            elif strategy == MutationStrategy.REPHRASE:
                return self._rephrase(template)
            elif strategy == MutationStrategy.SIMPLIFY:
                return self._simplify(template)
            elif strategy == MutationStrategy.EXPAND:
                return self._expand(template)
            else:
                return None
        except Exception as e:
            logger.error(f"mutation_failed", strategy=strategy.value, error=str(e))
            return None

    def _add_constraint(self, template: str) -> str:
        """添加约束条件"""
        constraints = [
            "\n\nIMPORTANT: Output ONLY the JSON, no additional text or explanation.",
            "\n\nCONSTRAINT: Your response must strictly follow the JSON schema above.",
            "\n\nNOTE: Ensure all fields are present and correctly typed.",
            "\n\nREQUIREMENT: Double-check your output before submitting.",
        ]
        # 选择第一个未使用的约束
        for constraint in constraints:
            if constraint not in template:
                return template + constraint
        return template + constraints[0]

    def _add_example(self, template: str) -> str:
        """添加示例"""
        example_section = """

Example output:
```json
{
  "type": "inquiry",
  "priority_score": 0.85,
  "urgency": "high",
  "language": "en",
  "products_mentioned": ["Product A", "Product B"],
  "customer_region": "Europe",
  "requires_human": false,
  "suggested_route": "quote_flow"
}
```"""
        if "Example output" not in template:
            return template + example_section
        return template

    def _rephrase(self, template: str) -> str:
        """调整措辞"""
        replacements = [
            ("You are", "Act as"),
            ("Classify", "Analyze and categorize"),
            ("Return", "Output"),
            ("Please", "Kindly"),
        ]
        result = template
        for old, new in replacements:
            result = result.replace(old, new, 1)
        return result

    def _simplify(self, template: str) -> str:
        """简化表达"""
        # 移除冗余说明
        simplifications = [
            ("Please note that", ""),
            ("It is important to", ""),
            ("Make sure to", ""),
        ]
        result = template
        for old, new in simplifications:
            result = result.replace(old, new)
        return result

    def _expand(self, template: str) -> str:
        """扩展说明"""
        expansion = """

Additional guidance:
- Carefully read the entire email before classifying
- Consider context clues like tone, urgency, and specific keywords
- When in doubt, prefer more conservative classifications
"""
        if "Additional guidance" not in template:
            return template + expansion
        return template

    async def evaluate(
        self,
        predict_fn: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        template: str
    ) -> float:
        """
        评估 Prompt 准确率

        参数:
            predict_fn: 预测函数，接收输入数据返回预测结果
            template: str 类型，待评估的 Prompt 模板

        返回:
            float: 准确率 (0.0-1.0)

        评估方法:
            对每个 Ground Truth 样本:
            1. 使用 template 调用 predict_fn 获取预测
            2. 比较预测结果与期望输出
            3. 计算正确率
        """
        if not self.ground_truth:
            logger.warning("evaluation_skipped", reason="no_ground_truth")
            return 0.0

        correct = 0
        for sample in self.ground_truth:
            try:
                prediction = await predict_fn(sample.input_data)
                if self._compare(prediction, sample.expected_output):
                    correct += 1
            except Exception as e:
                logger.error(
                    "prediction_error",
                    sample_id=sample.sample_id,
                    error=str(e)
                )

        accuracy = correct / len(self.ground_truth)
        logger.info(
            "prompt_evaluated",
            template_hash=hashlib.md5(template.encode()).hexdigest()[:8],
            accuracy=accuracy,
            correct=correct,
            total=len(self.ground_truth)
        )
        return accuracy

    def _compare(self, prediction: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """
        比较预测结果与期望输出

        参数:
            prediction: Dict 类型，预测结果
            expected: Dict 类型，期望输出

        返回:
            bool: 是否匹配

        比较策略:
            - 对关键字段进行精确匹配
            - 允许数值字段有小误差
        """
        # 关键字段必须完全匹配
        critical_fields = ["type", "urgency", "language", "suggested_route", "requires_human"]

        for field in critical_fields:
            if field in expected and field in prediction:
                if prediction[field] != expected[field]:
                    return False

        # 数值字段允许误差
        if "priority_score" in expected and "priority_score" in prediction:
            diff = abs(prediction["priority_score"] - expected["priority_score"])
            if diff > 0.2:  # 允许 0.2 的误差
                return False

        return True

    async def evolve(
        self,
        predict_fn: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        base_template: str,
        num_iterations: int = 10,
        min_improvement: float = 0.01
    ) -> PromptVersion:
        """
        执行进化循环

        参数:
            predict_fn: 预测函数
            base_template: str 类型，基础 Prompt 模板
            num_iterations: int 类型，进化迭代次数
            min_improvement: float 类型，最小改进阈值

        返回:
            PromptVersion: 最佳版本

        进化流程:
            1. 评估当前模板
            2. 生成变体
            3. 评估所有变体
            4. 选择最佳者
            5. 如果有改进，设为当前版本
            6. 重复直到达到迭代次数或无改进
        """
        # 初始化当前版本
        if not self.current_version:
            initial_accuracy = await self.evaluate(predict_fn, base_template)
            self.current_version = PromptVersion(
                version=1,
                template=base_template,
                accuracy=initial_accuracy,
                evaluated_at=datetime.utcnow(),
                ground_truth_size=len(self.ground_truth),
                changes_description="Initial version",
            )
            self.version_history.append(self.current_version)
            self.current_accuracy = initial_accuracy
            logger.info("initial_prompt_evaluated", accuracy=initial_accuracy)

        best_version = self.current_version

        for iteration in range(num_iterations):
            logger.info("evolution_iteration", iteration=iteration + 1, current_best=best_version.accuracy)

            # 生成变体
            variants = self.mutate(best_version.template)

            # 评估所有变体
            variant_scores = []
            for variant in variants:
                accuracy = await self.evaluate(predict_fn, variant)
                variant_scores.append((variant, accuracy))

            # 选择最佳者
            if variant_scores:
                best_variant, best_accuracy = max(variant_scores, key=lambda x: x[1])

                # 如果有改进，接受变体
                if best_accuracy > best_version.accuracy + min_improvement:
                    new_version = PromptVersion(
                        version=len(self.version_history) + 1,
                        template=best_variant,
                        accuracy=best_accuracy,
                        evaluated_at=datetime.utcnow(),
                        ground_truth_size=len(self.ground_truth),
                        changes_description=f"Improved by {best_accuracy - best_version.accuracy:.2%}",
                        parent_version=best_version.version,
                        mutation_strategy="best_of_variants",
                    )
                    self.version_history.append(new_version)
                    best_version = new_version
                    self.current_accuracy = best_accuracy
                    logger.info(
                        "prompt_improved",
                        new_version=new_version.version,
                        accuracy=best_accuracy,
                        improvement=best_accuracy - best_version.accuracy
                    )
                else:
                    logger.info("no_significant_improvement", best_variant_accuracy=best_accuracy)

        logger.info("evolution_completed", best_accuracy=best_version.accuracy, total_versions=len(self.version_history))
        return best_version

    def save_version(self, version: PromptVersion, storage_path: str) -> bool:
        """
        保存 Prompt 版本到存储

        参数:
            version: PromptVersion 类型，版本记录
            storage_path: str 类型，存储路径

        返回:
            bool: 是否成功保存
        """
        try:
            import os

            # 确保目录存在
            os.makedirs(storage_path, exist_ok=True)

            # 保存版本文件
            file_path = os.path.join(storage_path, f"v{version.version}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(version.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info("prompt_version_saved", version=version.version, path=file_path)
            return True

        except Exception as e:
            logger.error("prompt_version_save_failed", version=version.version, error=str(e))
            return False

    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [v.to_dict() for v in self.version_history]

    def get_best_version(self) -> Optional[PromptVersion]:
        """获取最佳版本"""
        if not self.version_history:
            return None
        return max(self.version_history, key=lambda v: v.accuracy)

    def export_comparison(self) -> Dict[str, Any]:
        """导出版本对比报告"""
        return {
            "prompt_name": self.name,
            "current_accuracy": self.current_accuracy,
            "total_versions": len(self.version_history),
            "versions": self.get_version_history(),
            "best_version": self.get_best_version().to_dict() if self.get_best_version() else None,
        }
