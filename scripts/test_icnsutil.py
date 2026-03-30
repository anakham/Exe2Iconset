#!/usr/bin/env python3
"""Test icnsutil for creating multi-size ICNS with different colors."""

from PIL import Image
import icnsutil
from icnsutil.ArgbImage import ArgbImage
import io
import os

def test_icnsutil():
    """Test icnsutil ICNS creation with different colors."""
    
    # icp4, icp5 support RGB format (PackBits compressed)
    # ic07-ic14 are PNG formats
    # Each type has FIXED display size - we must provide PNG at exactly that size!
    icon_configs = [
        # Small icons - use RGB format (PackBits compressed)
        (16, 16, 'icp4', 'rgb'),      # icp4 = 16x16 display
        (32, 32, 'icp5', 'rgb'),      # icp5 = 32x32 display
        # Main icons - use PNG
        (128, 128, 'ic07', 'png'),    # ic07 = 128x128 display
        (256, 256, 'ic08', 'png'),    # ic08 = 256x256 display
        (512, 512, 'ic09', 'png'),    # ic09 = 512x512 display
        (1024, 1024, 'ic10', 'png'),   # ic10 = 1024x1024 display
        # Retina: stored at 2x, displayed at 1x - use PNG
        (256, 256, 'ic13', 'png'),    # ic13 = 256 display (stored 512)
        (512, 512, 'ic14', 'png'),     # ic14 = 512 display (stored 1024)
    ]
    
    # Different colors for each icns type
    colors = [
        (255, 0, 0, 255),       # icp4 (16x16) - Red
        (0, 255, 0, 255),       # icp5 (32x32) - Green
        (255, 255, 0, 255),     # ic07 (128x128) - Yellow
        (255, 0, 255, 255),     # ic08 (256x256) - Magenta
        (0, 255, 255, 255),     # ic09 (512x512) - Cyan
        (128, 128, 128, 255),   # ic10 (1024x1024) - Gray
        (255, 128, 0, 255),     # ic13 (256 display) - Orange
        (0, 128, 255, 255),     # ic14 (512 display) - Sky Blue
    ]
    
    print("--- Creating ICNS with icnsutil ---")
    
    icns = icnsutil.IcnsFile()
    
    for (w, h, icns_type, fmt), color in zip(icon_configs, colors):
        img = Image.new('RGBA', (w, h), color)
        
        if fmt == 'rgb':
            # Use ArgbImage for RGB format (PackBits compressed)
            argb_img = ArgbImage(image=img)
            data = argb_img.rgb_data(compress=True)
            print(f"Added: {w}x{h} as {icns_type} (RGB, {len(data)} bytes) - RGBA{tuple(color[:3])}")
        else:
            # Use PNG format
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            data = buf.getvalue()
            print(f"Added: {w}x{h} as {icns_type} (PNG, {len(data)} bytes) - RGBA{tuple(color[:3])}")
        
        icns.add_media(data=data, key=icns_type)
    
    # Write ICNS file
    icns_path = 'test_icnsutil.icns'
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
