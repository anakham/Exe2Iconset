import os
from PIL import Image

from .extract import PE_EXTENSIONS


IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif',
                   '.webp', '.ico', '.cur', '.ppm', '.pbm', '.pgm',
                   '.pcx', '.icns'}


def detect_input_type(path):
    """Detect input type based on path.
    
    Returns:
        'pe': PE file (exe, dll, mun)
        'image': Single image file
        'directory': Directory with images
        'unknown': Not a recognized input
    """
    if not os.path.exists(path):
        return 'unknown'
    
    ext = os.path.splitext(path)[1].lower()
    if ext in PE_EXTENSIONS:
        return 'pe'
    if os.path.isfile(path) and ext in IMAGE_EXTENSIONS:
        return 'image'
    if os.path.isdir(path):
        return 'directory'
    return 'unknown'


def is_image_file(path):
    """Check if path is a single image file."""
    return detect_input_type(path) == 'image'


def is_image_directory(path):
    """Check if path is a directory with images."""
    return detect_input_type(path) == 'directory'


SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS


def _is_image_file(filename):
    """Check if file has image extension."""
    _, ext = os.path.splitext(filename.lower())
    return ext in IMAGE_EXTENSIONS


def _load_image(path):
    """Load image file and return RGBA PIL Image."""
    img = Image.open(path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return img


def extract_images_from_files(path, logger=None, progress_callback=None):
    """Extract images from file or directory.
    
    Args:
        path: Path to image file or directory containing images
        logger: Optional callable for logging messages
        progress_callback: Optional callable(current, total) for progress updates
    
    Returns:
        Dict mapping filename to list of icon dicts with 'width', 'height', 'bit_count', 'image'
    """
    def log(msg):
        if logger:
            logger(msg)
    
    def progress(current, total):
        if progress_callback:
            progress_callback(current, total)
    
    path = os.path.abspath(path)
    
    if os.path.isfile(path):
        return _extract_single_image(path, log)
    elif os.path.isdir(path):
        return _extract_directory(path, log, progress)
    else:
        log(f"Path not found: {path}")
        return {}


def _extract_single_image(path, log):
    """Extract single image file."""
    filename = os.path.basename(path)
    
    try:
        img = _load_image(path)
        w, h = img.size
        
        return {
            filename: [{
                'width': w,
                'height': h,
                'bit_count': 32,
                'image': img
            }]
        }
    except Exception as e:
        log(f"Failed to load {filename}: {e}")
        return {}


def _extract_directory(dir_path, log, progress):
    """Extract all image files from directory into a single group."""
    groups = {}
    
    image_files = [
        f for f in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, f)) and _is_image_file(f)
    ]
    
    if not image_files:
        log(f"No image files found in {dir_path}")
        return {}
    
    total = len(image_files)
    log(f"Found {total} image files in directory")
    
    icon_list = []
    
    for i, filename in enumerate(sorted(image_files)):
        progress(i + 1, total)
        
        file_path = os.path.join(dir_path, filename)
        
        try:
            img = _load_image(file_path)
            w, h = img.size
            
            icon_list.append({
                'width': w,
                'height': h,
                'bit_count': 32,
                'image': img
            })
        except Exception as e:
            log(f"Failed to load {filename}: {e}")
    
    progress(total, total)
    
    if icon_list:
        dir_name = os.path.basename(dir_path)
        groups[dir_name] = icon_list
        log(f"Loaded {len(icon_list)} images into group '{dir_name}'")
    
    return groups