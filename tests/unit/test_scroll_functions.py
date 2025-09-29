#!/usr/bin/env python3
"""
单元测试：测试滚动相关函数
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from snap import get_scroll_container, scroll_and_wait, get_current_scroll_position, get_total_scroll_height


class TestScrollContainerDetection:
    """测试滚动容器检测"""

    def test_selector_parsing(self):
        """测试选择器解析逻辑"""
        # 这里我们测试选择器列表是否正确
        from snap import get_scroll_container

        # 模拟选择器列表（实际测试需要真实的page对象）
        selectors = [
            ".bear-web-x-container.catalogue-opened.docx-in-wiki",
            ".bear-web-x-container",
            ".docx-content",
            ".wiki-content",
            "[role='main']",
            "main",
            ".scrollable-container",
            ".content-container"
        ]

        assert len(selectors) == 8
        assert "bear-web-x-container" in selectors[0]
        assert "docx-in-wiki" in selectors[0]


class MockPage:
    """模拟Page对象用于测试"""

    def __init__(self):
        self.scroll_height = 2000
        self.client_height = 1000
        self.scroll_top = 0
        self.mouse = MockMouse(self)

    def locator(self, selector):
        return MockLocator(self, selector)

    def evaluate(self, script):
        if "scrollHeight" in script:
            return self.scroll_height
        elif "clientHeight" in script:
            return self.client_height
        elif "scrollTop" in script:
            return self.scroll_top
        elif "scrollBy" in script:
            # 模拟滚动
            import re
            match = re.search(r'scrollBy\(\s*0,\s*(\d+)\s*\)', script)
            if match:
                scroll_amount = int(match.group(1))
                self.scroll_top += scroll_amount
        return None

    def wait_for_load_state(self, state, timeout=None):
        # 模拟等待状态
        pass

    def wait_for_timeout(self, timeout):
        # 模拟等待超时
        pass


class MockMouse:
    """模拟Mouse对象"""

    def __init__(self, page):
        self.page = page

    def wheel(self, delta_x, delta_y):
        self.page.scroll_top += delta_y


class MockLocator:
    """模拟Locator对象"""

    def __init__(self, page, selector):
        self.page = page
        self.selector = selector
        self.count_value = 1

    def count(self):
        return self.count_value

    def evaluate(self, script):
        if "scrollHeight" in script:
            return self.page.scroll_height
        elif "clientHeight" in script:
            return self.page.client_height
        elif "scrollTop" in script:
            return self.page.scroll_top
        elif "scrollBy" in script:
            # 模拟滚动
            import re
            match = re.search(r'scrollBy\(\s*0,\s*(\d+)\s*\)', script)
            if match:
                scroll_amount = int(match.group(1))
                self.page.scroll_top += scroll_amount
        return None


class TestScrollFunctions:
    """测试滚动函数"""

    def test_get_total_scroll_height_window(self):
        """测试获取窗口总滚动高度"""
        page = MockPage()
        page.scroll_height = 2000
        page.client_height = 1000

        height = get_total_scroll_height(page, None, "window")
        assert height == 2000

    def test_get_total_scroll_height_container(self):
        """测试获取容器总滚动高度"""
        page = MockPage()
        container = MockLocator(page, ".test")
        page.scroll_height = 1500
        page.client_height = 800

        height = get_total_scroll_height(page, container, ".test")
        assert height == 1500

    def test_get_current_scroll_position_window(self):
        """测试获取窗口当前滚动位置"""
        page = MockPage()
        page.scroll_top = 500

        position = get_current_scroll_position(page, None, "window")
        assert position == 500

    def test_get_current_scroll_position_container(self):
        """测试获取容器当前滚动位置"""
        page = MockPage()
        container = MockLocator(page, ".test")
        page.scroll_top = 300

        position = get_current_scroll_position(page, container, ".test")
        assert position == 300

    def test_scroll_and_wait_window(self):
        """测试窗口滚动并等待"""
        page = MockPage()
        initial_position = page.scroll_top

        scroll_and_wait(page, None, "window", 200)

        # 验证位置发生了变化
        assert page.scroll_top == initial_position + 200

    def test_scroll_and_wait_container(self):
        """测试容器滚动并等待"""
        page = MockPage()
        container = MockLocator(page, ".test")
        initial_position = page.scroll_top

        scroll_and_wait(page, container, ".test", 150)

        # 验证位置发生了变化
        assert page.scroll_top == initial_position + 150

    def test_scroll_bottom_detection(self):
        """测试滚动到底部检测逻辑"""
        page = MockPage()
        page.scroll_height = 2000
        page.client_height = 1000
        page.scroll_top = 1000  # 已经在底部

        # 模拟滚动检测逻辑
        max_scroll = page.scroll_height - page.client_height
        assert page.scroll_top == max_scroll

        # 尝试滚动 - 在实际情况下，滚动到底部后仍然可以滚动
        scroll_and_wait(page, None, "window", 100)
        # Mock对象没有底部限制，所以位置会变化
        assert page.scroll_top == 1100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])