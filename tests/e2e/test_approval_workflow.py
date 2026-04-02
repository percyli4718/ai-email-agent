#!/usr/bin/env python3
"""
审批工作流 Playwright E2E 测试

测试场景:
1. 创建审批请求测试
2. 审批列表加载测试
3. 批准操作测试
4. 拒绝操作测试
5. 通知推送测试
6. 审批状态变更测试

使用工具:
- Playwright: 浏览器自动化测试
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, expect, Page, Browser, BrowserContext

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ApprovalWorkflowTester:
    """审批工作流测试类"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "http://localhost:5173"
        self.api_url = "http://localhost:8000"
        self.screenshot_dir = Path(__file__).parent / "screenshots" / "approvals"
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
        print(f"📸 截图目录：{self.screenshot_dir}")

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
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"      {status} {test_name}")
        if details and not passed:
            print(f"           {details}")

    async def take_screenshot(self, name: str):
        """截取屏幕"""
        path = self.screenshot_dir / f"{name}.png"
        await self.page.screenshot(path=str(path))
        return path

    # =========================================================================
    # 测试 1: 创建审批请求
    # =========================================================================

    async def test_create_approval_request(self):
        """测试创建审批请求 API"""
        print("\n" + "=" * 60)
        print("测试 1: 创建审批请求")
        print("=" * 60)

        try:
            response = await self.page.request.post(
                f"{self.api_url}/api/approvals",
                data={
                    "email_id": "email_test_001",
                    "requester": "price_agent",
                    "request_type": "high_amount",
                    "reason": "Quote amount exceeds threshold ($50,000)",
                    "amount": 50000,
                    "currency": "USD",
                    "details": {"quote_id": "QT-TEST-001", "threshold": 10000}
                }
            )

            if response.ok:
                data = await response.json()
                self.log_result(
                    "创建审批请求 API",
                    True,
                    f"请求 ID: {data.get('id')}"
                )
                return data.get('id')
            else:
                error = await response.text()
                self.log_result(
                    "创建审批请求 API",
                    False,
                    f"Status: {response.status}, Error: {error}"
                )
                return None

        except Exception as e:
            self.log_result("创建审批请求 API", False, str(e))
            return None

    # =========================================================================
    # 测试 2: 审批列表加载
    # =========================================================================

    async def test_approval_list_load(self):
        """测试审批列表加载"""
        print("\n" + "=" * 60)
        print("测试 2: 审批列表加载")
        print("=" * 60)

        try:
            # 先通过 API 获取列表
            response = await self.page.request.get(f"{self.api_url}/api/approvals?status=pending&limit=10")
            
            if response.ok:
                data = await response.json()
                requests = data.get('requests', [])
                self.log_result(
                    "审批列表 API",
                    True,
                    f"找到 {len(requests)} 条待审批记录"
                )

                # 访问前端首页
                await self.page.goto(self.base_url, wait_until="networkidle")
                await self.page.wait_for_timeout(3000)
                
                # 点击审批 Tab 按钮（标签是 "✅ 审批 | Approvals"）
                try:
                    approvals_tab = self.page.locator('button:has-text("审批"), button:has-text("Approvals")').first
                    await approvals_tab.click()
                    await self.page.wait_for_timeout(3000)
                    await self.take_screenshot("approvals_page")

                    # 检查页面是否有审批相关内容
                    page_text = await self.page.text_content("body")
                    
                    # 检查是否有"审批"或"Approvals"文本
                    has_approvals_text = "审批" in page_text or "Approvals" in page_text
                    self.log_result("审批页面内容存在", has_approvals_text)

                    # 检查过滤器标签
                    has_filter = await self.page.is_visible("text=待处理", timeout=2000) or \
                                 await self.page.is_visible("text=Pending", timeout=2000)
                    self.log_result("过滤器标签显示", has_filter)

                    return True
                except Exception as e:
                    self.log_result("点击审批 Tab", False, str(e))
                    await self.take_screenshot("approvals_tab_error")
                    return False
            else:
                error = await response.text()
                self.log_result("审批列表 API", False, f"Status: {response.status}")
                return False

        except Exception as e:
            self.log_result("审批列表加载", False, str(e))
            await self.take_screenshot("approvals_list_error")
            return False

    # =========================================================================
    # 测试 3: 批准操作测试
    # =========================================================================

    async def test_approve_action(self):
        """测试批准操作"""
        print("\n" + "=" * 60)
        print("测试 3: 批准操作")
        print("=" * 60)

        try:
            # 获取待审批列表
            response = await self.page.request.get(f"{self.api_url}/api/approvals?status=pending&limit=1")
            data = await response.json()
            requests = data.get('requests', [])

            if not requests:
                # 创建一个测试请求
                create_response = await self.page.request.post(
                    f"{self.api_url}/api/approvals",
                    data={
                        "email_id": "email_approve_test",
                        "requester": "test_agent",
                        "request_type": "high_amount",
                        "reason": "Test approval",
                        "amount": 10000,
                        "currency": "USD"
                    }
                )
                if create_response.ok:
                    create_data = await create_response.json()
                    requests = [create_data]

            if requests:
                request_id = requests[0]['id']
                
                # 调用批准 API
                approve_response = await self.page.request.post(
                    f"{self.api_url}/api/approvals/{request_id}/approve",
                    data={
                        "reviewer": "test_admin",
                        "comments": "测试批准 | Test approval"
                    }
                )

                if approve_response.ok:
                    self.log_result("批准 API 调用", True, f"请求 #{request_id} 已批准")
                    
                    # 验证状态变更
                    status_response = await self.page.request.get(
                        f"{self.api_url}/api/approvals/{request_id}"
                    )
                    status_data = await status_response.json()
                    
                    status_correct = status_data.get('status') == 'approved'
                    self.log_result(
                        "审批状态变更为 approved",
                        status_correct,
                        f"当前状态：{status_data.get('status')}"
                    )

                    await self.take_screenshot("approve_success")
                    return True
                else:
                    error = await approve_response.text()
                    self.log_result("批准 API 调用", False, error)
                    return False
            else:
                self.log_result("批准操作", False, "没有待审批请求")
                return False

        except Exception as e:
            self.log_result("批准操作", False, str(e))
            await self.take_screenshot("approve_error")
            return False

    # =========================================================================
    # 测试 4: 拒绝操作测试
    # =========================================================================

    async def test_reject_action(self):
        """测试拒绝操作"""
        print("\n" + "=" * 60)
        print("测试 4: 拒绝操作")
        print("=" * 60)

        try:
            # 创建一个测试请求用于拒绝
            create_response = await self.page.request.post(
                f"{self.api_url}/api/approvals",
                data={
                    "email_id": "email_reject_test",
                    "requester": "test_agent",
                    "request_type": "special_terms",
                    "reason": "Test rejection",
                    "amount": 5000,
                    "currency": "USD"
                }
            )

            if not create_response.ok:
                self.log_result("创建测试请求", False, "无法创建测试请求")
                return False

            create_data = await create_response.json()
            request_id = create_data['id']

            # 调用拒绝 API
            reject_response = await self.page.request.post(
                f"{self.api_url}/api/approvals/{request_id}/reject",
                data={
                    "reviewer": "test_admin",
                    "comments": "测试拒绝 - 不符合要求 | Test rejection"
                }
            )

            if reject_response.ok:
                self.log_result("拒绝 API 调用", True, f"请求 #{request_id} 已拒绝")
                
                # 验证状态变更
                status_response = await self.page.request.get(
                    f"{self.api_url}/api/approvals/{request_id}"
                )
                status_data = await status_response.json()
                
                status_correct = status_data.get('status') == 'rejected'
                self.log_result(
                    "审批状态变更为 rejected",
                    status_correct,
                    f"当前状态：{status_data.get('status')}"
                )

                # 验证审批人信息
                reviewer_correct = status_data.get('reviewer') == 'test_admin'
                self.log_result(
                    "审批人信息记录",
                    reviewer_correct,
                    f"审批人：{status_data.get('reviewer')}"
                )

                await self.take_screenshot("reject_success")
                return True
            else:
                error = await reject_response.text()
                self.log_result("拒绝 API 调用", False, error)
                return False

        except Exception as e:
            self.log_result("拒绝操作", False, str(e))
            await self.take_screenshot("reject_error")
            return False

    # =========================================================================
    # 测试 5: 通知推送测试
    # =========================================================================

    async def test_notification_push(self):
        """测试通知推送"""
        print("\n" + "=" * 60)
        print("测试 5: 通知推送")
        print("=" * 60)

        try:
            # 创建审批请求应该会触发通知
            response = await self.page.request.post(
                f"{self.api_url}/api/approvals",
                data={
                    "email_id": "email_notify_test",
                    "requester": "test_agent",
                    "request_type": "risk_control",
                    "reason": "Test notification",
                    "amount": 20000,
                    "currency": "USD"
                }
            )

            if response.ok:
                # 检查通知列表
                notify_response = await self.page.request.get(
                    f"{self.api_url}/api/notifications?limit=10"
                )
                
                if notify_response.ok:
                    notify_data = await notify_response.json()
                    notifications = notify_data.get('notifications', [])
                    
                    # 查找审批相关的通知
                    approval_notifications = [
                        n for n in notifications 
                        if n.get('type') == 'approval_request'
                    ]

                    self.log_result(
                        "审批通知创建",
                        len(approval_notifications) > 0,
                        f"找到 {len(approval_notifications)} 条审批通知"
                    )

                    # 截图
                    await self.take_screenshot("notification_list")
                    return True
                else:
                    self.log_result("获取通知列表", False, f"Status: {notify_response.status}")
                    return False
            else:
                self.log_result("创建审批请求", False, "无法创建请求")
                return False

        except Exception as e:
            self.log_result("通知推送", False, str(e))
            await self.take_screenshot("notification_error")
            return False

    # =========================================================================
    # 测试 6: 审批状态变更测试
    # =========================================================================

    async def test_status_transition(self):
        """测试审批状态变更流程"""
        print("\n" + "=" * 60)
        print("测试 6: 审批状态变更测试")
        print("=" * 60)

        try:
            # 创建请求 -> pending
            create_response = await self.page.request.post(
                f"{self.api_url}/api/approvals",
                data={
                    "email_id": "email_status_test",
                    "requester": "test_agent",
                    "request_type": "new_customer",
                    "reason": "Test status transition",
                    "amount": 8000,
                    "currency": "USD"
                }
            )
            
            if not create_response.ok:
                self.log_result("创建状态测试请求", False)
                return False

            create_data = await create_response.json()
            request_id = create_data['id']
            
            # 验证初始状态为 pending
            initial_status = create_data.get('status')
            self.log_result(
                "初始状态为 pending",
                initial_status == 'pending',
                f"实际状态：{initial_status}"
            )

            # 批准 -> approved
            approve_response = await self.page.request.post(
                f"{self.api_url}/api/approvals/{request_id}/approve",
                data={
                    "reviewer": "admin",
                    "comments": "Approved for testing"
                }
            )

            if approve_response.ok:
                # 获取最新状态
                status_response = await self.page.request.get(
                    f"{self.api_url}/api/approvals/{request_id}"
                )
                status_data = await status_response.json()
                
                # 验证已批准
                self.log_result(
                    "状态变更：pending -> approved",
                    status_data.get('status') == 'approved',
                    f"当前状态：{status_data.get('status')}"
                )

                # 验证 reviewed_at 已设置
                has_reviewed_at = status_data.get('reviewed_at') is not None
                self.log_result(
                    "审批时间 recorded_at 已设置",
                    has_reviewed_at,
                    f"审批时间：{status_data.get('reviewed_at')}"
                )

                # 验证评论已记录
                has_comments = status_data.get('comments') is not None
                self.log_result(
                    "审批意见已记录",
                    has_comments,
                    f"意见：{status_data.get('comments')}"
                )

                await self.take_screenshot("status_transition")
                return True
            else:
                self.log_result("批准操作", False, "无法批准请求")
                return False

        except Exception as e:
            self.log_result("状态变更测试", False, str(e))
            await self.take_screenshot("status_error")
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
╔════════════════════════════════════════════════════════════╗
║           审批工作流 Playwright 测试报告                    ║
║              Approval Workflow Test Report                  ║
╠════════════════════════════════════════════════════════════╣
║ 总计 (Total): {total:<39} ║
║ 通过 (Passed): {passed:<39} ║
║ 失败 (Failed): {failed:<39} ║
║ 通过率 (Pass Rate): {pass_rate:.1f}%{'':27} ║
╚════════════════════════════════════════════════════════════╝

