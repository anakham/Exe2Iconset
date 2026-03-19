#!/usr/bin/env python3
"""Test if Pillow can create valid ICNS files from multiple icon sizes."""

from PIL import Image
from io import BytesIO
import os

def test_pillow_icns_write():
    """Test Pillow's ICNS write capability with multiple sizes."""
    
    # Standard macOS icon sizes
    icon_sizes = [
        (16, 16), (32, 32), (64, 64), (128, 128),
        (256, 256), (512, 512), (1024, 1024),
    ]
    
    # Create iconset directory
    iconset_path = "/tmp/test.iconset"
    os.makedirs(iconset_path, exist_ok=True)
    
    for width, height in icon_sizes:
        img = Image.new('RGBA', (width, height), (255, 0, 0, 255))
        png_path = os.path.join(iconset_path, f"icon_{width}x{height}.png")
        img.save(png_path, 'PNG')
        print(f"Created: icon_{width}x{height}.png")
    
    # Test 1: Direct ICNS save
    print("\n--- Test 1: Pillow direct ICNS ---")
    try:
        img = Image.open(os.path.join(iconset_path, "icon_256x256.png"))
        img.save("/tmp/test.icns", format='ICNS')
        print(f"SUCCESS: {os.path.getsize('/tmp/test.icns')} bytes")
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 2: Save from iconset
    print("\n--- Test 2: From iconset ---")
    # Create minimal ICNS manually
    try:
        # ICNS header + ic08 (256x256 PNG) block
        img = Image.open(os.path.join(iconset_path, "icon_256x256.png"))
        buf = BytesIO()
        img.save(buf, format='PNG')
        png_data = buf.getvalue()
        
        # Build ICNS file manually
        icns_data = b'icns'  # magic
        icns_data += (8 + 8 + len(png_data)).to_bytes(4, 'big')  # file size
        icns_data += b'ic08'  # 256x256 PNG block type
        icns_data += (8 + len(png_data)).to_bytes(4, 'big')  # block size
        icns_data += png_data
        
        with open("/tmp/test_manual.icns", "wb") as f:
            f.write(icns_data)
        print(f"SUCCESS (manual): {len(icns_data)} bytes")
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Cleanup
    import shutil
    shutil.rmtree(iconset_path)
    
    print(f"\nPillow version: {Image.__version__}")

if __name__ == '__main__':
    test_pillow_icns_write()
