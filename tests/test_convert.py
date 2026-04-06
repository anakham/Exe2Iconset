"""Tests for icon conversion functionality."""
import os
import pytest
from PIL import Image
from exe2iconset.core.convert import (
    convert_icons_to_icns_sizes,
    save_iconset,
)
from exe2iconset import ICON_TYPE_MAP


def test_convert_icons_to_icns_sizes(sample_icon_list):
    """Test icon size conversion."""
    mac_icon_sizes = [(16, 16), (128, 128), (256, 256)]
    result = convert_icons_to_icns_sizes(sample_icon_list, mac_icon_sizes)
    
    assert isinstance(result, dict)
    assert (256, 256) in result
    assert (128, 128) in result
    assert (16, 16) in result


def test_convert_icons_empty_list():
    """Test with empty icon list."""
    result = convert_icons_to_icns_sizes([], [(128, 128)])
    assert result == {}


def test_convert_icons_all_sizes(sample_image):
    """Test conversion to all ICNS sizes."""
    icon_data = [{'width': 512, 'height': 512, 'image': sample_image}]
    mac_icon_sizes = list(ICON_TYPE_MAP.keys())
    
    result = convert_icons_to_icns_sizes(icon_data, mac_icon_sizes)
    
    assert len(result) > 0


def test_save_iconset(sample_icon_list, tmp_path):
    """Test saving iconset directory."""
    entry = sample_icon_list[0]
    icon_images = {(entry['width'], entry['height']): entry['image']}
    iconset_path = tmp_path / "test.iconset"
    
    result = save_iconset(icon_images, str(iconset_path))
    
    assert result is True
    assert iconset_path.exists()
    assert (iconset_path / "icon_256x256.png").exists()


def test_save_iconset_empty(tmp_path):
    """Test saving empty iconset."""
    result = save_iconset({}, str(tmp_path / "empty"))
    assert os.path.exists(tmp_path / "empty")


def test_save_iconset_multiple_sizes(sample_icon_list, tmp_path):
    """Test saving iconset with multiple sizes."""
    icon_images = {(entry['width'], entry['height']): entry['image'] for entry in sample_icon_list}
    iconset_path = tmp_path / "multi.iconset"
    
    result = save_iconset(icon_images, str(iconset_path))
    
    assert result is True
    assert (iconset_path / "icon_256x256.png").exists()
    assert (iconset_path / "icon_128x128.png").exists()
    assert (iconset_path / "icon_64x64.png").exists()
    assert (iconset_path / "icon_32x32.png").exists()