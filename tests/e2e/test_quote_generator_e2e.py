#!/usr/bin/env python3
"""
报价生成器 Playwright E2E 测试

测试场景:
1. 报价生成 API 测试
2. 报价列表加载测试
3. 报价详情查看测试
4. 报价状态变更测试
5. 报价删除测试
6. 前端报价页面交互测试

使用工具:
- Playwright: 浏览器自动化测试
- Chrome DevTools MCP: 浏览器调试
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, expect, Page, Browser, BrowserContext

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class QuoteGeneratorTester:
    """报价生成器测试类"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "http://localhost:5173"
        self.api_url = "http://localhost:8000"
        self.screenshot_dir = Path(__file__).parent / "screenshots" / "quote_generator"
        self.test_results = []

    async def setup(self):
        """设置测试环境"""
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = await async_playwright().start()
        self.browser: Browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context: BrowserContext = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        self.page: Page = await self.context.new_page()
        print(f"截图目录：{self.screenshot_dir}")

    async def teardown(self):
        """清理测试环境"""
        await self.browser.close()
        await self.playwright.stop()

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "PASS" if passed else "FAIL"
        print(f"      {status} {test_name}")
        if details and not passed:
            print(f"           {details}")

    async def take_screenshot(self, name: str):
        """截取屏幕"""
        path = self.screenshot_dir / f"{name}.png"
        await self.page.screenshot(path=str(path))
        return path

    # =========================================================================
    # 测试 1: 创建报价单 (API)
    # =========================================================================

    async def test_create_quote_api(self):
        """测试创建报价单 API"""
        print("\n" + "=" * 60)
        print("测试 1: 创建报价单 API")
        print("=" * 60)

        try:
            # 先创建一封测试邮件
            email_response = await self.page.request.post(
                f"{self.api_url}/api/emails/generate",
                data={"count": 1, "auto_process": False}
            )

            if not email_response.ok:
                self.log_result("创建测试邮件", False, f"Status: {email_response.status}")
                return None

            email_data = await email_response.json()
            email_id = email_data["generated_emails"][0]["id"]

            # 调用报价生成 API
            quote_response = await self.page.request.post(
                f"{self.api_url}/api/quotes/generate",
                data={"email_id": email_id}
            )

            if quote_response.ok:
                data = await quote_response.json()
                self.log_result(
                    "报价生成 API",
                    True,
                    f"报价 ID: {data.get('quote', {}).get('quote_id')}"
                )
                return data.get('quote', {}).get('quote_id')
            else:
                error = await quote_response.text()
                self.log_result(
                    "报价生成 API",
                    False,
                    f"Status: {quote_response.status}, Error: {error}"
                )
                return None

        except Exception as e:
            self.log_result("报价生成 API", False, str(e))
            await self.take_screenshot("create_quote_error")
            return None

    # =========================================================================
    # 测试 2: 报价列表加载
    # =========================================================================

    async def test_quote_list_load(self):
        """测试报价列表加载"""
        print("\n" + "=" * 60)
        print("测试 2: 报价列表加载")
        print("=" * 60)

        try:
            # 先通过 API 获取列表
            response = await self.page.request.get(f"{self.api_url}/api/quotes?limit=10")

            if response.ok:
                data = await response.json()
                quotes = data.get('quotes', [])
                self.log_result(
                    "报价列表 API",
                    True,
                    f"找到 {len(quotes)} 条报价记录"
                )

                # 验证响应结构
                has_quotes_field = 'quotes' in data
                has_total_field = 'total' in data
                self.log_result("响应结构验证", has_quotes_field and has_total_field)

                return True
            else:
                error = await response.text()
                self.log_result("报价列表 API", False, f"Status: {response.status}")
                return False

        except Exception as e:
            self.log_result("报价列表加载", False, str(e))
            await self.take_screenshot("quote_list_error")
            return False

    # =========================================================================
    # 测试 3: 报价详情查看
    # =========================================================================

    async def test_quote_detail(self):
        """测试报价详情查看"""
        print("\n" + "=" * 60)
        print("测试 3: 报价详情查看")
        print("=" * 60)

        try:
            # 获取报价列表
            response = await self.page.request.get(f"{self.api_url}/api/quotes?limit=1")
            data = await response.json()
            quotes = data.get('quotes', [])

            if not quotes:
                # 如果没有报价，尝试创建一个
                quote_id = await self.test_create_quote_api()
                if not quote_id:
                    self.log_result("报价详情查看", False, "无法创建测试报价")
                    return False
                quote = {"quote_id": quote_id}
            else:
                quote = quotes[0]

            # 获取报价详情
            detail_response = await self.page.request.get(
                f"{self.api_url}/api/quotes/{quote['quote_id']}"
            )

            if detail_response.ok:
                detail_data = await detail_response.json()

                # 验证必需字段
                required_fields = ['quote_id', 'customer_email', 'total_amount', 'items']
                missing_fields = [f for f in required_fields if f not in detail_data]

                self.log_result(
                    "报价详情字段验证",
                    len(missing_fields) == 0,
                    f"缺失字段：{missing_fields}" if missing_fields else "所有必需字段存在"
                )

                # 验证报价项目
                has_items = len(detail_data.get('items', [])) > 0
                self.log_result("报价项目存在", has_items)

                await self.take_screenshot("quote_detail")
                return True
            else:
                error = await detail_response.text()
                self.log_result("报价详情 API", False, f"Status: {detail_response.status}")
                return False

        except Exception as e:
            self.log_result("报价详情查看", False, str(e))
            await self.take_screenshot("quote_detail_error")
            return False

    # =========================================================================
    # 测试 4: 报价状态变更
    # =========================================================================

    async def test_quote_status_update(self):
        """测试报价状态变更"""
        print("\n" + "=" * 60)
        print("测试 4: 报价状态变更")
        print("=" * 60)

        try:
            # 创建测试报价
            quote_id = await self.test_create_quote_api()
            if not quote_id:
                self.log_result("报价状态变更", False, "无法创建测试报价")
                return False

            # 测试状态变更：draft -> sent
            sent_response = await self.page.request.post(
                f"{self.api_url}/api/quotes/{quote_id}/status?status=sent"
            )

            if sent_response.ok:
                self.log_result("状态变更：draft -> sent", True)

                # 验证状态已更新
                detail_response = await self.page.request.get(
                    f"{self.api_url}/api/quotes/{quote_id}"
                )
                detail_data = await detail_response.json()

                status_correct = detail_data.get('status') == 'sent'
                self.log_result(
                    "状态验证",
                    status_correct,
                    f"当前状态：{detail_data.get('status')}"
                )

                # 测试状态变更：sent -> accepted
                accepted_response = await self.page.request.post(
                    f"{self.api_url}/api/quotes/{quote_id}/status?status=accepted"
                )

                if accepted_response.ok:
                    self.log_result("状态变更：sent -> accepted", True)

                    final_response = await self.page.request.get(
                        f"{self.api_url}/api/quotes/{quote_id}"
                    )
                    final_data = await final_response.json()

                    final_status_correct = final_data.get('status') == 'accepted'
                    self.log_result(
                        "最终状态验证",
                        final_status_correct,
                        f"最终状态：{final_data.get('status')}"
                    )

                    await self.take_screenshot("quote_status_update")
                    return True
                else:
                    self.log_result("状态变更：sent -> accepted", False)
                    return False
            else:
                error = await sent_response.text()
                self.log_result("状态变更 API", False, error)
                return False

        except Exception as e:
            self.log_result("报价状态变更", False, str(e))
            await self.take_screenshot("status_update_error")
            return False

    # =========================================================================
    # 测试 5: 报价删除
    # =========================================================================

    async def test_quote_delete(self):
        """测试报价删除"""
        print("\n" + "=" * 60)
        print("测试 5: 报价删除")
        print("=" * 60)

        try:
            # 创建测试报价
            quote_id = await self.test_create_quote_api()
            if not quote_id:
                self.log_result("报价删除", False, "无法创建测试报价")
                return False

            # 删除报价
            delete_response = await self.page.request.delete(
                f"{self.api_url}/api/quotes/{quote_id}"
            )

            if delete_response.ok:
                self.log_result("报价删除 API", True, f"报价 {quote_id} 已删除")

                # 验证报价已不存在
                get_response = await self.page.request.get(
                    f"{self.api_url}/api/quotes/{quote_id}"
                )

                not_found = get_response.status == 404
                self.log_result(
                    "验证报价已删除",
                    not_found,
                    f"GET 返回状态：{get_response.status}"
                )

                await self.take_screenshot("quote_delete")
                return True
            else:
                error = await delete_response.text()
                self.log_result("报价删除 API", False, error)
                return False

        except Exception as e:
            self.log_result("报价删除", False, str(e))
            await self.take_screenshot("quote_delete_error")
            return False

    # =========================================================================
    # 测试 6: 报价 Schema 验证
    # =========================================================================

    async def test_quote_schema_validation(self):
        """测试报价 Schema 验证"""
        print("\n" + "=" * 60)
        print("测试 6: 报价 Schema 验证")
        print("=" * 60)

        try:
            # 创建测试报价
            quote_id = await self.test_create_quote_api()
            if not quote_id:
                return False

            # 获取报价详情
            response = await self.page.request.get(
                f"{self.api_url}/api/quotes/{quote_id}"
            )
            data = await response.json()

            # 验证报价项目 Schema
            items = data.get('items', [])
            if items:
                item = items[0]
                required_item_fields = [
                    'product_name', 'quantity', 'unit_price',
                    'currency', 'incoterm', 'lead_time_days', 'subtotal'
                ]
                missing_item_fields = [f for f in required_item_fields if f not in item]

                self.log_result(
                    "报价项目 Schema 验证",
                    len(missing_item_fields) == 0,
                    f"缺失字段：{missing_item_fields}" if missing_item_fields else "所有必需字段存在"
                )

            # 验证报价单 Schema
            required_quote_fields = [
                'quote_id', 'customer_email', 'total_amount',
                'valid_until', 'shipping_port', 'payment_terms', 'status'
            ]
            missing_quote_fields = [f for f in required_quote_fields if f not in data]

            self.log_result(
                "报价单 Schema 验证",
                len(missing_quote_fields) == 0,
                f"缺失字段：{missing_quote_fields}" if missing_quote_fields else "所有必需字段存在"
            )

            return True

        except Exception as e:
            self.log_result("报价 Schema 验证", False, str(e))
            return False

    # =========================================================================
    # 测试 7: 前端报价页面加载
    # =========================================================================

    async def test_frontend_quote_page_load(self):
        """测试前端报价页面加载"""
        print("\n" + "=" * 60)
        print("测试 7: 前端报价页面加载")
        print("=" * 60)

        try:
            # 访问前端报价页面
            await self.page.goto(f"{self.base_url}/quotes", wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 检查页面标题
            title_visible = await self.page.is_visible("text=报价") or await self.page.is_visible("text=Quote")
            self.log_result("报价页面标题显示", title_visible)

            # 检查报价列表是否渲染
            await self.take_screenshot("frontend_quotes_page")

            # 检查表格或卡片容器
            container_exists = (
                await self.page.is_visible("table") or
                await self.page.is_visible('[class*="Quote"]') or
                await self.page.is_visible('[data-testid*="quote"]')
            )
            self.log_result("报价列表容器渲染", container_exists)

            return True

        except Exception as e:
            self.log_result("前端报价页面加载", False, str(e))
            await self.take_screenshot("frontend_page_error")
            return False

    # =========================================================================
    # 生成测试报告
    # =========================================================================

    def generate_report(self) -> str:
        """生成测试报告"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        report = f"""
+{'-' * 58}+
|           报价生成器 Playwright 测试报告                    |
|              Quote Generator Test Report                    |
+{'-' * 58}+
| 总计 (Total): {total:<39} |
| 通过 (Passed): {passed:<39} |
| 失败 (Failed): {failed:<39} |
| 通过率 (Pass Rate): {pass_rate:.1f}%{'':27} |
+{'-' * 58}+

详细结果 (Detailed Results):
{'-' * 58}
"""
        for r in self.test_results:
            status = "+" if r['passed'] else "-"
            report += f"{status} {r['name']}\n"
            if r['details']:
                report += f"   {r['details']}\n"

        report += f"\n测试时间：{datetime.now().isoformat()}\n"
        report += f"截图目录：{self.screenshot_dir}\n"

        return report

    # =========================================================================
    # 运行所有测试
    # =========================================================================

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("  报价生成器 Playwright E2E 测试")
        print("  Quote Generator Playwright E2E Tests")
        print("=" * 60)

        await self.setup()

        try:
            # 检查后端是否运行
            try:
                health = await self.page.request.get(f"{self.api_url}/api/health")
                if health.status != 200:
                    print(f"\n警告：后端 API 健康检查失败 (status: {health.status})")
                    print(f"   请确保后端服务在 {self.api_url} 运行")
            except Exception:
                print(f"\n错误：无法连接到后端 API ({self.api_url})")
                print("   请先启动后端服务")
                return self.generate_report()

            # 运行所有测试
            await self.test_create_quote_api()
            await self.test_quote_list_load()
            await self.test_quote_detail()
            await self.test_quote_status_update()
            await self.test_quote_delete()
            await self.test_quote_schema_validation()
            await self.test_frontend_quote_page_load()

        finally:
            await self.teardown()

        # 生成并打印报告
        report = self.generate_report()
        print(report)

        # 保存报告
        report_path = self.screenshot_dir / "test_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n测试报告已保存：{report_path}")

        return report


async def main():
    """主函数"""
    tester = QuoteGeneratorTester(headless=True)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
