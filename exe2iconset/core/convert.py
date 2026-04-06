from PIL import Image

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
    
    icon_sizes = []
    for icon_entry in icon_data_list:
        try:
            img = icon_entry['image'].copy()
            icon_sizes.append((icon_entry['width'], icon_entry['height'], img))
        except Exception:
            continue
    
    icon_sizes.sort(key=lambda x: x[0] * x[1], reverse=True)
    
    for target_w, target_h in mac_icon_sizes:
        best_source = None
        best_diff = float('inf')
        
        for src_w, src_h, src_data in icon_sizes:
            diff = abs(src_w - target_w) + abs(src_h - target_h)
            if diff < best_diff:
                best_diff = diff
                best_source = (src_w, src_h, src_data)
        
        if best_source:
            src_w, src_h, src_img = best_source
            src_img = src_img.copy()
            
            try:
                resized = src_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                regular_icons[(target_w, target_h)] = resized
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
