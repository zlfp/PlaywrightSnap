#!/usr/bin/env python3
import os, math, json, time, pathlib, re
from typing import List, Optional
import typer
from PIL import Image
from datetime import datetime
from playwright.sync_api import sync_playwright

app = typer.Typer(help="Scroll-and-snap webpage to tiles, optionally stitch into one long image.")

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def safe_dirname(url: str) -> str:
    name = re.sub(r'^https?://', '', url)
    name = re.sub(r'[^a-zA-Z0-9._-]+', '_', name)
    return name[:120]

def ensure_dir(p: str): pathlib.Path(p).mkdir(parents=True, exist_ok=True)

def stitch_tiles(tile_paths: List[str], out_path: str, overlap_top: int = 0, overlap_bottom: int = 0):
    tiles = [Image.open(p) for p in tile_paths]
    widths = [im.width for im in tiles]
    heights = [im.height for im in tiles]

    if not tiles:
        raise RuntimeError("No tiles to stitch")

    width = max(widths)

    # 累计高度（考虑去掉每块顶部/底部的重复区域）
    total_height = 0
    for i, h in enumerate(heights):
        h_eff = h
        if i > 0:
            h_eff -= overlap_top
        if i < len(heights) - 1:
            h_eff -= overlap_bottom
        total_height += max(1, h_eff)

    canvas = Image.new("RGB", (width, total_height), (255, 255, 255))
    y_offset = 0
    for i, im in enumerate(tiles):
        top_crop = overlap_top if i > 0 else 0
        bottom_crop = overlap_bottom if i < len(tiles)-1 else 0
        crop_box = (0, top_crop, im.width, im.height - bottom_crop)
        im_cropped = im.crop(crop_box)
        canvas.paste(im_cropped, (0, y_offset))
        y_offset += im_cropped.height

    canvas.save(out_path)
    for im in tiles:
        im.close()

WAIT_MAP = {
    "load": "load",
    "dom": "domcontentloaded",
    "networkidle": "networkidle"
}

@app.command()
def snap(
    url: List[str] = typer.Argument(..., help="One or more webpage URLs."),
    out: str = typer.Option("out", help="Output directory."),
    stitch: bool = typer.Option(False, help="Stitch all tiles into one long image."),
    width: int = typer.Option(1280, help="Viewport width."),
    height: int = typer.Option(1000, help="Viewport height (tile height baseline)."),
    scale: float = typer.Option(1.0, help="deviceScaleFactor, e.g. 1.0 / 2.0"),
    wait: str = typer.Option("networkidle", help="load|dom|networkidle|<seconds>s"),
    scroll_delay_ms: int = typer.Option(350, help="Delay after each scroll (ms)."),
    tile_overlap: int = typer.Option(80, help="Overlap pixels between tiles to avoid gaps."),
    sticky_top: int = typer.Option(0, help="Pixels to crop from top for tiles 2..N when stitching."),
    sticky_bottom: int = typer.Option(0, help="Pixels to crop from bottom for tiles 1..N-1 when stitching."),
    cap_height: int = typer.Option(50000, help="Max page scrollHeight to capture."),
    cookies: Optional[str] = typer.Option(None, help="Path to cookies.json (exported format)."),
    user_data_dir: Optional[str] = typer.Option(None, help="Chromium user data dir for persistent login."),
    mobile: bool = typer.Option(False, help="Emulate mobile-like viewport/touch UA."),
    headless: bool = typer.Option(True, help="Run headless."),
):
    session_dir = os.path.join(out, ts())
    ensure_dir(session_dir)

    meta = dict(urls=url, started_at=time.time(), tiles=[])
    meta_path = os.path.join(session_dir, "meta.json")

    with sync_playwright() as p:
        launch_opts = dict(headless=headless, args=["--disable-gpu"])
        if user_data_dir:
            browser = p.chromium.launch_persistent_context(user_data_dir, **launch_opts)
        else:
            browser = p.chromium.launch(**launch_opts)
        context = browser if user_data_dir else browser.new_context()

        if mobile:
            # 简单的移动端模拟（可换成官方设备描述）
            context.grant_permissions([])
            context.set_default_timeout(30000)

        if cookies:
            try:
                with open(cookies, "r", encoding="utf-8") as f:
                    jar = json.load(f)
                # 兼容 Playwright cookie 字段名
                context.add_cookies(jar)
            except Exception as e:
                print(f"[warn] failed to load cookies: {e}")

        page = context.new_page()

        # 视口与缩放
        page.set_viewport_size({"width": width, "height": height})
        page.evaluate(f"() => {{ document.body.style.zoom = {scale}; }}")

        for u in url:
            print(f"==> {u}")
            url_dir = os.path.join(session_dir, safe_dirname(u))
            tiles_dir = os.path.join(url_dir, "tiles")
            ensure_dir(tiles_dir)

            # 加载策略
            if wait.endswith("s") and wait[:-1].isdigit():
                target_state = "load"
                page.goto(u, wait_until=target_state, timeout=60000)
                time.sleep(float(wait[:-1]))
            else:
                target_state = WAIT_MAP.get(wait, "networkidle")
                page.goto(u, wait_until=target_state, timeout=90000)

            # 计算页面总高度
            total_height = page.evaluate("() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
            total_height = min(total_height, cap_height)
            viewport_h = height
            step = max(1, viewport_h - tile_overlap)

            # 循环分块
            tile_paths = []
            y = 0
            idx = 1
            while y < total_height:
                page.evaluate(f"(y) => window.scrollTo(0, y)", y)
                page.wait_for_timeout(scroll_delay_ms)

                # 计算当前块有效高度
                remaining = total_height - y
                h_eff = viewport_h if remaining >= viewport_h else remaining

                # 截图（整窗截即可；也可改 clip 方案）
                tile_path = os.path.join(tiles_dir, f"tile_{idx:04d}.png")
                page.screenshot(path=tile_path)
                tile_paths.append(tile_path)

                meta["tiles"].append({"url": u, "tile": tile_path, "y": y, "height": h_eff})
                y += step
                idx += 1

            # 保存单页元数据
            ensure_dir(url_dir)
            with open(os.path.join(url_dir, "page_meta.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "url": u,
                    "total_height": total_height,
                    "viewport": {"width": width, "height": height},
                    "scale": scale,
                    "wait": wait,
                    "tiles": tile_paths
                }, f, ensure_ascii=False, indent=2)

            # 拼接
            if stitch and tile_paths:
                stitched_path = os.path.join(url_dir, "stitched.png")
                stitch_tiles(tile_paths, stitched_path, overlap_top=sticky_top, overlap_bottom=sticky_bottom)
                print(f"[ok] stitched -> {stitched_path}")

        # 关闭
        if user_data_dir:
            context.close()
        else:
            context.close()
            browser.close()

    meta["finished_at"] = time.time()
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Output at: {session_dir}")

if __name__ == "__main__":
    app()