"""
模拟数据注入器模块

模块作用:
    本模块负责将模拟邮件数据注入到 ChromaDB 向量数据库和 SQLite 数据库中。
    用于测试和演示目的，提供真实的向量搜索和数据持久化功能。

使用场景:
    - 应用启动时初始化测试数据
    - 演示模式下展示功能
    - 开发环境测试向量搜索

在项目中的位置:
    位于 src/email_agent/retriever/mock_data_injector.py，
    属于检索层数据注入组件，被 main.py 调用初始化数据。
"""
import json
import subprocess
from typing import List, Dict, Any
from src.email_agent.logging_config import get_logger
from src.email_agent.retriever.chroma_init import get_chromadb_client

logger = get_logger(__name__)


# 模拟邮件数据 (10 封邮件)
MOCK_EMAILS = [
    {
        "id": "email-001",
        "from_address": "support@amazon.com",
        "subject": "您的订单已发货 | Your order has been shipped",
        "body": "尊敬的客户，您的订单 #12345 已通过顺丰快递发出，运单号 SF1234567890。预计 3 个工作日内送达。",
        "priority": "medium",
        "category": "transactional",
        "region": "CN"
    },
    {
        "id": "email-002",
        "from_address": "billing@github.com",
        "subject": "GitHub Pro 订阅续费通知 | GitHub Pro Subscription Renewal",
        "body": "您的 GitHub Pro 订阅将于 2026 年 4 月 15 日续费，金额为 $4.00。如需取消订阅，请访问账户设置页面。",
        "priority": "medium",
        "category": "billing",
        "region": "US"
    },
    {
        "id": "email-003",
        "from_address": "hr@company.com",
        "subject": "2026 年度绩效评估开始 | 2026 Annual Performance Review Starts",
        "body": "各位员工，2026 年度绩效评估正式开始。请于 4 月 30 日前完成自我评估并与主管预约评估会议。",
        "priority": "high",
        "category": "internal",
        "region": "CN"
    },
    {
        "id": "email-004",
        "from_address": "security@google.com",
        "subject": "安全提醒：新设备登录 | Security Alert: New Device Login",
        "body": "我们检测到您的 Google 账户于 2026 年 3 月 29 日从新设备登录。如非本人操作，请立即更改密码。",
        "priority": "high",
        "category": "security",
        "region": "US"
    },
    {
        "id": "email-005",
        "from_address": "newsletter@techcrunch.com",
        "subject": "TechCrunch 每日简报 | Daily Briefing",
        "body": "今日科技新闻：AI 初创公司融资创新高，苹果公司发布新 iPad，特斯拉季度交付量超预期。",
        "priority": "low",
        "category": "newsletter",
        "region": "US"
    },
    {
        "id": "email-006",
        "from_address": "payments@stripe.com",
        "subject": "付款成功确认 | Payment Confirmation #STR-789012",
        "body": "您已成功支付 $99.00 给 Example Corp。交易 ID: STR-789012。如需退款，请在 30 天内联系客服。",
        "priority": "medium",
        "category": "transactional",
        "region": "US"
    },
    {
        "id": "email-007",
        "from_address": "support@dingtalk.com",
        "subject": "钉钉会议邀请：Q2 产品规划评审 | DingTalk Meeting Invitation",
        "body": "您已被邀请参加 Q2 产品规划评审会议。时间：2026 年 4 月 5 日 14:00-16:00。请点击链接接受邀请。",
        "priority": "high",
        "category": "meeting",
        "region": "CN"
    },
    {
        "id": "email-008",
        "from_address": "legal@company.com",
        "subject": "合同审批流程更新 | Contract Approval Process Update",
        "body": "自 2026 年 4 月 1 日起，所有超过$50,000 的合同需要 CFO 审批。请参见附件详细流程说明。",
        "priority": "medium",
        "category": "legal",
        "region": "US"
    },
    {
        "id": "email-009",
        "from_address": "noreply@linkedin.com",
        "subject": "你有 5 个新联系人建议 | 5 New Connection Suggestions",
        "body": "基于您的行业和人脉，我们为您推荐了 5 位新的联系人。点击查看详情并发送连接邀请。",
        "priority": "low",
        "category": "social",
        "region": "US"
    },
    {
        "id": "email-010",
        "from_address": "finance@company.com",
        "subject": "Q1 预算执行报告 | Q1 Budget Execution Report",
        "body": "附件为 2026 年 Q1 预算执行报告。总收入超出预期 15%，市场营销费用控制在预算范围内。",
        "priority": "high",
        "category": "finance",
        "region": "CN"
    }
]


