#!/usr/bin/env python3
"""Test if Pillow can create valid ICNS files from multiple icon sizes using append_images."""

from PIL import Image
import os
import struct
import io


# PackBits compression - from icnsutil/PackBytes.py
def pack(data):
    """PackBits compression."""
    ret = []
    buf = []
    i = 0

    def flush_buf():
        if len(buf) > 0:
            ret.append(len(buf) - 1)
            ret.extend(buf)
            buf.clear()

    end = len(data)
    while i < end:
        arr = data[i:i + 3]
        x = arr[0]
        if len(arr) == 3 and x == arr[1] and x == arr[2]:
            flush_buf()
            c = 3
            while (i + c) < end and data[i + c] == x:
                c += 1
            i += c
            while c > 130:
                ret.append(0xFF)
                ret.append(x)
                c -= 130
            if c > 2:
                ret.append(c + 0x7D)
                ret.append(x)
            else:
                i -= c
        else:
            buf.append(x)
            if len(buf) > 127:
                flush_buf()
            i += 1
    flush_buf()
    return bytes(ret)


def create_rgba_with_mask(img):
    """Create ARGB data and mask for ICNS.
    
    Creates an image with left half opaque and right half transparent.
    Returns (argb_data, mask_data) for icns.
    """
    w, h = img.size
    pixels = list(img.getdata())
    
    # Separate channels: all A, all R, all G, all B (AARRGGBBB order)
    a_channel = []
    r_channel = []
    g_channel = []
    b_channel = []
    
    # Create mask: left half opaque (255), right half transparent (0)
    for i, (r, g, b, a) in enumerate(pixels):
        x = i % w
        if x < w // 2:
            # Left half: fully opaque
            a_channel.append(255)
        else:
            # Right half: fully transparent
            a_channel.append(0)
        r_channel.append(r)
        g_channel.append(g)
        b_channel.append(b)
    
    # Compress each channel with PackBits
    a_compressed = pack(a_channel)
    r_compressed = pack(r_channel)
    g_compressed = pack(g_channel)
    b_compressed = pack(b_channel)
    
    # ARGB format: header + A + R + G + B
    argb_data = b'ARGB' + a_compressed + r_compressed + g_compressed + b_compressed
    
    # Mask format: just alpha channel compressed
    mask_data = pack(a_channel)
    
    return argb_data, mask_data


def create_rgb24_data(img):
    """Create 24-bit RGB data in ICNS format (RRRGGGBBB channel order, PackBits compressed).
    
    This matches what icnsutil's ArgbImage.rgb_data() does.
    """
    # Convert to RGBA and extract channels
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    w, h = img.size
    pixels = list(img.getdata())
    
    # Separate channels: all R, then all G, then all B (RRRGGGBBB order)
    r_channel = []
    g_channel = []
    b_channel = []
    
    for r, g, b, a in pixels:
        r_channel.append(r)
        g_channel.append(g)
        b_channel.append(b)
    
    # Compress each channel with PackBits
    r_compressed = pack(r_channel)
    g_compressed = pack(g_channel)
    b_compressed = pack(b_channel)
    
    return r_compressed + g_compressed + b_compressed


def add_icp_blocks(icns_path, icon_sizes, colors):
    """Manually add icp4/icp5 blocks for 16/32 sizes using PackBits compressed RGB."""
    
    # Read existing ICNS
    with open(icns_path, 'rb') as f:
        data = f.read()
    
    # icp types for small sizes - use ARGB format (ic04/ic05) for alpha support
    # ic04 = 16x16 ARGB, ic05 = 32x32 ARGB
    # Fall back to icp4/icp5 if ARGB not supported
    icp_types = {
        (16, 16): b'ic04',  # ARGB
        (32, 32): b'ic05',  # ARGB
    }
    
    # Create icp blocks with PackBits compressed ARGB
    icp_blocks = b''
    for (w, h), color in zip(icon_sizes, colors):
        if (w, h) in icp_types:
            # Create image with half transparent/half opaque
            img = Image.new('RGBA', (w, h), color)
            # Create left half opaque, right half transparent
            for y in range(h):
                for x in range(w):
                    if x >= w // 2:
                        img.putpixel((x, y), (color[0], color[1], color[2], 0))
            
            argb_data, mask_data = create_rgba_with_mask(img)
            
            # Add block with ARGB format
            block_type = icp_types[(w, h)]
            block = block_type + struct.pack('>I', len(argb_data) + 8) + argb_data
            icp_blocks += block
            print(f"Added {block_type.decode()}: {w}x{h}, {len(argb_data)} bytes (ARGB with mask)")
    
    if icp_blocks:
        # Parse the ICNS
        magic = data[:4]
        file_size = int.from_bytes(data[4:8], 'big')
        
        # New file size
        new_size = file_size + len(icp_blocks)
        
        # Rebuild: header + original blocks + new icp blocks
        new_data = magic + struct.pack('>I', new_size) + data[8:] + icp_blocks
        
        with open(icns_path, 'wb') as f:
            f.write(new_data)
        
        print(f"Updated {icns_path}")
    
    return icns_path


