"""Pytest configuration and fixtures."""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_image():
    """Create a sample RGBA image for testing."""
    from PIL import Image
    return Image.new('RGBA', (128, 128), (255, 0, 0, 255))


@pytest.fixture
def sample_icon_list(sample_image):
    """Create a sample icon list for testing."""
    return [
        {'width': 128, 'height': 128, 'image': sample_image},
        {'width': 64, 'height': 64, 'image': sample_image.copy()},
        {'width': 32, 'height': 32, 'image': sample_image.copy()},
    ]


@pytest.fixture
def tmp_iconset(tmp_path):
    """Create a temporary iconset directory."""
    iconset_path = tmp_path / "test.iconset"
    iconset_path.mkdir()
    return iconset_path
