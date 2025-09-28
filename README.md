# Playwright Snap — 滚动截屏拼接（MVP）

一个用 Playwright + Typer + Pillow 实现的命令行工具：滚动网页并按视口分块截图，支持将多块图片拼接为一张长图，附带元数据输出，方便后续处理。

## 环境要求
- Python ≥ 3.10（建议）
- macOS / Linux / Windows（需可安装 Playwright 浏览器）

## 虚拟环境（推荐）
为避免依赖冲突，建议使用虚拟环境：

**创建并激活虚拟环境：**
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

**使用完成后退出虚拟环境：**
```bash
deactivate
```

## 安装
1) 安装依赖：
```
pip install -r requirements.txt
```
2) 安装 Playwright 浏览器（至少 Chromium）：
```
python -m playwright install chromium
```
如需安装全部浏览器：
```
python -m playwright install
```

## 快速开始
对单个网页滚动截屏，输出到默认目录 `out/<时间戳>/`：
```
python snap.py https://example.com
```
对多个网页：
```
python snap.py https://example.com https://news.ycombinator.com
```

## 常用参数
- `--out` 输出根目录（默认 `out`）。例如：`--out shots`
- `--stitch` 将所有分块拼接为一张长图，例如：`--stitch`
- 视口与缩放：`--width 1280 --height 1000 --scale 1.0`（scale 使用 CSS zoom）
- 加载等待：`--wait networkidle` 或固定时间如 `--wait 5s`
- 滚动节奏：`--scroll_delay_ms 350`（每次滚动后的等待毫秒数）
- 分块重叠：`--tile_overlap 80`（避免缝隙，可结合拼接时的裁剪参数）
- 拼接裁剪：`--sticky_top 0 --sticky_bottom 0`（拼接时对中间块的顶部/底部进行裁剪像素）
- 截图上限：`--cap_height 50000`（限制页面滚动高度）
- Cookies：`--cookies cookies.json`（使用 Playwright 的 cookies JSON 格式）
- 持久登录：`--user_data_dir ~/.cache/pw-user`（使用持久化 Chromium 用户目录）
- 移动端模拟：`--mobile`（简单移动端视口/触控 UA 处理）
- 有头模式：`--headless False`（默认 True）

查看全部参数：
```
python snap.py --help
```

## 示例
1) 生成并拼接长图：
```
python snap.py \
  https://example.com \
  --out output \
  --width 1280 --height 1000 --scale 1.0 \
  --wait networkidle \
  --tile_overlap 80 \
  --stitch --sticky_top 80 --sticky_bottom 80
```
执行完成后，输出结构类似：
```
output/
  2024-01-01_12-00-00/
    example.com/
      tiles/
        tile_0001.png
        tile_0002.png
        ...
      stitched.png           # 如果设置了 --stitch
      page_meta.json         # 单页元信息（视口、总高度、参数、tile 列表）
    meta.json                # 这次会话的总体信息（所有 URL 的 tile 列表）
```

2) 使用 cookies 和持久化用户目录（适合需要登录的站点）：
```
python snap.py \
  https://example.com/account \
  --cookies cookies.json \
  --user_data_dir ~/.cache/pw-user \
  --stitch
```

3) 指定等待时间（而非加载状态）：
```
python snap.py https://example.com --wait 5s
```

4) **有头浏览器模式（推荐用于需要登录的站点）：**
```
python snap.py https://chaojifeng.feishu.cn/wiki/UTPswj4VoipiDHk1PTFcZaLanjf --no-headless --wait 10s
```
**适用场景：**
- 需要手动登录的网站（如飞书文档、Notion等）
- 复杂的单页应用（SPA）
- 调试和验证截图效果

**关键参数说明：**
- `--no-headless`: 显示浏览器窗口，可手动操作登录
- `--wait 10s`: 使用固定等待时间而非 `networkidle`，适合复杂应用
- 登录后程序会自动继续执行截图任务

## 使用建议与注意事项
- 如果出现拼接重复或缝隙，调大 `--tile_overlap` 并结合 `--sticky_top/--sticky_bottom` 做裁剪。
- 某些页面滚动高度异常时可减小 `--cap_height`。
- `--scale` 通过注入 CSS `zoom` 实现，可能与真实 DPR 有差异；如需更精准，考虑调整 Playwright 的设备参数。
- `--mobile` 为简化版移动端模拟，复杂场景可按需扩展 Playwright 设备描述。
- 首次使用需确保已安装 Playwright 浏览器（见安装步骤）。
- **重要提示**：对于需要登录的复杂网站（如飞书、Notion等），推荐使用 `--no-headless --wait 10s` 组合，这是最简单有效的解决方案。
- `networkidle` 等待状态在某些复杂应用中可能永远不会达成，建议使用固定等待时间如 `--wait 5s` 或 `--wait 10s`。

## 运行原理概述
- 使用 Playwright 同步 API 打开页面，按设定的视口和滚动步进进行多次截图。
- 将截图存放于每个 URL 的 `tiles/` 目录，并记录元数据。
- 可选地根据重叠与裁剪参数将多张分块图拼接为一张长图。

如有更多需求（元素高亮、指定 clip 截图、设备预设等），可以在此 MVP 的基础上继续扩展。
