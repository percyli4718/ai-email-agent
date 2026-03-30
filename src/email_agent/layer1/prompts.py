"""
Layer 1: 提示词模板模块

模块作用:
    本模块定义电子邮件分类器使用的提示词模板和类型定义。
    包含分类结果的数据结构 (EmailClassification) 和用于调用 LLM 的分类提示词模板。

使用场景:
    - classifier.py 导入 CLASSIFIER_PROMPT 用于邮件分类
    - 定义分类结果的类型约束，确保数据结构一致性
    - 调整提示词模板以优化分类准确率

在项目中的位置:
    位于 src/email_agent/layer1/prompts.py，
    是 Layer 1 分类器模块的组成部分，
    为 classifier.py 提供提示词模板和类型定义。
"""
from typing import TypedDict, Optional, List


class EmailClassification(TypedDict, total=False):
    """
    电子邮件分类结果的数据结构

    作用:
        定义邮件分类结果的 Schema，使用 TypedDict 提供类型检查。
        total=False 表示所有字段都是可选的，便于部分更新。

    字段说明:
        type: str 类型，邮件类型
            - inquiry: 询价、产品信息或价格咨询
            - complaint: 订单、质量、配送或服务投诉
            - status_check: 订单状态或物流追踪查询
            - other: 其他类型邮件

        priority_score: float 类型，优先级分数 (0.0-1.0)
            - 0.9-1.0: VIP 客户、大订单 (>50k USD)、紧急截止日期
            - 0.7-0.9: 常规咨询、时间敏感
            - 0.4-0.6: 标准咨询
            - 0.0-0.3: 低优先级、垃圾邮件或内容不清

        urgency: str 类型，紧急程度
            - low: 低优先级
            - medium: 中等优先级
            - high: 高优先级

        language: str 类型，邮件语言代码
            - en: 英语
            - pt: 葡萄牙语
            - es: 西班牙语
            - fr: 法语
            - de: 德语
            - zh: 中文
            - ar: 阿拉伯语

        products_mentioned: list[str] 类型，邮件中提及的药品产品名称列表

        customer_region: str 类型，客户所在区域或国家

        requires_human: bool 类型，是否需要人工处理
            - true: 投诉、复杂问题或优先级>0.8
            - false: 可自动处理

        suggested_route: str 类型，建议的处理路由
            - quote_flow: 报价流程 (用于询价邮件)
            - complaint_flow: 投诉处理流程
            - status_flow: 状态查询流程
            - general_flow: 通用处理流程

    使用场景:
        - 作为 classify() 函数的返回值类型
        - 确保分类结果数据结构的一致性
        - IDE 和类型检查工具提供代码补全和错误检测
    """
    type: str  # 邮件类型：inquiry, complaint, status_check, other
    priority_score: float  # 优先级分数：0.0 - 1.0
    urgency: str  # 紧急程度：low, medium, high
    language: str  # 语言代码：en, pt, es, fr, de, zh, ar
    products_mentioned: list[str]  # 邮件中提及的产品名称列表
    customer_region: str  # 客户所在区域/国家
    requires_human: bool  # 是否需要人工处理
    suggested_route: str  # 建议路由：quote_flow, complaint_flow, status_flow, general_flow


# 电子邮件分类提示词模板
# 用于指导 Claude 模型对邮件进行分类分析
CLASSIFIER_PROMPT = """
You are an email classification specialist for pharmaceutical distribution.

Classify the following email and return a JSON object with the classification result.

【Subject】
{subject}

【Email Body】
{email_body}

Return a JSON object with this exact schema:
{{
  "type": "<inquiry|complaint|status_check|other>",
  "priority_score": <float 0.0-1.0>,
  "urgency": "<low|medium|high>",
  "language": "<en|pt|es|fr|de|zh|ar>",
  "products_mentioned": ["<product name>", ...],
  "customer_region": "<region/country>",
  "requires_human": <true|false>,
  "suggested_route": "<quote_flow|complaint_flow|status_flow|general_flow>"
}}

Classification guidelines:
1. Type:
   - inquiry: Request for quote, product information, or pricing
   - complaint: Issue with order, quality, delivery, or service
   - status_check: Asking about order status or shipment tracking
   - other: Everything else

2. Priority score:
   - 0.9-1.0: VIP customer, large order (>50k USD), urgent deadline
   - 0.7-0.9: Regular inquiry, time-sensitive
   - 0.4-0.6: Standard inquiry
   - 0.0-0.3: Low priority, spam, or unclear

3. Urgency:
   - high: Mentions deadline, urgent, ASAP, or VIP customer
   - medium: Normal business timeframe
   - low: No urgency indicated

4. Products: List all pharmaceutical products mentioned

5. Region: Infer from email content, company domain, or explicit mention

6. Requires human: true if complaint, complex issue, or priority > 0.8

7. Suggested route:
   - quote_flow: Type is inquiry
   - complaint_flow: Type is complaint
   - status_flow: Type is status_check
   - general_flow: Type is other

Output ONLY the JSON, no additional text.
"""
