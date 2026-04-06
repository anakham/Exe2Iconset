"""Tests for ICNS creation functionality."""
import pytest
from PIL import Image
from exe2iconset import ICON_TYPE_MAP, pack_bits_compress, create_icns_from_images


def test_pack_bits_compress():
    """Test PackBits compression basic functionality."""
    data = b'\x00\x00\x00\x00\x00\x00\x00\x00'
    result = pack_bits_compress(data)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_pack_bits_compress_repeated():
    """Test PackBits compression with repeated bytes."""
    data = b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa'
    result = pack_bits_compress(data)
    assert isinstance(result, bytes)


def test_pack_bits_compress_all_sizes(sample_image):
    """Test PackBits compression works for all ICNS sizes."""
    for size, (icon_type, icon_format) in ICON_TYPE_MAP.items():
        img = sample_image.resize(size, Image.Resampling.LANCZOS)
        if icon_format == 'ARGB':
            # Test ARGB channel compression
            pixels = list(img.get_flattened_data())
            r_channel = [p[0] for p in pixels]
            compressed = pack_bits_compress(bytes(r_channel))
            assert isinstance(compressed, bytes)


def test_icon_type_map_sizes():
    """Test that ICON_TYPE_MAP contains expected sizes."""
    expected_sizes = {(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), 
                      (256, 256), (512, 512), (1024, 1024)}
    assert set(ICON_TYPE_MAP.keys()) == expected_sizes


def test_create_icns_from_images(sample_icon_list, tmp_path):
    """Test ICNS file creation with various image sizes."""
    icon_images = {(entry['width'], entry['height']): entry['image'] for entry in sample_icon_list}
    icns_path = tmp_path / "test.icns"
    
    result = create_icns_from_images(icon_images, str(icns_path))
    
    assert result is True
    assert icns_path.exists()
    assert icns_path.stat().st_size > 0


def test_create_icns_from_images_empty(tmp_path):
    """Test ICNS creation with empty dict returns False."""
    icns_path = tmp_path / "empty.icns"
    
    result = create_icns_from_images({}, str(icns_path))
    
    assert result is False
    assert not icns_path.exists()