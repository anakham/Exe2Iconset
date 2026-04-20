from PIL import Image
from bisect import bisect_left, bisect_right

try:
    from .extract import extract_icons_from_pe
except ImportError:
    from extract import extract_icons_from_pe


def convert_icons_to_icns_sizes(icon_data_list, mac_icon_sizes):
    """Convert icon list to required ICNS sizes.
    
    Args:
        icon_data_list: List of dicts with 'width', 'height', 'image' keys
        mac_icon_sizes: List of (width, height) tuples for target ICNS sizes
        
    Returns:
        Dict mapping (width, height) to PIL Image
    """
    regular_icons = {}
    
    icon_selected = dict()
    for icon_entry in icon_data_list:
        try:
            img = icon_entry['image'].copy()
            (w, h) = (icon_entry['width'], icon_entry['height'])
            bc = icon_entry['bit_count']
            if (w, h) in icon_selected:
                if bc < icon_selected[(w,h)][0]:
                    continue
            icon_selected[(w, h)] = (bc , img)
        except Exception:
            continue

    target_sizes = mac_icon_sizes.copy()
    icon_selected = dict(sorted(icon_selected.items()))

    resolutions_with_exact_match = set()

    for (src_w, src_h), (_, src_img) in icon_selected.items():
        lt = bisect_left(target_sizes, (src_w, src_h))
        rt = bisect_right(target_sizes, (src_w, src_h))
        if lt == rt:
            lt = lt - 1

        for target_w, target_h in target_sizes[lt:rt]:
            try:
                resized = src_img
                resize_done = False
                if (target_w, target_h) != (src_w, src_h):
                    resized = src_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    resize_done = True
                if (target_w, target_h) not in resolutions_with_exact_match:
                    regular_icons[(target_w, target_h)] = resized
                if not resize_done:
                    resolutions_with_exact_match.add((target_w, target_h))
            except Exception:
                pass
    
    return regular_icons


def save_iconset(icon_images, iconset_path):
    """Save icon images to iconset directory.
    
    Args:
        icon_images: Dict mapping (width, height) to PIL Image
        iconset_path: Path to iconset directory
        
    Returns:
        True if successful
    """
    import os
    from pathlib import Path
    
    iconset_path = Path(iconset_path)
    iconset_path.mkdir(parents=True, exist_ok=True)
    
    for (w, h), img in icon_images.items():
        img.save(iconset_path / f"icon_{w}x{h}.png", 'PNG')
    
    return True


def get_icon_groups(file_path, logger=None):
    """Extract icon groups from a PE file.
    
    Args:
        file_path: Path to PE file (exe, dll, mun)
        logger: Optional callable for logging messages
        
    Returns:
        Dict mapping group keys to list of icon dicts
    """
    return extract_icons_from_pe(file_path, logger)
