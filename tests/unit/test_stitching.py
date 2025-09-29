#!/usr/bin/env python3
"""
单元测试：测试图片拼接功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from snap import stitch_tiles
from PIL import Image
import tempfile
import shutil


def create_test_image(width, height, color=(255, 255, 255)):
    """创建测试图片"""
    image = Image.new("RGB", (width, height), color)
    return image


class TestStitchTilesFunction:
    """测试图片拼接函数"""

    def test_stitch_two_identical_tiles(self):
        """测试拼接两个相同的图片"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试图片
            tile1_path = os.path.join(temp_dir, "tile1.png")
            tile2_path = os.path.join(temp_dir, "tile2.png")
            output_path = os.path.join(temp_dir, "stitched.png")

            # 创建两个100x50的红色图片
            tile1 = create_test_image(100, 50, (255, 0, 0))
            tile2 = create_test_image(100, 50, (255, 0, 0))

            tile1.save(tile1_path)
            tile2.save(tile2_path)

            # 拼接
            stitch_tiles([tile1_path, tile2_path], output_path)

            # 验证结果
            assert os.path.exists(output_path)

            stitched = Image.open(output_path)
            assert stitched.size == (100, 100)  # 宽度不变，高度相加
            assert stitched.mode == "RGB"

            tile1.close()
            tile2.close()
            stitched.close()

    def test_stitch_with_overlap(self):
        """测试带重叠的拼接"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试图片
            tile1_path = os.path.join(temp_dir, "tile1.png")
            tile2_path = os.path.join(temp_dir, "tile2.png")
            output_path = os.path.join(temp_dir, "stitched.png")

            # 创建两个100x100的图片，重叠20像素
            tile1 = create_test_image(100, 100, (255, 0, 0))  # 红色
            tile2 = create_test_image(100, 100, (0, 255, 0))  # 绿色

            tile1.save(tile1_path)
            tile2.save(tile2_path)

            # 拼接，重叠20像素
            stitch_tiles([tile1_path, tile2_path], output_path, overlap_top=20, overlap_bottom=20)

            # 验证结果
            assert os.path.exists(output_path)

            stitched = Image.open(output_path)
            expected_height = 100 + (100 - 20 - 20)  # 第一个完整 + 第二个减去重叠
            assert stitched.size == (100, expected_height)

            tile1.close()
            tile2.close()
            stitched.close()

    def test_stitch_different_widths(self):
        """测试拼接不同宽度的图片"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试图片
            tile1_path = os.path.join(temp_dir, "tile1.png")
            tile2_path = os.path.join(temp_dir, "tile2.png")
            output_path = os.path.join(temp_dir, "stitched.png")

            # 创建不同宽度的图片
            tile1 = create_test_image(100, 50, (255, 0, 0))   # 100x50
            tile2 = create_test_image(150, 50, (0, 255, 0))   # 150x50

            tile1.save(tile1_path)
            tile2.save(tile2_path)

            # 拼接
            stitch_tiles([tile1_path, tile2_path], output_path)

            # 验证结果
            assert os.path.exists(output_path)

            stitched = Image.open(output_path)
            assert stitched.size == (150, 100)  # 宽度取最大值，高度相加

            tile1.close()
            tile2.close()
            stitched.close()

    def test_stitch_single_tile(self):
        """测试拼接单个图片"""
        with tempfile.TemporaryDirectory() as temp_dir:
            tile_path = os.path.join(temp_dir, "tile1.png")
            output_path = os.path.join(temp_dir, "stitched.png")

            # 创建单个图片
            tile = create_test_image(100, 50, (255, 0, 0))
            tile.save(tile_path)

            # 拼接
            stitch_tiles([tile_path], output_path)

            # 验证结果
            assert os.path.exists(output_path)

            stitched = Image.open(output_path)
            assert stitched.size == (100, 50)

            tile.close()
            stitched.close()

    def test_stitch_empty_list(self):
        """测试空列表拼接"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "stitched.png")

            # 应该抛出异常
            with pytest.raises(RuntimeError, match="No tiles to stitch"):
                stitch_tiles([], output_path)

    def test_stitch_multiple_tiles_with_overlap(self):
        """测试多个图片带重叠拼接"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试图片
            tile_paths = []
            output_path = os.path.join(temp_dir, "stitched.png")

            # 创建3个100x100的图片
            for i in range(3):
                tile_path = os.path.join(temp_dir, f"tile{i+1}.png")
                tile = create_test_image(100, 100, (i * 127, 255 - i * 127, 128))
                tile.save(tile_path)
                tile_paths.append(tile_path)
                tile.close()

            # 拼接，重叠10像素
            stitch_tiles(tile_paths, output_path, overlap_top=10, overlap_bottom=10)

            # 验证结果
            assert os.path.exists(output_path)

            stitched = Image.open(output_path)
            # 第一个完整 + 第二个减去上下重叠 + 第三个减去上下重叠
            expected_height = 100 + (100 - 10 - 10) + (100 - 10 - 10)
            assert stitched.size == (100, expected_height)

            stitched.close()

    def test_stitch_overlap_calculation_edge_cases(self):
        """测试重叠计算的边界情况"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试图片
            tile1_path = os.path.join(temp_dir, "tile1.png")
            tile2_path = os.path.join(temp_dir, "tile2.png")
            output_path = os.path.join(temp_dir, "stitched.png")

            # 创建小图片
            tile1 = create_test_image(50, 30, (255, 0, 0))
            tile2 = create_test_image(50, 30, (0, 255, 0))

            tile1.save(tile1_path)
            tile2.save(tile2_path)

            # 测试大重叠值（大于图片高度）
            stitch_tiles([tile1_path, tile2_path], output_path, overlap_top=15, overlap_bottom=15)

            # 验证结果
            assert os.path.exists(output_path)

            stitched = Image.open(output_path)
            # 重叠值会被限制，确保不会出现负高度
            assert stitched.size[1] > 0
            assert stitched.size[0] == 50

            tile1.close()
            tile2.close()
            stitched.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])