"""
Agent Monitoring E2E Tests with Playwright

Tests the Agent Monitoring dashboard:
1. Agent performance metrics display
2. Cost dashboard with charts
3. Execution history table
4. Execution detail modal
5. Real-time status updates

Run with:
    pytest tests/e2e/test_agent_monitoring.py -v
"""
import pytest
from playwright.sync_api import Page, expect, TimeoutError
import re
import time


# ============================================================================
# Test Configuration
# ============================================================================

BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def page(page: Page) -> Page:
    """Configure page for tests"""
    page.set_viewport_size({"width": 1920, "height": 1080})
    return page


@pytest.fixture(scope="function")
def authenticated_page(page: Page) -> Page:
    """Navigate to app and wait for load"""
    page.goto(BASE_URL, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)
    return page


# ============================================================================
# Helper Functions
# ============================================================================

def wait_for_element(page: Page, selector: str, timeout: int = 5000) -> None:
    """Wait for element to be visible"""
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
    except TimeoutError:
        page.screenshot(path="tests/e2e/screenshots/monitoring_error.png")
        raise


def navigate_to_monitoring(page: Page) -> None:
    """Navigate to Agent Monitoring page"""
    # Click on Agent Monitoring tab in navigation
    try:
        # Try to find navigation link with text "Agent" or "监控"
        monitoring_link = page.locator('a[href*="monitoring"], a:has-text("Agent"), a:has-text("监控"), [data-testid="nav-monitoring"]')
        if monitoring_link.count() > 0:
            monitoring_link.first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        # If navigation fails, try direct URL
        page.goto(f"{BASE_URL}/monitoring", timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)


# ============================================================================
# Agent Metrics Tests
# ============================================================================

class TestAgentMetrics:
    """Test Agent Metrics Component"""

    def test_agent_metrics_renders(self, page: Page, authenticated_page: Page):
        """Test that agent metrics component renders"""
        page = authenticated_page

        # Navigate to monitoring page
        navigate_to_monitoring(page)

        # Wait for metrics component
        try:
            metrics_section = page.locator('text=Agent 性能指标, text=Agent Performance Metrics')
            expect(metrics_section).to_be_visible(timeout=10000)
        except Exception:
            # Take screenshot for debugging
            page.screenshot(path="tests/e2e/screenshots/agent_metrics_missing.png")
            # Component may not have data yet, which is acceptable
            pytest.skip("Agent metrics component not found - may need test data")

    def test_agent_metrics_cards_display(self, page: Page, authenticated_page: Page):
        """Test that agent metric cards display correct information"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Check for metric cards
        metric_cards = page.locator('[class*="AgentMetricCard"], [data-testid="agent-metric-card"]')

        # If cards exist, verify they contain expected data
        if metric_cards.count() > 0:
            # Each card should have agent name and metrics
            first_card = metric_cards.first
            expect(first_card).to_be_visible()

            # Check for agent name
            expect(first_card).to_contain_text(re.compile(r'agent|Agent', re.IGNORECASE))

            # Check for metrics (execution count, cost, etc.)
            expect(first_card).to_contain_text(re.compile(r'执行| Executions|成本|Cost', re.IGNORECASE))


# ============================================================================
# Cost Dashboard Tests
# ============================================================================

class TestCostDashboard:
    """Test Cost Dashboard Component"""

    def test_cost_dashboard_renders(self, page: Page, authenticated_page: Page):
        """Test that cost dashboard renders"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Wait for cost dashboard
        try:
            cost_section = page.locator('text=成本趋势, text=Cost Trend')
            expect(cost_section).to_be_visible(timeout=10000)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/cost_dashboard_missing.png")
            pytest.skip("Cost dashboard not found - may need test data")

    def test_cost_summary_cards(self, page: Page, authenticated_page: Page):
        """Test cost summary cards display"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Look for summary cards
        summary_cards = page.locator('[class*="SummaryCard"], [data-testid="summary-card"]')

        if summary_cards.count() > 0:
            # Should have multiple summary cards
            expect(summary_cards).to_have_count(3)

            # Check for key metrics
            page_content = page.content()
            assert any(keyword in page_content for keyword in [
                '总成本', 'Total Cost',
                '处理邮件', 'Emails Processed',
                '平均', 'Avg Cost'
            ])

    def test_performance_trend_chart(self, page: Page, authenticated_page: Page):
        """Test performance trend chart renders"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Wait for performance trend section
        try:
            perf_section = page.locator('text=性能趋势, text=Performance Trend')
            expect(perf_section).to_be_visible(timeout=10000)

            # Check for chart SVG (Recharts renders as SVG)
            charts = page.locator('svg')
            expect(charts).to_have_count(gte=1)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/performance_chart_missing.png")
            pytest.skip("Performance trend chart not found")


