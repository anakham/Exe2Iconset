#!/usr/bin/env python3
"""Test if Pillow can create valid ICNS files from multiple icon sizes."""

from PIL import Image
import struct
import os

ICNS_BLOCK_TYPES = {
    (16, 16): b'icp4',
    (32, 32): b'icp5',
    (64, 64): b'icp6',
    (128, 128): b'ic07',
    (256, 256): b'ic08',
    (512, 512): b'ic09',
    (1024, 1024): b'ic10',
}

def create_multi_size_icns(icon_sizes, colors, output_path):
    """Create ICNS file with multiple icon sizes and colors."""
    
    blocks = b''
    iconset_path = "/tmp/test.iconset"
    os.makedirs(iconset_path, exist_ok=True)
    
    for (w, h), color in zip(icon_sizes, colors):
        img = Image.new('RGBA', (w, h), color)
        
        # Save as PNG
        png_path = os.path.join(iconset_path, f"icon_{w}x{h}.png")
        img.save(png_path, 'PNG')
        
        # Read PNG data
        with open(png_path, 'rb') as f:
            png_data = f.read()
        
        block_type = ICNS_BLOCK_TYPES.get((w, h), b'ic08')
        block = block_type + struct.pack('>I', len(png_data) + 8) + png_data
        blocks += block
    
    # Build ICNS file
    icns_data = b'icns' + struct.pack('>I', 8 + len(blocks)) + blocks
    
    with open(output_path, 'wb') as f:
        f.write(icns_data)
    
    # Cleanup
    import shutil
    shutil.rmtree(iconset_path)
    
    return icns_data

def test_pillow_icns_write():
    """Test Pillow's ICNS write capability with multiple sizes."""
    
    # Standard macOS icon sizes
    icon_sizes = [
        (16, 16), (32, 32), (64, 64), (128, 128),
        (256, 256), (512, 512), (1024, 1024),
    ]
    
    # Different colors for each size to verify each size is included
    colors = [
        (255, 0, 0, 255),    # 16 - Red
        (0, 255, 0, 255),    # 32 - Green
        (0, 0, 255, 255),    # 64 - Blue
        (255, 255, 0, 255),  # 128 - Yellow
        (255, 0, 255, 255),  # 256 - Magenta
        (0, 255, 255, 255),  # 512 - Cyan
        (128, 128, 128, 255), # 1024 - Gray
    ]
    
    for (width, height), color in zip(icon_sizes, colors):
        print(f"Created: icon_{width}x{height}.png (RGB{tuple(color[:3])})")
    
    # Test 1: Create multi-size ICNS with different colors
    print("\n--- Test 1: Multi-size ICNS (manual construction) ---")
    try:
        icns_data = create_multi_size_icns(icon_sizes, colors, "/tmp/test_multicolor.icns")
        print(f"SUCCESS: {len(icns_data)} bytes")
        
        # Parse and verify structure
        print("ICNS structure:")
        pos = 8
        while pos < len(icns_data):
            block_type = icns_data[pos:pos+4].decode()
            block_size = int.from_bytes(icns_data[pos+4:pos+8], 'big')
            print(f"  Block: {block_type} size={block_size}")
            pos += block_size
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 2: Pillow single-image ICNS (scaled)
    print("\n--- Test 2: Pillow single-image ICNS ---")
    try:
        img = Image.new('RGBA', (256, 256), (255, 0, 255, 255))
        img.save("/tmp/test_single.icns", format='ICNS')
        
        with open('/tmp/test_single.icns', 'rb') as f:
            data = f.read()
        
        print(f"SUCCESS: {len(data)} bytes")
        print("Note: Pillow scales single image to all sizes internally")
        
        pos = 8
        while pos < len(data):
            block_type = data[pos:pos+4].decode()
            block_size = int.from_bytes(data[pos+4:pos+8], 'big')
            print(f"  Block: {block_type} size={block_size}")
            pos += block_size
    except Exception as e:
        print(f"FAILED: {e}")
    
    print(f"\nPillow version: {Image.__version__}")

if __name__ == '__main__':
    test_pillow_icns_write()