详细结果 (Detailed Results):
{'─' * 60}
"""
        for r in self.test_results:
            status = "✅" if r['passed'] else "❌"
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
        print("\n" + "█" * 60)
        print("█  审批工作流 Playwright E2E 测试")
        print("█  Approval Workflow Playwright E2E Tests")
        print("█" * 60)

        await self.setup()

        try:
            # 检查后端是否运行
            try:
                health = await self.page.request.get(f"{self.api_url}/api/health")
                if health.status != 200:
                    print(f"\n⚠️  警告：后端 API 健康检查失败 (status: {health.status})")
                    print(f"   请确保后端服务在 {self.api_url} 运行")
            except Exception:
                print(f"\n❌ 错误：无法连接到后端 API ({self.api_url})")
                print("   请先启动后端服务")
                return self.generate_report()

            # 运行所有测试
            await self.test_create_approval_request()
            await self.test_approval_list_load()
            await self.test_approve_action()
            await self.test_reject_action()
            await self.test_notification_push()
            await self.test_status_transition()

        finally:
            await self.teardown()

        # 生成并打印报告
        report = self.generate_report()
        print(report)
        
        # 保存报告
        report_path = self.screenshot_dir / "test_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 测试报告已保存：{report_path}")
        
        return report


async def main():
    """主函数"""
    tester = ApprovalWorkflowTester(headless=True)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
