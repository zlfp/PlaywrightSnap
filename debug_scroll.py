#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

def debug_scroll_position():
    """调试滚动位置检测"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.set_viewport_size({"width": 1280, "height": 1000})

        url = "https://chaojifeng.feishu.cn/wiki/UTPswj4VoipiDHk1PTFcZaLanjf"
        print(f"Loading: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(10)

        # 检测滚动容器
        container = page.locator(".bear-web-x-container.catalogue-opened.docx-in-wiki")
        if container.count() > 0:
            print("Found Feishu scroll container")

            # 获取各种高度信息
            scroll_height = container.evaluate("el => el.scrollHeight")
            client_height = container.evaluate("el => el.clientHeight")
            scroll_top = container.evaluate("el => el.scrollTop")

            print(f"scrollHeight: {scroll_height}")
            print(f"clientHeight: {client_height}")
            print(f"scrollTop: {scroll_top}")
            print(f"Max scroll position: {scroll_height - client_height}")

            # 测试滚动到底部
            print("\n=== Testing scroll to bottom ===")

            # 方法1: 直接设置scrollTop
            container.evaluate(f"el => el.scrollTop = {scroll_height - client_height}")
            time.sleep(1)

            final_top = container.evaluate("el => el.scrollTop")
            print(f"After direct scroll: scrollTop = {final_top}")

            # 方法2: 使用scrollIntoView
            print("\n=== Testing scrollIntoView ===")
            page.evaluate("""
                () => {
                    // 查找最后一个元素
                    const allElements = document.querySelectorAll('*');
                    let lastElement = null;
                    for (let el of allElements) {
                        if (el.getBoundingClientRect && el.getBoundingClientRect().bottom > 0) {
                            lastElement = el;
                        }
                    }
                    if (lastElement) {
                        lastElement.scrollIntoView({block: 'end', behavior: 'auto'});
                        console.log('Scrolled to last element:', lastElement.tagName, lastElement.className);
                    }
                }
            """)
            time.sleep(1)

            final_top_2 = container.evaluate("el => el.scrollTop")
            print(f"After scrollIntoView: scrollTop = {final_top_2}")

            # 方法3: 模拟用户滚动到最底部
            print("\n=== Testing mouse wheel to bottom ===")
            page.mouse.wheel(0, 50000)
            time.sleep(2)

            final_top_3 = container.evaluate("el => el.scrollTop")
            print(f"After mouse wheel: scrollTop = {final_top_3}")

            # 最终验证
            max_possible = scroll_height - client_height
            print(f"\n=== Final Analysis ===")
            print(f"Maximum possible scroll position: {max_possible}")
            print(f"Final scroll position: {final_top_3}")
            print(f"Can reach bottom: {final_top_3 >= max_possible - 10}")

            # 截图对比
            print("\n=== Taking screenshots ===")

            # 截图当前状态
            page.screenshot(path="debug_final_position.png")
            print("Screenshot taken: debug_final_position.png")

            # 尝试滚动到不同位置并截图
            positions = [0, scroll_height//3, 2*scroll_height//3, max_possible]
            for i, pos in enumerate(positions):
                container.evaluate(f"el => el.scrollTop = {pos}")
                time.sleep(1)
                actual_pos = container.evaluate("el => el.scrollTop")
                page.screenshot(path=f"debug_pos_{i+1}_y{actual_pos}.png")
                print(f"Position {i+1}: target={pos}, actual={actual_pos}")

        browser.close()

if __name__ == "__main__":
    debug_scroll_position()