try:
    import pytest
except ImportError:
    pytest = None

from exe2iconset import ICON_TYPE_MAP, pack_bits_compress


def test_icon_type_map():
    """Test that ICON_TYPE_MAP has expected icon sizes."""
    assert (16, 16) in ICON_TYPE_MAP
    assert (32, 32) in ICON_TYPE_MAP
    assert (128, 128) in ICON_TYPE_MAP
    assert (256, 256) in ICON_TYPE_MAP
    assert (512, 512) in ICON_TYPE_MAP
    assert (1024, 1024) in ICON_TYPE_MAP


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


if __name__ == "__main__":
    test_icon_type_map()
    print("test_icon_type_map PASSED")
    test_pack_bits_compress()
    print("test_pack_bits_compress PASSED")
    test_pack_bits_compress_repeated()
    print("test_pack_bits_compress_repeated PASSED")
    print("All tests passed!")
