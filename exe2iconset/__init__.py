__version__ = "0.1.0"

from .core.extract import (
    extract_icons_from_pe,
    extract_images,
    is_pe_file,
    PE_EXTENSIONS,
)
from .core.images import (
    extract_images_from_files,
    detect_input_type,
    is_image_file,
    is_image_directory,
    IMAGE_EXTENSIONS,
)
from .core.convert import convert_icons_to_icns_sizes, save_iconset, get_icon_groups
from .core.icns import create_icns_from_images, ICON_TYPE_MAP, pack_bits_compress

__all__ = [
    "extract_icons_from_pe",
    "extract_images",
    "is_pe_file",
    "PE_EXTENSIONS",
    "extract_images_from_files",
    "detect_input_type",
    "is_image_file",
    "is_image_directory",
    "IMAGE_EXTENSIONS",
    "convert_icons_to_icns_sizes",
    "save_iconset",
    "get_icon_groups",
    "create_icns_from_images",
    "ICON_TYPE_MAP",
    "pack_bits_compress",
]

from .gui import run_gui, IconExtractorApp