def generate_embedding_with_ollama(text: str, model: str = "nomic-embed-text") -> List[float]:
    """
    使用 Ollama 生成 embedding 向量

    参数:
        text: 需要生成 embedding 的文本
        model: 使用的模型名称

    返回:
        embedding 向量列表
    """
    try:
        # 使用 curl 直接调用 Ollama API，绕过 httpx 代理问题
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "http://localhost:11434/api/embeddings",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"model": model, "prompt": text})
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"Ollama curl 失败：{result.stderr}")
            return []

        response = json.loads(result.stdout)
        return response.get("embedding", [])

    except Exception as e:
        logger.error(f"Ollama embedding 生成失败：{e}")
        return []


def inject_mock_emails_to_chromadb() -> bool:
    """
    将模拟邮件注入到 ChromaDB

    返回:
        bool: 是否成功
    """
    try:
        logger.info("开始注入模拟邮件到 ChromaDB...")

        # 先初始化 ChromaDB
        from src.email_agent.retriever.chroma_init import initialize_chromadb, get_chromadb_client
        initialize_chromadb()
        client = get_chromadb_client()
        collection = client.get_collection("email_embeddings")

        # 检查是否已存在数据
        count = collection.count()
        if count > 0:
            logger.info(f"ChromaDB 已有 {count} 个文档，跳过注入")
            return True

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for email in MOCK_EMAILS:
            # 组合文档文本
            doc_text = f"{email['subject']} {email['body']}"

            # 生成 embedding
            embedding = generate_embedding_with_ollama(doc_text)

            if embedding:
                ids.append(email["id"])
                embeddings.append(embedding)
                documents.append(doc_text)
                metadatas.append({
                    "from_address": email["from_address"],
                    "priority": email["priority"],
                    "category": email["category"],
                    "region": email["region"]
                })
                logger.info(f"已为邮件 {email['id']} 生成 embedding")
            else:
                logger.warning(f"邮件 {email['id']} embedding 生成失败，跳过")

        if ids:
            # 批量添加到 ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"成功注入 {len(ids)} 封模拟邮件到 ChromaDB")
            return True
        else:
            logger.warning("没有成功生成任何 embedding")
            return False

    except Exception as e:
        logger.error(f"ChromaDB 注入失败：{e}")
        return False


def inject_mock_emails_to_db(db_session) -> int:
    """
    将模拟邮件注入到 SQLite 数据库

    参数:
        db_session: SQLAlchemy 数据库会话

    返回:
        注入的邮件数量
    """
    from src.email_agent.storage.models import Email, Customer

    try:
        logger.info("开始注入模拟邮件到数据库...")

        # 检查是否已存在数据
        existing_count = db_session.query(Email).count()
        if existing_count > 0:
            logger.info(f"数据库已有 {existing_count} 封邮件，跳过注入")
            return 0

        # 创建示例客户
        customers = [
            Customer(name="Amazon CN", email="support@amazon.com", tier="A", region="CN"),
            Customer(name="GitHub Inc", email="billing@github.com", tier="A", region="US"),
            Customer(name="Company HR", email="hr@company.com", tier="A", region="CN"),
        ]

        for customer in customers:
            db_session.add(customer)
        db_session.commit()

        # 获取客户 ID 映射
        customer_map = {c.email: c.id for c in db_session.query(Customer).all()}

        # 创建邮件记录
        emails = []
        for email_data in MOCK_EMAILS:
            email = Email(
                id=email_data["id"],
                from_address=email_data["from_address"],
                subject=email_data["subject"],
                body=email_data["body"],
                priority=email_data["priority"],
                status="pending",
                region=email_data["region"],
                customer_id=customer_map.get(email_data["from_address"], 1)
            )
            emails.append(email)
            db_session.add(email)

        db_session.commit()
        logger.info(f"成功注入 {len(emails)} 封模拟邮件到数据库")
        return len(emails)

    except Exception as e:
        logger.error(f"数据库注入失败：{e}")
        db_session.rollback()
        return 0


def search_emails_in_chromadb(query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    在 ChromaDB 中搜索邮件

    参数:
        query_text: 查询文本
        n_results: 返回结果数量

    返回:
        搜索结果列表
    """
    try:
        # 先初始化 ChromaDB
        from src.email_agent.retriever.chroma_init import initialize_chromadb, get_chromadb_client
        initialize_chromadb()

        # 生成查询 embedding
        query_embedding = generate_embedding_with_ollama(query_text)

        if not query_embedding:
            logger.error("查询 embedding 生成失败")
            return []

        # 获取 ChromaDB 客户端和集合
        client = get_chromadb_client()
        collection = client.get_collection("email_embeddings")

        # 使用 embedding 查询（避免使用集合的默认 embedding 函数）
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        # 格式化结果
        formatted_results = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                result = {
                    "document": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0
                }
                formatted_results.append(result)

        return formatted_results

    except Exception as e:
        logger.error(f"ChromaDB 搜索失败：{e}")
        return []
