import struct
import io
from io import BytesIO
from PIL import Image, ImageOps

try:
    import pefile
except ImportError:
    pefile = None


def _extract_resources_by_type(pe, resource_type_id, logger=None):
    """Extract all resources of a specific type with proper recursion."""
    results = []
    
    def log(msg):
        if logger:
            logger(msg)
    
    if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        return results
    
    resource_type_name = pefile.RESOURCE_TYPE.get(resource_type_id, f"UNKNOWN_{resource_type_id}")
    
    for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if entry.id == resource_type_id:
            log(f"Debug: Found {resource_type_name} (ID={resource_type_id})")
            
            if hasattr(entry, 'directory') and entry.directory:
                for sub_entry in entry.directory.entries:
                    sub_id = sub_entry.id if sub_entry.id else 0
                    sub_name = sub_entry.name if sub_entry.name else None
                    
                    log(f"Debug:   Resource ID={sub_id}, name={sub_name}")
                    
                    if hasattr(sub_entry, 'directory') and sub_entry.directory:
                        for lang_entry in sub_entry.directory.entries:
                            lang_id = lang_entry.id if lang_entry.id else 0
                            
                            if hasattr(lang_entry, 'data') and lang_entry.data:
                                offset = lang_entry.data.struct.OffsetToData
                                size = lang_entry.data.struct.Size
                                results.append({
                                    'id': sub_id,
                                    'name': sub_name,
                                    'lang': lang_id,
                                    'offset': offset,
                                    'size': size
                                })
    
    return results


def _fix_dib_data(data):
    """Fix DIB (BMP) data from RT_ICON resources for proper PIL loading."""
    if len(data) < 4:
        return data
    
    header_size = int.from_bytes(data[0:4], 'little')
    if header_size != 40:
        return data
    
    biHeight = int.from_bytes(data[8:12], 'little', signed=True)
    if biHeight < 0:
        return data
    
    biWidth = int.from_bytes(data[4:8], 'little', signed=True)
    if biWidth <= 0:
        return data
    
    biBitCount = int.from_bytes(data[14:16], 'little')
    
    if biBitCount == 32:
        actual_height = biHeight // 2
        pixel_data = data[40:40 + biWidth * actual_height * 4]
        ba = bytearray(pixel_data)
        for i in range(0, len(ba), 4):
            ba[i], ba[i+2] = ba[i+2], ba[i]
        
        img = Image.frombytes('RGBA', (biWidth, actual_height), bytes(ba), 'raw')
        img = ImageOps.flip(img)
        buf = BytesIO()
        img.save(buf, 'PNG')
        return buf.getvalue()
    
    fixed_data = bytearray(data)
    struct.pack_into('<i', fixed_data, 8, biHeight // 2)
    return bytes(fixed_data)


def _read_icon_image(pe, offset, size):
    """Read icon image from PE file and return RGBA PIL Image.
    
    Args:
        pe: pefile.PE object
        offset: offset to icon data in memory-mapped image
        size: size of icon data
        
    Returns:
        PIL Image in RGBA format, or None if extraction fails
    """
    raw_data = pe.get_memory_mapped_image()[offset:offset+size]
    fixed_data = _fix_dib_data(raw_data)
    
    try:
        img = Image.open(BytesIO(fixed_data))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        return img
    except Exception:
        return None


def extract_icons_from_pe(file_path, logger=None):
    """Extract icon groups from PE resources using pefile.
    
    Args:
        file_path: Path to PE file (exe, dll, mun)
        logger: Optional callable for logging messages
        
    Returns:
        Dict mapping group keys to list of icon dicts with 'width', 'height', 'image'
    """
    def log(msg):
        if logger:
            logger(msg)
    
    try:
        if pefile is None:
            log("pefile library not available")
            return {}

        pe = pefile.PE(file_path)

        if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            log("No resource directory found in PE file")
            return {}

        log("Debug: Starting resource directory traversal...")
        log(f"Debug: Root resource entries: {len(pe.DIRECTORY_ENTRY_RESOURCE.entries)}")
        
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            log(f"Debug: Root entry id={entry.id}, name={entry.name}")

        icon_by_id = {}
        groups = {}

        rt_icon_resources = _extract_resources_by_type(pe, pefile.RESOURCE_TYPE['RT_ICON'], logger)
        log(f"Debug: Found {len(rt_icon_resources)} RT_ICON entries")
        
        for res in rt_icon_resources:
            icon_by_id[(res['id'], res['lang'])] = {
                'offset': res['offset'],
                'size': res['size']
            }

        rt_group_resources = _extract_resources_by_type(pe, pefile.RESOURCE_TYPE['RT_GROUP_ICON'], logger)
        log(f"Debug: Found {len(rt_group_resources)} RT_GROUP_ICON entries")
        
        group_icon_entries = [(res['id'], res['lang'], res['offset'], res['size']) for res in rt_group_resources]

        for group_id, group_lang, data_offset, size in group_icon_entries:
            data = pe.get_memory_mapped_image()[data_offset:data_offset+size]
            if len(data) < 6:
                continue

            idReserved, idType, idCount = struct.unpack('<HHH', data[:6])
            if idReserved != 0 or idType != 1:
                continue

            entries = []
            offset = 6
            for _ in range(idCount):
                if offset + 14 > len(data):
                    break
                bWidth, bHeight, bColorCount, bReserved, wPlanes, wBitCount, dwBytesInRes, nID = struct.unpack('<BBBBHHIH', data[offset:offset+14])
                entries.append({
                    'width': bWidth,
                    'height': bHeight,
                    'color_count': bColorCount,
                    'planes': wPlanes,
                    'bit_count': wBitCount,
                    'bytes_in_res': dwBytesInRes,
                    'id': nID,
                })
                offset += 14

            group_key = f"icongroup_{group_id}_{group_lang}"
            icon_list = []

            for e in entries:
                rid = e['id']
                icon_data = icon_by_id.get((rid, group_lang))
                if not icon_data:
                    continue
                width = e['width'] if e['width'] != 0 else 256
                height = e['height'] if e['height'] != 0 else 256
                img = _read_icon_image(pe, icon_data.get('offset', 0), icon_data.get('size', 0))
                if img:
                    icon_list.append({
                        'width': width,
                        'height': height,
                        'image': img
                    })

            if icon_list:
                groups[group_key] = icon_list
            else:
                log(f"Warning: Icon group {group_id} has no valid icons")

        for group_key, icon_list in groups.items():
            log(f"Debug: Group {group_key}: {len(icon_list)} icon(s)")

        return groups

    except Exception as e:
        log(f"PE icon extraction failed: {str(e)}")
        return {}