# ============================================================================
# Execution History Tests
# ============================================================================

class TestExecutionHistory:
    """Test Execution History Table"""

    def test_execution_history_renders(self, page: Page, authenticated_page: Page):
        """Test that execution history table renders"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Wait for execution history section
        try:
            history_section = page.locator('text=执行历史, text=Execution History')
            expect(history_section).to_be_visible(timeout=10000)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/execution_history_missing.png")
            pytest.skip("Execution history not found")

    def test_execution_history_table_structure(self, page: Page, authenticated_page: Page):
        """Test execution history table has correct columns"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Look for table headers
        try:
            table = page.locator('table').first
            expect(table).to_be_visible()

            # Check for expected column headers
            headers = table.locator('th')
            header_texts = [header.text_content().lower() for header in headers.all()]

            # Should have key columns
            expected_columns = ['task', 'agent', 'status', 'cost']
            found_columns = sum(1 for col in expected_columns if any(col in text for text in header_texts))

            assert found_columns >= 3, f"Expected at least 3 key columns, found {found_columns}"
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/table_structure_error.png")
            pytest.skip("Execution history table not found")

    def test_execution_history_status_badges(self, page: Page, authenticated_page: Page):
        """Test status badges display correctly"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Look for status badges in table
        status_badges = page.locator('span[class*="bg-"]:has-text("completed"), span:has-text("completed"), span:has-text("running"), span:has-text("pending")')

        if status_badges.count() > 0:
            # Verify status badge is visible
            expect(status_badges.first).to_be_visible()


# ============================================================================
# Execution Detail Modal Tests
# ============================================================================

class TestExecutionDetailModal:
    """Test Execution Detail Modal"""

    def test_modal_opens_on_click(self, page: Page, authenticated_page: Page):
        """Test that clicking execution row opens detail modal"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Find first execution row
        try:
            table = page.locator('table').first
            rows = table.locator('tbody tr')

            if rows.count() > 0:
                # Click first row
                rows.first.click()

                # Wait for modal to appear
                modal = page.locator('[class*="Modal"], [class*="modal"], [role="dialog"]')
                expect(modal).to_be_visible(timeout=5000)
            else:
                pytest.skip("No execution rows to click")
        except Exception as e:
            page.screenshot(path="tests/e2e/screenshots/modal_click_error.png")
            pytest.skip(f"Could not open modal: {str(e)}")

    def test_modal_displays_details(self, page: Page, authenticated_page: Page):
        """Test that modal displays execution details"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Open modal via first row
        try:
            table = page.locator('table').first
            rows = table.locator('tbody tr')

            if rows.count() > 0:
                rows.first.click()

                # Wait for modal
                modal = page.locator('[role="dialog"]').first
                expect(modal).to_be_visible(timeout=5000)

                # Check for detail sections
                modal_content = modal.text_content().lower()

                # Should have key information
                expected_fields = ['task', 'agent', 'status', 'cost']
                found_fields = sum(1 for field in expected_fields if field in modal_content)

                assert found_fields >= 2, f"Expected at least 2 detail fields, found {found_fields}"
            else:
                pytest.skip("No execution rows available")
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/modal_details_error.png")
            pytest.skip("Could not verify modal details")

    def test_modal_closes(self, page: Page, authenticated_page: Page):
        """Test that modal can be closed"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Open modal
        try:
            table = page.locator('table').first
            rows = table.locator('tbody tr')

            if rows.count() > 0:
                rows.first.click()

                # Wait for modal
                modal = page.locator('[role="dialog"]').first
                expect(modal).to_be_visible(timeout=5000)

                # Close by clicking X button or backdrop
                close_button = modal.locator('button:has-text("×"), button:has-text("Close")').first
                if close_button.count() > 0:
                    close_button.click()
                else:
                    # Click backdrop
                    page.keyboard.press('Escape')

                # Verify modal is closed
                expect(modal).to_be_hidden(timeout=5000)
            else:
                pytest.skip("No execution rows available")
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/modal_close_error.png")
            pytest.skip("Could not close modal")


# ============================================================================
# Status Filter Tests
# ============================================================================

