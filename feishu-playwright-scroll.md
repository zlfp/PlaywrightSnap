# Feishu (飞书) with Playwright (Python): Scrolling Cookbook

> 本文档总结了在 **Python + Playwright** 下控制“飞书”（Web 端或 WebView）页面滚动的常用方法与实用片段，便于粘贴给 Claude Code 继续开发。

---

## 环境与前提

- 安装 Playwright（Python）：
  ```bash
  pip install playwright
  playwright install
  ```
- 建议使用 **异步 API**（`playwright.async_api`）。
- 假设你已拿到 `page` 对象（已登录或已进入目标页面）。

---

## 方式一：在页面上下文执行 JS（`page.evaluate`）

最通用的方式，直接操作 `window` 或 DOM：

```python
# 向下滚动 500 像素
await page.evaluate("window.scrollBy(0, 500)")

# 滚动到页面底部
await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
```

用于 **无限滚动**（动态加载内容）的一个通用循环：

```python
async def scroll_to_bottom(page, max_scrolls: int = 50, delay_ms: int = 1000):
    previous_height = 0
    for _ in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(delay_ms)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height
```

> 参考：Playwright 官方 *Evaluating JavaScript* 指南。

---

## 方式二：模拟鼠标滚轮（`page.mouse.wheel`）

更“接近用户”的滚动手势：

```python
# 连续滚动两次，每次 300 像素
await page.mouse.wheel(0, 300)
await page.wait_for_timeout(400)
await page.mouse.wheel(0, 300)
```

也可用于无限滚动：

```python
async def wheel_to_bottom(page, max_scrolls: int = 50, step: int = 15000, delay_ms: int = 800):
    for _ in range(max_scrolls):
        await page.mouse.wheel(0, step)
        await page.wait_for_timeout(delay_ms)
```

> 说明：`mouse.wheel` 会分发 `wheel` 事件，通常会触发滚动。

---

## 方式三：滚动**内部可滚动容器**（元素滚动）

飞书页面中常见内部滚动区（如消息列表、侧栏、文件夹树）。这时应滚动容器元素，而不是 `window`。

```python
# 例：滚动某个容器（请替换为真实选择器）
container = page.locator(".scrollable-container")
await container.evaluate("el => el.scrollTop += 400")   # 向下滚动 400
await container.evaluate("el => el.scrollTop = el.scrollHeight")  # 滚到底部
```

如果需要“滚动直到某元素可见”，可结合 `locator.scroll_into_view_if_needed()`：

```python
target = page.get_by_text("目标消息或元素文本")
await target.scroll_into_view_if_needed()
```

> 小贴士：优先用 **role/text/label** 等更稳定的定位方式（`get_by_role`, `get_by_text`, `get_by_label`），少用脆弱的深层级 CSS。

---

## 方式四：键盘滚动（`PageDown` / `End` / 方向键）

```python
await page.keyboard.press("PageDown")
await page.keyboard.press("End")  # 滚到底部
```

> 依赖页面是否对键盘滚动有响应，不是所有页面都有效。

---

## Feishu（飞书）页面的常见注意点

1. **内部滚动容器**：聊天/频道列表经常是内部 `div` 可滚动，需用“方式三”针对容器滚动。
2. **动态渲染/虚拟列表**：滚动后内容才加载，建议：
   - 滚一次 → `wait_for_timeout(...)` 或等待某条内容出现（`locator.wait_for(...)`）。
   - 用“高度变更”或“元素计数变更”来判断是否还有新内容。
3. **iframe / 嵌入视图**：如遇 iframe，需先 `frame = page.frame(...)` 或用 `frame_locator(...)` 进入对应 frame，再滚动。
4. **防止抢焦点**：滚动前可先 `await page.bring_to_front()` 或点击空白处，以确保键盘/鼠标事件有效。
5. **选择器定位思路**：
   - 文本定位：`page.get_by_text("群公告")`
   - 角色定位：`page.get_by_role("button", name="发送")`
   - 渐进收窄：`page.locator("section").get_by_role("list")...`
6. **错误恢复**：若滚动无效，检查：
   - 是否滚到了**正确容器**（用 `el.scrollHeight`/`el.clientHeight` 调试）。
   - 是否被 CSS 拦截（如 `overscroll-behavior`, 自定义滚动方案）。
   - 有无等待加载（适当 `wait_for_timeout` 或等待可见元素）。

---

## 端到端示例（异步版）

```python
import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 打开飞书 Web 端（示例：需替换为你的入口）
        await page.goto("https://www.feishu.cn/")

        # 假设你已经完成登录，进入某工作区的消息页面后：
        # 1) 尝试全页滚动
        await page.evaluate("window.scrollBy(0, 500)")

        # 2) 用鼠标滚轮
        await page.mouse.wheel(0, 1200)

        # 3) 针对内部容器（示例选择器需替换为真实值）
        msg_list = page.locator('[data-qa="message-list"]')  # 假设存在这样的自定义属性
        if await msg_list.count():
            await msg_list.evaluate("el => el.scrollTop = el.scrollHeight")

        # 4) 无限滚动（演示：以全页为例）
        await page.evaluate("window.scrollTo(0, 0)")  # 先回到顶部
        await page.wait_for_timeout(500)

        previous_height = 0
        for _ in range(30):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                break
            previous_height = new_height

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

> 提示：工作中建议把“滚动策略”封装为工具函数，允许选择 “全页滚动 / 容器滚动 / 鼠标滚轮 / 键盘滚动”，并支持“最大滚动次数、步进、等待策略”等参数。

---

## 进一步阅读（英文文档）

- `mouse.wheel`（Python）：Playwright 官方文档  
- 键盘事件（`keyboard.press` 等）：Playwright 官方文档  
- 在页面上下文执行 JS：`page.evaluate`（Python）官方指南  
- 定位器（Locator）与稳定定位策略  
- “滚动到底部 / 无限滚动”的实战参考文章  

（把本文与链接一起交给 Claude Code，可根据你的具体 DOM 结构生成更精确的滚动逻辑与选择器。）
