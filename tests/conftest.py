"""Pytest configuration and fixtures for exe2iconset tests."""
import pytest
from PIL import Image


@pytest.fixture
def make_image():
    """Factory fixture that creates RGBA images with custom size and color."""
    def _make(size=(256, 256), color=(255, 0, 0, 255)):
        return Image.new('RGBA', size, color)
    return _make


@pytest.fixture
def sample_image(make_image):
    """Create a sample red RGBA image for testing (256x256)."""
    return make_image()


@pytest.fixture
def sample_icon_list(make_image):
    """Create a sample icon list with different colored images for each size."""
    sizes = [(256, 256), (128, 128), (64, 64), (32, 32)]
    colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
    return [
        {'width': w, 'height': h, 'image': make_image((w, h), c)}
        for (w, h), c in zip(sizes, colors)
    ]