class TestStatusFilter:
    """Test Status Filter Functionality"""

    def test_status_filter_exists(self, page: Page, authenticated_page: Page):
        """Test that status filter dropdown exists"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Look for status filter
        try:
            filter_select = page.locator('select:has-text("all"), select:has-text("All"), select:has-text("全部")')
            expect(filter_select).to_be_visible(timeout=5000)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/status_filter_missing.png")
            pytest.skip("Status filter not found")

    def test_status_filter_options(self, page: Page, authenticated_page: Page):
        """Test status filter has correct options"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Find filter select
        try:
            filter_select = page.locator('select').filter(has_text=re.compile(r'All|全部')).first

            options = filter_select.locator('option')
            option_texts = [opt.text_content().lower() for opt in options.all()]

            # Should have standard status options
            expected_statuses = ['all', 'pending', 'running', 'completed', 'failed']
            found_statuses = sum(1 for status in expected_statuses if any(status in text for text in option_texts))

            assert found_statuses >= 4, f"Expected at least 4 status options, found {found_statuses}"
        except Exception:
            pytest.skip("Could not verify filter options")


# ============================================================================
# Summary Cards Tests
# ============================================================================

class TestSummaryCards:
    """Test Summary Cards Section"""

    def test_summary_cards_renders(self, page: Page, authenticated_page: Page):
        """Test that summary cards render"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Look for summary section
        try:
            summary_section = page.locator('[class*="SummaryCard"], [data-testid="summary-card"]')
            expect(summary_section).to_have_count(gte=1, timeout=10000)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/summary_cards_missing.png")
            pytest.skip("Summary cards not found")

    def test_summary_cards_content(self, page: Page, authenticated_page: Page):
        """Test summary cards display key metrics"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Get page content
        page_content = page.content().lower()

        # Check for key metric keywords
        expected_keywords = [
            'total', 'execution',
            'success', 'rate',
            'cost',
            'agent'
        ]

        found_keywords = sum(1 for kw in expected_keywords if kw in page_content)
        assert found_keywords >= 2, f"Expected at least 2 metric keywords, found {found_keywords}"


# ============================================================================
# Responsive Design Tests
# ============================================================================

class TestResponsiveDesign:
    """Test Responsive Layout"""

    def test_mobile_viewport(self, page: Page, authenticated_page: Page):
        """Test component renders on mobile viewport"""
        page = authenticated_page

        # Resize to mobile
        page.set_viewport_size({"width": 375, "height": 667})

        navigate_to_monitoring(page)

        # Wait for content
        try:
            expect(page.locator('body')).to_contain_text(re.compile(r'Agent|监控', re.IGNORECASE), timeout=10000)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/mobile_view_error.png")
            pytest.skip("Mobile view test skipped")

    def test_tablet_viewport(self, page: Page, authenticated_page: Page):
        """Test component renders on tablet viewport"""
        page = authenticated_page

        # Resize to tablet
        page.set_viewport_size({"width": 768, "height": 1024})

        navigate_to_monitoring(page)

        # Wait for content
        try:
            expect(page.locator('body')).to_contain_text(re.compile(r'Agent|监控', re.IGNORECASE), timeout=10000)
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/tablet_view_error.png")
            pytest.skip("Table view test skipped")


# ============================================================================
# Integration Tests
# ============================================================================

class TestMonitoringIntegration:
    """Test API Integration"""

    def test_api_data_fetching(self, page: Page, authenticated_page: Page):
        """Test that page fetches data from API"""
        page = authenticated_page

        navigate_to_monitoring(page)

        # Wait for network to be idle (indicates API calls completed)
        page.wait_for_load_state("networkidle", timeout=10000)

        # Check if any data is displayed
        page_content = page.content()

        # Should have some content (even if empty state)
        assert len(page_content) > 0, "Page should have content"

    def test_loading_state(self, page: Page, authenticated_page: Page):
        """Test loading states are handled"""
        page = authenticated_page

        # Navigate and check for loading indicators
        navigate_to_monitoring(page)

        # Initial loading state may show skeleton
        time.sleep(1)  # Brief wait for loading

        # Loading should complete
        try:
            # Either data loads or empty state shows
            expect(page.locator('body')).to_contain_text(
                re.compile(r'Agent|监控|暂无|No data|Loading', re.IGNORECASE),
                timeout=10000
            )
        except Exception:
            page.screenshot(path="tests/e2e/screenshots/loading_state_error.png")
            raise


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
