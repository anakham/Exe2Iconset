import struct
import io


def pack_bits_compress(data):
    """PackBits compression for bytes."""
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


ICON_TYPE_MAP = {
    (16, 16): (b'ic04', 'ARGB'),
    (32, 32): (b'ic05', 'ARGB'),
    (48, 48): (b'icp6', 'PNG'),
    (64, 64): (b'ic12', 'PNG'),
    (128, 128): (b'ic07', 'PNG'),
    (256, 256): (b'ic08', 'PNG'),
    (512, 512): (b'ic09', 'PNG'),
    (1024, 1024): (b'ic10', 'PNG'),
}


def create_icns_from_images(icon_images, icns_path):
    """Create ICNS file directly from resized images.
    
    Args:
        icon_images: dict of {(width, height): Image.Image} for each target size
        icns_path: output path for ICNS file
    
    Returns:
        True if successful
    """
    blocks = []
    
    for (disp_w, disp_h), img in icon_images.items():
        if not img:
            continue
        
        icon_info = ICON_TYPE_MAP.get((disp_w, disp_h))
        if not icon_info:
            continue
        
        icon_type, icon_format = icon_info
        
        if icon_format == 'ARGB':
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            pixels = list(img.getdata())
            a_channel = []
            r_channel = []
            g_channel = []
            b_channel = []
            
            for r, g, b, a in pixels:
                a_channel.append(a)
                r_channel.append(r)
                g_channel.append(g)
                b_channel.append(b)
            
            a_compressed = pack_bits_compress(bytes(a_channel))
            r_compressed = pack_bits_compress(bytes(r_channel))
            g_compressed = pack_bits_compress(bytes(g_channel))
            b_compressed = pack_bits_compress(bytes(b_channel))
            
            block_data = b'ARGB' + a_compressed + r_compressed + g_compressed + b_compressed
        else:
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            block_data = buf.getvalue()
        
        block = icon_type + struct.pack('>I', len(block_data) + 8) + block_data
        blocks.append((icon_type, block))
    
    if not blocks:
        return False
    
    blocks.sort(key=lambda x: x[0])
    
    blocks_data = b''.join(block for _, block in blocks)
    total_size = 8 + len(blocks_data)
    icns_data = b'icns' + struct.pack('>I', total_size) + blocks_data
    
    with open(icns_path, 'wb') as f:
        f.write(icns_data)
    
    return True
