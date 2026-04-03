"""Tests for icon conversion."""
import os
import tempfile


def test_convert_icons_to_icns_sizes():
    """Test icon size conversion."""
    from PIL import Image
    from exe2iconset.core.convert import convert_icons_to_icns_sizes
    
    test_img = Image.new('RGBA', (256, 256), (255, 0, 0, 255))
    icon_data = [{'width': 256, 'height': 256, 'image': test_img}]
    
    mac_icon_sizes = [(16, 16), (128, 128), (256, 256)]
    result = convert_icons_to_icns_sizes(icon_data, mac_icon_sizes)
    
    assert isinstance(result, dict)
    assert (256, 256) in result
    assert (128, 128) in result
    assert (16, 16) in result


def test_convert_icons_empty_list():
    """Test with empty icon list."""
    from exe2iconset.core.convert import convert_icons_to_icns_sizes
    
    result = convert_icons_to_icns_sizes([], [(128, 128)])
    assert result == {}


def test_save_iconset():
    """Test saving iconset directory."""
    from PIL import Image
    from exe2iconset.core.convert import save_iconset
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img = Image.new('RGBA', (128, 128), (0, 255, 0, 255))
        icon_images = {(128, 128): test_img}
        
        iconset_path = os.path.join(tmpdir, "test.iconset")
        result = save_iconset(icon_images, iconset_path)
        
        assert result is True
        assert os.path.exists(iconset_path)
        assert os.path.exists(os.path.join(iconset_path, "icon_128x128.png"))


def test_save_iconset_empty():
    """Test saving empty iconset."""
    from exe2iconset.core.convert import save_iconset
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = save_iconset({}, tmpdir)
        assert os.path.exists(tmpdir)


if __name__ == "__main__":
    test_convert_icons_to_icns_sizes()
    print("test_convert_icons_to_icns_sizes PASSED")
    test_convert_icons_empty_list()
    print("test_convert_icons_empty_list PASSED")
    test_save_iconset()
    print("test_save_iconset PASSED")
    test_save_iconset_empty()
    print("test_save_iconset_empty PASSED")
    print("All tests passed!")
