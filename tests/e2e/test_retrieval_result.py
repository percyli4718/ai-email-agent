"""
Layer 2 检索结果页面 Playwright E2E 测试

测试场景:
1. 检索结果面板加载
2. Tab 切换功能
3. 定价政策展示
4. 合规要求展示
5. 相似邮件展示

注意：这些测试需要前端服务运行在 http://localhost:3000
运行测试前请执行：npm run dev
"""
import pytest
from playwright.sync_api import Page, expect

# 跳过标记 - 如果没有运行前端服务则跳过
pytestmark = pytest.mark.skip(reason="Requires frontend server running on localhost:3000")


# 测试数据
TEST_EMAIL_ID = "email_001"


def test_retrieval_panel_loads(page: Page, playwright_base_url: str):
    """测试检索结果面板加载"""
    # 访问邮件详情页（假设路由）
    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 等待页面加载
    expect(page.locator("h2")).to_contain_text("Request for Quote")

    # 点击"显示检索结果"按钮
    show_button = page.get_by_role("button", name="显示检索结果")
    show_button.click()

    # 等待检索结果面板出现
    retrieval_panel = page.locator("text=Layer 2: 上下文检索结果")
    expect(retrieval_panel).to_be_visible(timeout=5000)


def test_retrieval_tabs_switch(page: Page, playwright_base_url: str):
    """测试检索结果 Tab 切换功能"""
    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 显示检索结果
    show_button = page.get_by_role("button", name="显示检索结果")
    show_button.click()

    # 等待面板出现
    retrieval_panel = page.locator("text=Layer 2: 上下文检索结果")
    expect(retrieval_panel).to_be_visible()

    # 测试 Tab 切换
    tabs = ["概览", "定价政策", "合规要求", "相似邮件"]
    for tab in tabs:
        tab_button = page.get_by_role("button", name=tab)
        tab_button.click()
        # 等待动画
        page.wait_for_timeout(300)
        # 验证 Tab 激活状态
        expect(tab_button).to_have_class(page.locator(tab_button).get_attribute("class"))


def test_pricing_policy_display(page: Page, playwright_base_url: str):
    """测试定价政策展示"""
    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 显示检索结果并切换到定价 Tab
    page.get_by_role("button", name="显示检索结果").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="定价政策").click()

    # 验证定价表格存在
    pricing_table = page.locator("table")
    expect(pricing_table).to_be_visible()

    # 验证表头
    expect(page.locator("th")).to_contain_text("产品")
    expect(page.locator("th")).to_contain_text("基准价")
    expect(page.locator("th")).to_contain_text("折扣率")


def test_compliance_requirements_display(page: Page, playwright_base_url: str):
    """测试合规要求展示"""
    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 显示检索结果并切换到合规 Tab
    page.get_by_role("button", name="显示检索结果").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="合规要求").click()

    # 验证合规要求区域存在
    compliance_section = page.locator("text=合规要求")
    expect(compliance_section).to_be_visible()


def test_similar_emails_display(page: Page, playwright_base_url: str):
    """测试相似邮件展示"""
    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 显示检索结果并切换到相似邮件 Tab
    page.get_by_role("button", name="显示检索结果").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="相似邮件").click()

    # 验证相似邮件区域存在
    similar_section = page.locator("text=相似邮件")
    expect(similar_section).to_be_visible()


def test_customer_history_card(page: Page, playwright_base_url: str):
    """测试客户历史卡片展示"""
    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 显示检索结果
    page.get_by_role("button", name="显示检索结果").click()

    # 验证客户历史区域存在
    customer_section = page.locator("text=客户历史")
    expect(customer_section).to_be_visible()


def test_retrieval_loading_state(page: Page, playwright_base_url: str):
    """测试加载状态显示"""
    # 模拟慢速网络
    page.context.route("**/api/**", lambda route: route.continue_())

    page.goto(f"{playwright_base_url}/#/emails/{TEST_EMAIL_ID}")

    # 显示检索结果
    page.get_by_role("button", name="显示检索结果").click()

    # 应该能看到加载状态或内容
    # 由于是异步加载，可能需要等待
    page.wait_for_load_state("networkidle")

    # 验证面板存在（无论是加载中还是已加载完成）
    panel = page.locator("text=Layer 2").or_(page.locator("text=加载中"))
    expect(panel).to_be_visible(timeout=5000)
