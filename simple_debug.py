#!/usr/bin/env python3
import time
from playwright.sync_api import sync_playwright

def simple_debug():
    """简单的滚动调试"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.set_viewport_size({"width": 1280, "height": 1000})

        url = "https://chaojifeng.feishu.cn/wiki/UTPswj4VoipiDHk1PTFcZaLanjf"
        print(f"Loading: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(5)

        # 检测滚动容器
        container = page.locator(".bear-web-x-container.catalogue-opened.docx-in-wiki")
        if container.count() > 0:
            print("Found Feishu scroll container")

            # 获取高度信息
            scroll_height = container.evaluate("el => el.scrollHeight")
            client_height = container.evaluate("el => el.clientHeight")
            max_scroll = scroll_height - client_height

            print(f"scrollHeight: {scroll_height}")
            print(f"clientHeight: {client_height}")
            print(f"Maximum scroll position: {max_scroll}")

            # 测试不同的滚动方法
            print("\n=== Testing different scroll methods ===")

            # 1. 直接设置scrollTop
            container.evaluate(f"el => el.scrollTop = {max_scroll}")
            time.sleep(1)
            pos1 = container.evaluate("el => el.scrollTop")
            print(f"Method 1 - Direct scrollTop: {pos1}")

            # 2. 使用Element.scroll()
            container.evaluate("el => el.scroll(0, el.scrollHeight)")
            time.sleep(1)
            pos2 = container.evaluate("el => el.scrollTop")
            print(f"Method 2 - Element.scroll(): {pos2}")

            # 3. 查找最后一个元素并滚动到它
            last_element_pos = page.evaluate("""
                () => {
                    const container = document.querySelector('.bear-web-x-container.catalogue-opened.docx-in-wiki');
                    if (!container) return 0;

                    // 查找容器内的最后一个可见元素
                    const allElements = container.querySelectorAll('*');
                    let lastElement = null;
                    let maxBottom = 0;

                    for (let el of allElements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.bottom > maxBottom) {
                            maxBottom = rect.bottom;
                            lastElement = el;
                        }
                    }

                    if (lastElement) {
                        lastElement.scrollIntoView({block: 'end', behavior: 'auto'});
                        return container.scrollTop;
                    }
                    return 0;
                }
            """)
            time.sleep(1)
            pos3 = container.evaluate("el => el.scrollTop")
            print(f"Method 3 - Last element scrollIntoView: {pos3}")

            # 最终比较
            print(f"\n=== Results ===")
            print(f"Target max position: {max_scroll}")
            print(f"Best achieved position: {max(pos1, pos2, pos3)}")
            print(f"Difference: {max_scroll - max(pos1, pos2, pos3)}")

            # 截图验证
            page.screenshot(path="debug_best_position.png")
            print("Screenshot saved: debug_best_position.png")

        browser.close()

if __name__ == "__main__":
    simple_debug()