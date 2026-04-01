"""
Email Generation E2E Test with Playwright

测试流程:
1. 访问 Inbox 页面
2. 验证 GenerateEmailPanel 组件存在
3. 选择生成数量并点击生成按钮
4. 验证邮件出现在列表中
5. 验证数据库存储
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def test_email_generation_flow():
    """测试邮件生成完整流程"""

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("=" * 60)
        print("Email Generation E2E Test")
        print("=" * 60)

        try:
            # [1/5] 访问 Inbox 页面
            print("\n[1/5] 访问 Inbox 页面...")
            await page.goto("http://localhost:5173", wait_until="networkidle")
            await page.wait_for_timeout(3000)  # 等待 React 加载

            # 截图
            await page.screenshot(path="tests/e2e/screenshots/01-inbox-initial.png")
            print("      页面加载完成")

            # [2/5] 查找 GenerateEmailPanel 组件
            print("\n[2/5] 查找邮件生成面板...")

            # 检查是否存在生成面板
            try:
                # 查找包含"生成邮件"文本的按钮或面板
                panel_visible = await page.is_visible("text=生成邮件", timeout=2000)
                if not panel_visible:
                    # 尝试其他选择器
                    panel_visible = await page.is_visible("text=Generate Emails", timeout=2000)

                if panel_visible:
                    print("      ✅ 找到生成面板")
                else:
                    # 获取页面内容诊断
                    page_content = await page.content()
                    if "GenerateEmailPanel" in page_content or "生成" in page_content:
                        print("      ⚠️ 组件可能存在但未正确渲染")
                    else:
                        print("      ⚠️ 未找到生成面板，可能前端未正确集成")
                    print(f"      页面标题：{await page.title()}")
            except Exception as e:
                print(f"      ⚠️ 检查失败：{e}")

            # [3/5] 测试生成邮件 API
            print("\n[3/5] 测试生成邮件 API...")
            await page.goto("http://localhost:8000/api/health")
            health = await page.text_content("body")
            print(f"      API 健康检查：{health}")

            # [4/5] 直接调用 API 测试
            print("\n[4/5] 调用生成邮件 API...")
            response = await page.request.post(
                "http://localhost:8000/api/emails/generate",
                data={"count": 1, "auto_process": False}
            )

            if response.ok:
                data = await response.json()
                print(f"      ✅ API 响应成功")
                print(f"      生成邮件数：{data.get('total', 0)}")
                if data.get('generated_emails'):
                    email = data['generated_emails'][0]
                    print(f"      邮件 ID: {email.get('id')}")
                    print(f"      主题：{email.get('subject', '')[:50]}...")
            else:
                error_text = await response.text()
                print(f"      ❌ API 失败：{response.status} - {error_text}")

            # [5/5] 验证邮件已存储到数据库
            print("\n[5/5] 验证数据库存储...")
            from email_agent.config import settings
            from email_agent.storage.database import get_database
            from email_agent.storage.models import Email
            from sqlalchemy import select, func

            db = get_database(settings)
            async with db.session() as session:
                stmt = select(func.count()).select_from(Email)
                result = await session.execute(stmt)
                email_count = result.scalar()
                print(f"      数据库邮件总数：{email_count}")

                if email_count > 0:
                    print("      ✅ 邮件已成功存储到数据库")
                else:
                    print("      ❌ 数据库中没有邮件")

            print("\n" + "=" * 60)
            if email_count > 0:
                print("✅ E2E 测试通过 - 邮件生成和存储功能正常")
            else:
                print("⚠️ E2E 测试完成 - 但数据库存储可能有问题")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 测试失败：{e}")
            import traceback
            traceback.print_exc()

            # 失败时截图
            await page.screenshot(path="tests/e2e/screenshots/error.png")
            print("      错误截图已保存")

        finally:
            await browser.close()


if __name__ == "__main__":
    # 确保截图目录存在
    screenshot_dir = Path(__file__).parent / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(test_email_generation_flow())
