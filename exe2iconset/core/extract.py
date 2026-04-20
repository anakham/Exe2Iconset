import struct
from io import BytesIO
from PIL import Image
from PIL.IcoImagePlugin import IcoFile

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


def _read_icon_image(pe, offset, size, icon_entry=None):
    """Read icon image from PE file and return RGBA PIL Image.
    
    Uses Pillow's IcoFile which properly handles:
    - PNG images in resources
    - 32-bit DIB with alpha channel
    - Lower bit depth DIB with AND mask converted to alpha
    
    Args:
        pe: pefile.PE object
        offset: offset to icon data in memory-mapped image
        size: size of icon data
        icon_entry: Optional dict with 'width', 'height', 'bit_count', 'bytes_in_res'
                   If provided, builds proper ICO buffer for IcoFile parsing
        
    Returns:
        PIL Image in RGBA format, or None if extraction fails
    """
    raw_data = pe.get_memory_mapped_image()[offset:offset+size]
    
    if len(raw_data) < 4:
        return None
    
    # Check for PNG magic - direct PNG in resources
    if raw_data[:4] == b'\x89PNG':
        try:
            img = Image.open(BytesIO(raw_data))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            return img
        except Exception:
            pass
    
    # If we have icon entry metadata, build ICO buffer for proper parsing
    return _read_via_icoimageplugin(raw_data, icon_entry)


def _read_via_icoimageplugin(raw_data, icon_entry):
    """Build ICO buffer and parse via IcoFile for proper AND mask handling."""
    bpp = icon_entry.get('bit_count', 32)
    width = icon_entry.get('width', 32)
    height = icon_entry.get('height', 32)
    if width == 0:
        width = 256
    if height == 0:
        height = 256
    
    # Build ICO file structure:
    # - 6 byte header: reserved(2) + type(2) + count(2)
    # - 16 byte directory entry per image
    # - image data
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved=0, type=1 (icon), count=1
    
    # Directory entry: width, height, colors, reserved, planes, bpp, size, offset
    dir_entry = struct.pack('<BBBBHHII',
        width if width < 256 else 0,
        height if height < 256 else 0,
        0,  # colors
        0,  # reserved
        1,  # planes
        bpp,  # bit count
        len(raw_data),  # size of image data
        22  # offset to image data = 6 (header) + 16 (directory entry)
    )
    
    ico_buffer = BytesIO(ico_header + dir_entry + raw_data)
    
    try:
        ico = IcoFile(ico_buffer)
        img = ico.getimage((width, height))
        if img and img.mode != 'RGBA':
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
        Dict mapping group keys to list of icon dicts with 'width', 'height', 'bit_count', 'image'
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
                bit_count = e['bit_count']
                img = _read_icon_image(pe, icon_data.get('offset', 0), icon_data.get('size', 0), e)
                if img:
                    icon_list.append({
                        'width': width,
                        'height': height,
                        'bit_count': bit_count,
                        'image': img
                    })

            if icon_list:
                groups[group_key] = icon_list
            else:
                log(f"Warning: Icon group {group_id} has no valid icons")

        for group_key, icon_list in groups.items():
            resolutions = ", ".join(f"{icon['width']}x{icon['height']}@{icon['bit_count']}b" for icon in icon_list)
            log(f"Debug: Group {group_key}: {len(icon_list)} icons ({resolutions})")
            
        return groups

    except Exception as e:
        log(f"PE icon extraction failed: {str(e)}")
        return {}
