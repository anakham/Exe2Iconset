#!/usr/bin/env python3
"""Simple CLI interface for exe2iconset."""

import argparse
import os
import sys

from exe2iconset import (
    extract_images,
    convert_icons_to_icns_sizes,
    save_iconset,
    create_icns_from_images,
    ICON_TYPE_MAP,
)


def list_groups(file_path, verbose=False):
    """List available icon groups in a file or directory."""
    def log(msg):
        if verbose:
            print(msg)
    
    icon_groups = extract_images(file_path, log)
    
    if not icon_groups:
        print("No icon groups found.")
        return None
    
    print(f"Available icon groups in {os.path.basename(file_path)}:")
    for i, key in enumerate(icon_groups):
        print(f"  {i + 1}. {key}: {len(icon_groups[key])} icons")
    
    return icon_groups


def main():
    parser = argparse.ArgumentParser(
        description="Extract icons from Windows EXE/DLL files and create macOS ICNS"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to EXE, DLL, MUN, image file, or directory",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available icon groups and exit (PE files only)",
    )
    parser.add_argument(
        "-g", "--group",
        type=str,
        help="Icon group to use (by key, e.g., icongroup_3_1033). Use --list to see available groups.",
    )
    parser.add_argument(
        "-o", "--output",
        default="appicon.icns",
        help="Output ICNS file path (default: appicon.icns)",
    )
    parser.add_argument(
        "--iconset",
        action="store_true",
        help="Also create iconset directory for inspection",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    args = parser.parse_args()
    
    def log(msg):
        if args.verbose:
            print(msg)
    
    if not args.input:
        parser.print_help()
        return 0
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        return 1
    
    # Handle list command - show groups for any input type
    if args.list:
        list_groups(args.input, args.verbose)
        return 0
    
    # Extract icons/images
    log(f"Loading from {args.input}...")
    icon_groups = extract_images(args.input, log)
    
    if not icon_groups:
        print("Error: No images found", file=sys.stderr)
        return 1
    
    # Select icon group (only relevant for PE files)
    if args.group:
        if args.group not in icon_groups:
            print(f"Error: Icon group '{args.group}' not found.", file=sys.stderr)
            print("Use --list to see available groups.")
            return 1
        icon_data_list = icon_groups[args.group]
    else:
        print(f"Found {len(icon_groups)} icon groups:")
        for key in icon_groups:
            print(f"  - {key}: {len(icon_groups[key])} icons")
        
        if len(icon_groups) == 1:
            first_group_key = list(icon_groups.keys())[0]
            icon_data_list = icon_groups[first_group_key]
            print(f"Using group: {first_group_key}")
        else:
            print("Multiple groups found. Use --group to specify.")
            print("Run with --list to see all groups.")
            return 1
    
    # Convert to ICNS sizes
    mac_icon_sizes = list(ICON_TYPE_MAP.keys())
    icon_images = convert_icons_to_icns_sizes(icon_data_list, mac_icon_sizes)
    
    if not icon_images:
        print("Error: Failed to create icon images", file=sys.stderr)
        return 1
    
    print(f"Created {len(icon_images)} icon sizes")
    
    # Create ICNS file
    success = create_icns_from_images(icon_images, args.output)
    
    if success:
        print(f"Created ICNS: {args.output}")
    else:
        print("Error: Failed to create ICNS file", file=sys.stderr)
        return 1
    
    # Optionally create iconset directory
    if args.iconset:
        iconset_path = args.output.replace(".icns", ".iconset")
        save_iconset(icon_images, iconset_path)
        print(f"Created iconset: {iconset_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
