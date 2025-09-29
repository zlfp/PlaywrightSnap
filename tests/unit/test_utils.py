#!/usr/bin/env python3
"""
单元测试：测试工具函数
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from snap import ts, safe_dirname, ensure_dir
import tempfile
import shutil
from datetime import datetime


class TestTimestampFunction:
    """测试时间戳函数"""

    def test_ts_format(self):
        """测试时间戳格式"""
        timestamp = ts()
        # 验证格式：YYYY-MM-DD_HH-MM-SS
        assert len(timestamp) == 19
        assert timestamp[4] == '-'
        assert timestamp[7] == '-'
        assert timestamp[10] == '_'
        assert timestamp[13] == '-'
        assert timestamp[16] == '-'

    def test_ts_changes(self):
        """测试时间戳会随时间变化"""
        timestamp1 = ts()
        import time
        time.sleep(1.1)  # 确保时间变化超过1秒
        timestamp2 = ts()
        assert timestamp1 != timestamp2


class TestSafeDirnameFunction:
    """测试安全目录名函数"""

    def test_basic_url(self):
        """测试基本URL"""
        assert safe_dirname("https://example.com") == "example.com"
        assert safe_dirname("http://test.org") == "test.org"

    def test_complex_url(self):
        """测试复杂URL"""
        assert safe_dirname("https://example.com/path/to/page") == "example.com_path_to_page"
        assert safe_dirname("http://test.org/a/b/c?query=1") == "test.org_a_b_c_query_1"

    def test_special_characters(self):
        """测试特殊字符处理"""
        assert safe_dirname("https://example.com/page with spaces") == "example.com_page_with_spaces"
        assert safe_dirname("https://test.com/$%^&*()") == "test.com_"

    def test_length_limit(self):
        """测试长度限制"""
        long_url = "https://" + "a" * 150 + ".com"
        result = safe_dirname(long_url)
        assert len(result) <= 120

    def test_empty_url(self):
        """测试空URL"""
        assert safe_dirname("") == ""
        assert safe_dirname("https://") == ""


class TestEnsureDirFunction:
    """测试目录创建函数"""

    def test_create_new_directory(self):
        """测试创建新目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "test", "nested", "directory")
            ensure_dir(new_dir)
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)

    def test_existing_directory(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = os.path.join(temp_dir, "existing")
            os.makedirs(existing_dir)
            # 应该不会抛出异常
            ensure_dir(existing_dir)
            assert os.path.exists(existing_dir)

    def test_file_exists(self):
        """测试文件已存在的情况"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "existing_file")
            with open(file_path, 'w') as f:
                f.write("test")

            # 应该会抛出异常，因为我们期望创建目录
            with pytest.raises(Exception):
                ensure_dir(file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])