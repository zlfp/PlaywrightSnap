#!/usr/bin/env python3
"""
端到端测试：测试完整的滚动截图流程
"""

import pytest
import sys
import os
import tempfile
import shutil
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from snap import snap
from PIL import Image
import json


class TestEndToEndScrollCapture:
    """端到端测试：完整的滚动截图流程"""

    @pytest.fixture
    def test_page_url(self):
        """提供测试页面的URL"""
        # 获取测试HTML文件的绝对路径
        test_page_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "fixtures", "test_page.html"
        )
        test_page_path = os.path.abspath(test_page_path)
        return f"file://{test_page_path}"

    @pytest.fixture
    def temp_output_dir(self):
        """提供临时输出目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_basic_scroll_capture(self, test_page_url, temp_output_dir):
        """测试基本滚动截图功能"""
        print(f"Testing URL: {test_page_url}")
        print(f"Output directory: {temp_output_dir}")

        # 运行滚动截图
        snap(
            url=[test_page_url],
            out=temp_output_dir,
            stitch=False,  # 不拼接，单独测试截图功能
            width=800,
            height=600,
            wait="load",
            scroll_delay_ms=500,
            tile_overlap=50,
            headless=True  # 使用无头模式进行测试
        )

        # 验证输出结构
        session_dirs = [d for d in os.listdir(temp_output_dir) if os.path.isdir(os.path.join(temp_output_dir, d))]
        assert len(session_dirs) >= 1, "应该至少有一个会话目录"

        latest_session = session_dirs[-1]
        session_path = os.path.join(temp_output_dir, latest_session)

        # 验证元数据文件
        meta_path = os.path.join(session_path, "meta.json")
        assert os.path.exists(meta_path), "元数据文件应该存在"

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert "urls" in meta
        assert "tiles" in meta
        assert len(meta["tiles"]) > 0, "应该至少有一个截图"

        # 验证URL目录结构
        from snap import safe_dirname
        expected_url_dirname = safe_dirname(test_page_url)
        url_dir = os.path.join(session_path, expected_url_dirname)
        assert os.path.exists(url_dir), f"URL目录应该存在: {expected_url_dirname}"

        # 验证tiles目录
        tiles_dir = os.path.join(url_dir, "tiles")
        assert os.path.exists(tiles_dir), "tiles目录应该存在"

        # 验证截图文件
        tile_files = [f for f in os.listdir(tiles_dir) if f.endswith(".png")]
        assert len(tile_files) > 0, "应该至少有一个截图文件"

        # 验证所有截图文件都能正常打开
        for tile_file in tile_files:
            tile_path = os.path.join(tiles_dir, tile_file)
            assert os.path.exists(tile_path), f"截图文件应该存在: {tile_file}"

            try:
                img = Image.open(tile_path)
                assert img.size[0] == 800, f"截图宽度应该为800: {tile_file}"
                assert img.size[1] == 600, f"截图高度应该为600: {tile_file}"
                img.close()
            except Exception as e:
                pytest.fail(f"无法打开截图文件 {tile_file}: {e}")

        # 验证页面元数据
        page_meta_path = os.path.join(url_dir, "page_meta.json")
        assert os.path.exists(page_meta_path), "页面元数据文件应该存在"

        with open(page_meta_path, "r", encoding="utf-8") as f:
            page_meta = json.load(f)

        assert "url" in page_meta
        assert "total_height" in page_meta
        assert "viewport" in page_meta
        assert "tiles" in page_meta
        assert page_meta["viewport"]["width"] == 800
        assert page_meta["viewport"]["height"] == 600

        print(f"✅ 成功捕获 {len(tile_files)} 个截图")
        print(f"✅ 页面总高度: {page_meta['total_height']}")

    def test_scroll_capture_with_stitching(self, test_page_url, temp_output_dir):
        """测试带拼接的滚动截图功能"""
        # 运行滚动截图并拼接
        snap(
            url=[test_page_url],
            out=temp_output_dir,
            stitch=True,  # 启用拼接
            width=800,
            height=600,
            wait="load",
            scroll_delay_ms=500,
            tile_overlap=50,
            sticky_top=25,
            sticky_bottom=25,
            headless=True
        )

        # 验证拼接后的文件
        session_dirs = [d for d in os.listdir(temp_output_dir) if os.path.isdir(os.path.join(temp_output_dir, d))]
        latest_session = session_dirs[-1]
        session_path = os.path.join(temp_output_dir, latest_session)

        from snap import safe_dirname
        expected_url_dirname = safe_dirname(test_page_url)
        url_dir = os.path.join(session_path, expected_url_dirname)
        stitched_path = os.path.join(url_dir, "stitched.png")

        assert os.path.exists(stitched_path), "拼接后的文件应该存在"

        # 验证拼接后的图片
        stitched_img = Image.open(stitched_path)
        assert stitched_img.size[0] == 800, "拼接后宽度应该为800"
        assert stitched_img.size[1] > 600, "拼接后高度应该大于单个tile的高度"
        stitched_img.close()

        print(f"✅ 拼接成功，拼接后尺寸: {stitched_img.size}")

    def test_multiple_urls(self, test_page_url, temp_output_dir):
        """测试多个URL的处理"""
        # 运行多个URL的滚动截图
        snap(
            url=[test_page_url, test_page_url],  # 同一个URL两次
            out=temp_output_dir,
            stitch=False,
            width=800,
            height=600,
            wait="load",
            scroll_delay_ms=500,
            tile_overlap=50,
            headless=True
        )

        # 验证输出结构
        session_dirs = [d for d in os.listdir(temp_output_dir) if os.path.isdir(os.path.join(temp_output_dir, d))]
        assert len(session_dirs) >= 1, "应该至少有一个会话目录"

        latest_session = session_dirs[-1]
        session_path = os.path.join(temp_output_dir, latest_session)

        # 验证元数据
        meta_path = os.path.join(session_path, "meta.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert len(meta["urls"]) == 2, "应该处理2个URL"
        assert len(meta["tiles"]) > 0, "应该有截图记录"

        print(f"✅ 成功处理 {len(meta['urls'])} 个URL")

    def test_different_viewport_sizes(self, test_page_url, temp_output_dir):
        """测试不同的视口大小"""
        # 测试不同的视口大小
        viewports = [
            (1024, 768),
            (800, 600),
            (640, 480)
        ]

        for width, height in viewports:
            print(f"测试视口大小: {width}x{height}")

            # 为每个视口测试创建独立的子目录
            viewport_dir = os.path.join(temp_output_dir, f"viewport_{width}x{height}")
            os.makedirs(viewport_dir, exist_ok=True)

            snap(
                url=[test_page_url],
                out=viewport_dir,
                stitch=False,
                width=width,
                height=height,
                wait="load",
                scroll_delay_ms=500,
                tile_overlap=50,
                headless=True
            )

            # 验证截图尺寸
            session_dirs = [d for d in os.listdir(viewport_dir) if os.path.isdir(os.path.join(viewport_dir, d))]
            latest_session = session_dirs[-1]
            session_path = os.path.join(viewport_dir, latest_session)

            from snap import safe_dirname
            expected_url_dirname = safe_dirname(test_page_url)
            url_dir = os.path.join(session_path, expected_url_dirname)
            tiles_dir = os.path.join(url_dir, "tiles")

            if os.path.exists(tiles_dir):
                tile_files = [f for f in os.listdir(tiles_dir) if f.endswith(".png")]
                if tile_files:
                    first_tile = os.path.join(tiles_dir, tile_files[0])
                    img = Image.open(first_tile)
                    assert img.size[0] == width, f"截图宽度应该为{width}，实际为{img.size[0]}"
                    assert img.size[1] == height, f"截图高度应该为{height}，实际为{img.size[1]}"
                    img.close()

        print(f"✅ 成功测试 {len(viewports)} 种视口大小")

    def test_error_handling_invalid_url(self, temp_output_dir):
        """测试无效URL的错误处理"""
        # 测试无效URL
        with pytest.raises(Exception):
            snap(
                url=["https://invalid-url-that-does-not-exist.com"],
                out=temp_output_dir,
                width=800,
                height=600,
                wait="load",
                timeout=5000,  # 短超时
                headless=True
            )

    def test_tile_overlap_functionality(self, test_page_url, temp_output_dir):
        """测试tile重叠功能"""
        # 测试不同的重叠值
        snap(
            url=[test_page_url],
            out=temp_output_dir,
            stitch=True,
            width=800,
            height=600,
            wait="load",
            scroll_delay_ms=500,
            tile_overlap=100,  # 较大的重叠值
            sticky_top=50,
            sticky_bottom=50,
            headless=True
        )

        # 验证拼接效果
        session_dirs = [d for d in os.listdir(temp_output_dir) if os.path.isdir(os.path.join(temp_output_dir, d))]
        latest_session = session_dirs[-1]
        session_path = os.path.join(temp_output_dir, latest_session)

        from snap import safe_dirname
        expected_url_dirname = safe_dirname(test_page_url)
        url_dir = os.path.join(session_path, expected_url_dirname)
        stitched_path = os.path.join(url_dir, "stitched.png")

        if os.path.exists(stitched_path):
            stitched_img = Image.open(stitched_path)
            print(f"✅ 重叠拼接成功，拼接后尺寸: {stitched_img.size}")
            stitched_img.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])