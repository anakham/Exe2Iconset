"""Tests for icon extraction from PE files."""
import os


def test_extract_icons_from_pe_no_file():
    """Test extraction with non-existent file."""
    from exe2iconset.core.extract import extract_icons_from_pe
    
    result = extract_icons_from_pe("/nonexistent/file.exe")
    assert result == {}


def test_extract_icons_from_pe_invalid():
    """Test extraction with invalid file."""
    import tempfile
    from exe2iconset.core.extract import extract_icons_from_pe
    
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
        f.write(b"NOT A VALID PE FILE")
        temp_path = f.name
    
    try:
        result = extract_icons_from_pe(temp_path)
        # May return empty or raise exception
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_get_icon_groups():
    """Test get_icon_groups wrapper function."""
    from exe2iconset.core.convert import get_icon_groups
    
    result = get_icon_groups("/nonexistent/file.exe")
    assert result == {}


if __name__ == "__main__":
    test_extract_icons_from_pe_no_file()
    print("test_extract_icons_from_pe_no_file PASSED")
    test_extract_icons_from_pe_invalid()
    print("test_extract_icons_from_pe_invalid PASSED")
    test_get_icon_groups()
    print("test_get_icon_groups PASSED")
    print("All tests passed!")
