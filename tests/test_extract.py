"""Tests for icon extraction from PE files."""
import os
import tempfile
import pytest
from exe2iconset.core.extract import extract_icons_from_pe
from exe2iconset.core.convert import get_icon_groups


def test_extract_icons_from_pe_no_file():
    """Test extraction with non-existent file."""
    result = extract_icons_from_pe("/nonexistent/file.exe")
    assert result == {}


def test_extract_icons_from_pe_invalid():
    """Test extraction with invalid file."""
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
        f.write(b"NOT A VALID PE FILE")
        temp_path = f.name
    
    try:
        result = extract_icons_from_pe(temp_path)
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_get_icon_groups():
    """Test get_icon_groups wrapper function."""
    result = get_icon_groups("/nonexistent/file.exe")
    assert result == {}


def test_extract_icons_pe_without_resources(tmp_path):
    """Test extraction from PE file without icon resources."""
    # Create a minimal PE-like file with no resources
    # This simulates a PE file that has valid header but no icon resources
    minimal_pe = tmp_path / "minimal.exe"
    minimal_pe.write_bytes(b"MZ" + b"\x00" * 100)
    
    result = extract_icons_from_pe(str(minimal_pe))
    assert isinstance(result, dict)