def create_multi_size_icns_with_append(icon_sizes, colors, output_path):
    """Create ICNS file using Pillow's append_images parameter.
    
    The append_images parameter allows specifying different images for each size
    instead of Pillow auto-scaling from a single image.
    
    For retina support, provide @2x sizes (e.g., 256 for 128 display).
    """
    # Main image is the largest
    main_w, main_h = icon_sizes[0]
    main_color = colors[0]
    main_img = Image.new('RGBA', (main_w, main_h), main_color)
    
    # Append all other sizes (including retina @2x versions)
    append_images = []
    for (w, h), color in zip(icon_sizes[1:], colors[1:]):
        img = Image.new('RGBA', (w, h), color)
        append_images.append(img)
    
    # Save with append_images
    main_img.save(output_path, format='ICNS', append_images=append_images)
    
    print(f"Created {output_path}")
    
    # Add small icon blocks manually (icp4/icp5 with PackBits RGB)
    add_icp_blocks(output_path, icon_sizes, colors)
    
    return output_path


def parse_icns_structure(icns_path):
    """Parse and print ICNS file structure."""
    with open(icns_path, 'rb') as f:
        data = f.read()
    
    print("\nICNS structure:")
    pos = 8  # Skip 'icns' header
    while pos < len(data):
        block_type = data[pos:pos+4].decode('latin-1', errors='replace')
        block_size = int.from_bytes(data[pos+4:pos+8], 'big')
        
        # Try to extract PNG info
        png_data = data[pos+8:pos+block_size]
        if png_data[:4] == b'\x89PNG':
            try:
                img = Image.open(io.BytesIO(png_data))
                print(f"  {block_type}: {img.size} (PNG)")
            except:
                print(f"  {block_type}: {block_size} bytes")
        else:
            print(f"  {block_type}: {block_size} bytes")
        
        pos += block_size


def test_pillow_append_images():
    """Test Pillow's append_images for ICNS creation."""
    
    # macOS icon sizes - include 16x16 (icp4), 32x32 (icp5)
    icon_sizes = [
        (16, 16),     # icp4 - 16x16
        (32, 32),     # icp5 - 32x32  
        (128, 128),   # ic07 - 128x128
        (256, 256),   # ic08 - 256x256
        (512, 512),   # ic09 - 512x512
        (1024, 1024), # ic10 - 1024x1024
    ]
    
    # Different colors for each size
    colors = [
        (255, 0, 0, 255),     # 16 - Red
        (0, 255, 0, 255),     # 32 - Green
        (255, 255, 0, 255),   # 128 - Yellow
        (255, 0, 255, 255),   # 256 - Magenta
        (0, 255, 255, 255),   # 512 - Cyan
        (128, 128, 128, 255), # 1024 - Gray
    ]
    
    print("Testing Pillow append_images + PackBits for ICNS:")
    print(f"Sizes: {icon_sizes}")
    print(f"Colors: {[c[:3] for c in colors]}")
    
    # Create ICNS with append_images
    output_path = "test_append.icns"
    create_multi_size_icns_with_append(icon_sizes, colors, output_path)
    
    # Parse structure
    parse_icns_structure(output_path)
    
    # Get file size
    size = os.path.getsize(output_path)
    print(f"\nFile size: {size} bytes")
    
    print(f"\nPillow version: {Image.__version__}")


if __name__ == '__main__':
    test_pillow_append_images()
