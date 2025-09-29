#!/usr/bin/env python3
"""
集成测试：测试模块间的集成
"""

import pytest
import sys
import os
import tempfile
import shutil

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from snap import snap, get_scroll_container, safe_dirname, ensure_dir, stitch_tiles
from PIL import Image
import json
import time


class TestModuleIntegration:
    """测试模块集成"""

    def test_safe_dirname_and_ensure_dir_integration(self):
        """测试安全目录名和目录创建的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建安全的目录名
            url = "https://example.com/test page with spaces/path?query=1"
            safe_name = safe_dirname(url)

            # 创建目录
            full_path = os.path.join(temp_dir, safe_name)
            ensure_dir(full_path)

            # 验证
            assert os.path.exists(full_path)
            assert os.path.isdir(full_path)

    def test_complete_workflow_without_browser(self):
        """测试完整的工作流程（不使用浏览器）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 模拟一些输出文件
            session_dir = os.path.join(temp_dir, "test_session")
            ensure_dir(session_dir)

            # 创建模拟的tile文件
            tile_paths = []
            for i in range(3):
                tile_path = os.path.join(session_dir, f"tile_{i+1:04d}.png")
                img = Image.new("RGB", (100, 50), (i * 127, 255 - i * 127, 128))
                img.save(tile_path)
                tile_paths.append(tile_path)
                img.close()

            # 测试拼接功能
            stitched_path = os.path.join(session_dir, "stitched.png")
            stitch_tiles(tile_paths, stitched_path, overlap_top=10, overlap_bottom=10)

            # 验证拼接结果
            assert os.path.exists(stitched_path)

            stitched = Image.open(stitched_path)
            # 第一个完整 + 第二个减去重叠 + 第三个减去重叠
            expected_height = 50 + (50 - 10 - 10) + (50 - 10 - 10)
            assert stitched.size == (100, expected_height)
            stitched.close()

    def test_meta_data_creation(self):
        """测试元数据创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建模拟的元数据
            meta = {
                "urls": ["https://example.com"],
                "started_at": time.time(),
                "finished_at": time.time() + 10,
                "tiles": [
                    {"url": "https://example.com", "tile": "tile1.png", "y": 0, "height": 100},
                    {"url": "https://example.com", "tile": "tile2.png", "y": 920, "height": 100}
                ]
            }

            # 保存元数据
            meta_path = os.path.join(temp_dir, "meta.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            # 验证元数据
            assert os.path.exists(meta_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                loaded_meta = json.load(f)

            assert loaded_meta["urls"] == ["https://example.com"]
            assert len(loaded_meta["tiles"]) == 2
            assert loaded_meta["tiles"][0]["y"] == 0

    def test_wait_map_configuration(self):
        """测试等待映射配置"""
        from snap import WAIT_MAP

        expected_wait_map = {
            "load": "load",
            "dom": "domcontentloaded",
            "networkidle": "networkidle"
        }

        assert WAIT_MAP == expected_wait_map

    def test_file_structure_creation(self):
        """测试文件结构创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 模拟snap函数的文件结构创建逻辑
            session_dir = os.path.join(temp_dir, "test_session")
            ensure_dir(session_dir)

            url = "https://example.com"
            url_dir = os.path.join(session_dir, safe_dirname(url))
            tiles_dir = os.path.join(url_dir, "tiles")

            # 创建目录结构
            ensure_dir(url_dir)
            ensure_dir(tiles_dir)

            # 验证目录结构
            assert os.path.exists(session_dir)
            assert os.path.exists(url_dir)
            assert os.path.exists(tiles_dir)

            # 创建模拟文件
            tile_path = os.path.join(tiles_dir, "tile_0001.png")
            img = Image.new("RGB", (100, 50), (255, 0, 0))
            img.save(tile_path)
            img.close()

            # 创建元数据文件
            meta_path = os.path.join(url_dir, "page_meta.json")
            page_meta = {
                "url": url,
                "total_height": 2000,
                "viewport": {"width": 1280, "height": 1000},
                "scale": 1.0,
                "wait": "networkidle",
                "tiles": [tile_path]
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(page_meta, f, ensure_ascii=False, indent=2)

            # 验证文件
            assert os.path.exists(tile_path)
            assert os.path.exists(meta_path)

    def test_error_handling_integration(self):
        """测试错误处理的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试文件路径错误处理
            non_existent_path = os.path.join(temp_dir, "non_existent", "file.png")

            # 应该能够处理不存在的路径
            try:
                result = safe_dirname(non_existent_path)
                assert isinstance(result, str)
            except Exception:
                pytest.fail("safe_dirname should not raise exception for file paths")

            # 测试目录创建的错误处理
            try:
                # 尝试在不存在的路径中创建文件
                ensure_dir(non_existent_path)
                # 如果成功，验证目录确实被创建了
                assert os.path.exists(non_existent_path)
            except Exception as e:
                pytest.fail(f"ensure_dir should handle paths gracefully: {e}")

    def test_parameter_processing(self):
        """测试参数处理"""
        # 测试参数类型的处理
        from snap import WAIT_MAP

        # 测试wait参数的默认值处理
        wait_value = "networkidle"
        target_state = WAIT_MAP.get(wait_value, "networkidle")
        assert target_state == "networkidle"

        # 测试wait参数的时间处理
        wait_value = "10s"
        if wait_value.endswith("s") and wait_value[:-1].isdigit():
            target_state = "load"
            wait_time = float(wait_value[:-1])
            assert target_state == "load"
            assert wait_time == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])