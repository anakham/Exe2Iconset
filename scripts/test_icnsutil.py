#!/usr/bin/env python3
"""Test icnsutil for creating multi-size ICNS with different colors."""

from PIL import Image
import icnsutil
import io
import os

def test_icnsutil():
    """Test icnsutil ICNS creation with different colors."""
    
    # Standard macOS icon sizes and their ICNS types
    icon_configs = [
        (16, 16, 'icp4'),      # 16px
        (32, 32, 'icp5'),      # 32px
        (64, 64, 'icp6'),      # 64px
        (128, 128, 'ic07'),    # 128px
        (256, 256, 'ic08'),    # 256px (or @2x for 512px stored)
        (512, 512, 'ic09'),    # 512px (or @2x for 1024px stored)
        (1024, 1024, 'ic10'),  # 1024px (or @2x for 2048px stored)
    ]
    
    # Different colors for each size
    colors = [
        (255, 0, 0, 255),       # 16 - Red
        (0, 255, 0, 255),       # 32 - Green
        (0, 0, 255, 255),       # 64 - Blue
        (255, 255, 0, 255),     # 128 - Yellow
        (255, 0, 255, 255),     # 256 - Magenta
        (0, 255, 255, 255),     # 512 - Cyan
        (128, 128, 128, 255),   # 1024 - Gray
    ]
    
    print("--- Creating ICNS with icnsutil ---")
    
    icns = icnsutil.IcnsFile()
    
    for (w, h, icns_type), color in zip(icon_configs, colors):
        img = Image.new('RGBA', (w, h), color)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        png_data = buf.getvalue()
        
        icns.add_media(data=png_data, key=icns_type)
        print(f"Added: {w}x{h} as {icns_type} (RGBA{tuple(color[:3])})")
    
    # Write ICNS file
    icns_path = '/tmp/test_icnsutil.icns'
    icns.write(icns_path)
    
    print(f"\nCreated: {icns_path}")
    print(f"Size: {os.path.getsize(icns_path)} bytes")
    
    # Verify
    print("\n--- Verifying ---")
    icns_verify = icnsutil.IcnsFile(icns_path)
    for type_code in icns_verify.media:
        data = icns_verify.media[type_code]
        print(f"  {type_code}: {len(data)} bytes")

if __name__ == '__main__':
    test_icnsutil()
