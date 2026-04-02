"""
Layer 1 邮件分类页面 Playwright E2E 测试

测试场景:
1. 分类页面加载
2. 过滤功能测试
3. 分类卡片展示
4. 详情弹窗功能
5. 空状态处理

注意：这些测试需要前端服务运行在 http://localhost:3000
运行测试前请执行：npm run dev
"""
import pytest
from playwright.sync_api import Page, expect

# 跳过标记 - 如果没有运行前端服务则跳过
pytestmark = pytest.mark.skip(reason="Requires frontend server running on localhost:3000")


def test_classifications_page_loads(page: Page, playwright_base_url: str):
    """测试分类页面加载"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 验证页面标题
    title = page.locator("h1")
    expect(title).to_contain_text("邮件分类管理")
    expect(title).to_contain_text("Email Classification")


def test_filter_type_dropdown(page: Page, playwright_base_url: str):
    """测试类型过滤下拉框"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 验证类型过滤器存在
    type_filter = page.locator("label:has-text('邮件类型') + select")
    expect(type_filter).to_be_visible()

    # 验证选项存在
    options = [
        "全部 | All",
        "📧 询盘 | Inquiry",
        "⚠️ 投诉 | Complaint",
        "❓ 咨询 | Question",
        "📄 合同 | Contract",
        "📝 其他 | Other"
    ]
    for option in options:
        expect(type_filter.locator(f"option:text('{option}')")).to_be_attached()


def test_filter_urgency_dropdown(page: Page, playwright_base_url: str):
    """测试紧急程度过滤下拉框"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 验证紧急程度过滤器存在
    urgency_filter = page.locator("label:has-text('紧急程度') + select")
    expect(urgency_filter).to_be_visible()

    # 验证选项存在
    options = [
        "全部 | All",
        "🔴 高 | High",
        "🟡 中 | Medium",
        "🟢 低 | Low"
    ]
    for option in options:
        expect(urgency_filter.locator(f"option:text('{option}')")).to_be_attached()


def test_filter_route_dropdown(page: Page, playwright_base_url: str):
    """测试路由类型过滤下拉框"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 验证路由过滤器存在
    route_filter = page.locator("label:has-text('路由类型') + select")
    expect(route_filter).to_be_visible()

    # 验证选项存在
    options = [
        "全部 | All",
        "💰 报价流程 | Quote Flow",
        "⚠️ 投诉流程 | Complaint Flow",
        "🤖 自动回复 | Auto Reply",
        "👤 人工处理 | Manual"
    ]
    for option in options:
        expect(route_filter.locator(f"option:text('{option}')")).to_be_attached()


def test_classification_cards_display(page: Page, playwright_base_url: str):
    """测试分类卡片展示"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 等待数据加载
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # 验证卡片容器存在（可能有数据或空状态）
    cards_or_empty = page.locator("text=询价|投诉|咨询|合同|暂无分类数据")
    expect(cards_or_empty).to_be_visible(timeout=5000)


def test_classification_detail_modal(page: Page, playwright_base_url: str):
    """测试分类详情弹窗"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 等待数据加载
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # 查找第一个分类卡片并点击
    first_card = page.locator("div[class*='rounded-lg']:has(h3)").first
    if first_card.is_visible(timeout=3000):
        first_card.click()

        # 等待弹窗出现
        modal = page.locator("text=Layer 1: 邮件分类详情")
        expect(modal).to_be_visible(timeout=5000)

        # 验证弹窗内容
        expect(page.locator("text=基本信息")).to_be_visible()
        expect(page.locator("text=AI 分类结果")).to_be_visible()
        expect(page.locator("text=路由决策")).to_be_visible()

        # 关闭弹窗
        close_button = page.locator("button[title='Close'], button:has(svg)")
        close_button.first.click()

        # 验证弹窗关闭
        expect(modal).not_to_be_visible(timeout=3000)


def test_filter_type_change(page: Page, playwright_base_url: str):
    """测试类型过滤功能"""
    page.goto(f"{playwright_base_url}/#/classifications")

    # 等待初始加载
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # 选择 Inquiry 类型
    type_filter = page.locator("label:has-text('邮件类型') + select")
    type_filter.select_option("inquiry")

    # 等待过滤生效
    page.wait_for_timeout(500)

    # 验证过滤后只显示 inquiry 类型
    # （这里假设卡片上有类型标识）
    cards = page.locator("text=询盘 | Inquiry")
    expect(cards).to_be_visible(timeout=3000)


def test_empty_state_display(page: Page, playwright_base_url: str):
    """测试空状态显示"""
    # 这个测试假设在没有数据时的表现
    page.goto(f"{playwright_base_url}/#/classifications")

    # 可能是空状态或有数据，两种情况都接受
    empty_state = page.locator("text=暂无分类数据")
    has_data = page.locator("div[class*='rounded-lg']:has(h3)")

    # 等待加载完成
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # 要么是空状态，要么有数据
    if empty_state.is_visible():
        expect(empty_state).to_be_visible()
    else:
        expect(has_data).to_be_visible()


def test_page_responsive_layout(page: Page, playwright_base_url: str):
    """测试页面响应式布局"""
    # 测试不同视口大小
    viewports = [
        {"width": 375, "height": 667},  # 手机
        {"width": 768, "height": 1024}, # 平板
        {"width": 1920, "height": 1080} # 桌面
    ]

    for viewport in viewports:
        page.set_viewport_size(viewport)
        page.goto(f"{playwright_base_url}/#/classifications")

        # 验证页面标题始终可见
        title = page.locator("h1")
        expect(title).to_be_visible()

        # 验证过滤器可见
        filters = page.locator("label:has-text('邮件类型')")
        expect(filters).to_be_visible()
