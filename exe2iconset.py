import os
import struct
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import shutil
from pathlib import Path
import json
import threading
from io import BytesIO

try:
    import pefile
except ImportError:
    pefile = None


# PackBits compression for ICNS small icons (icp4/icp5)
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


def create_icns_file(iconset_path, icns_path):
    """Create ICNS file from iconset directory.
    
    Uses PNG for main icons (ic07-ic14) and PackBits RGB for small icons (icp4/icp5).
    """
    # Map of icon types (by display size)
    # Only icp4/icp5 support PackBits RGB, others use PNG
    # icp4 = 16x16, icp5 = 32x32, ic07 = 128x128, ic08 = 256x256, ic09 = 512x512, ic10 = 1024x1024
    # ic11 = 32 (16@2x), ic12 = 64 (32@2x), ic13 = 256 (128@2x), ic14 = 512 (256@2x)
    icon_type_map = {
        (16, 16): b'icp4',    # PackBits RGB
        (32, 32): b'icp5',    # PackBits RGB
        (64, 64): b'ic12',    # PNG (no icp6 support in iconutil)
        (128, 128): b'ic07',   # PNG
        (256, 256): b'ic08',   # PNG
        (512, 512): b'ic09',   # PNG
        (1024, 1024): b'ic10', # PNG
    }
    
    retina_type_map = {
        (16, 16): b'ic11',   # 16@2x: 32 stored, 16 display
        (32, 32): b'ic12',   # 32@2x: 64 stored, 32 display
        (128, 128): b'ic13', # 128@2x: 256 stored, 128 display
        (256, 256): b'ic14', # 256@2x: 512 stored, 256 display
    }
    
    blocks = []
    
    # Read all PNG files from iconset
    for filename in os.listdir(iconset_path):
        if not filename.endswith('.png'):
            continue
            
        filepath = os.path.join(iconset_path, filename)
        
        # Parse size from filename (e.g., "icon_128x128.png" or "icon_128x128@2x.png")
        name = filename[:-4]  # remove .png
        
        is_retina = '@2x' in name
        name_parts = name.replace('@2x', '').split('x')
        
        if len(name_parts) != 2:
            continue
            
        try:
            width = int(name_parts[0])
            height = int(name_parts[1])
        except ValueError:
            continue
        
        # Read PNG data
        with open(filepath, 'rb') as f:
            png_data = f.read()
        
        # Determine icon type
        if is_retina:
            # For retina: stored size is 2x the display size
            # icon_128x128@2x.png = 256x256 stored, 128x128 display -> ic13
            actual_width = width * 2
            actual_height = height * 2
            icon_type = retina_type_map.get((width, height))
        else:
            actual_width = width
            actual_height = height
            icon_type = icon_type_map.get((width, height))
        
        if not icon_type:
            continue
        
        # For small icons (icp4, icp5), use PackBits RGB instead of PNG
        if icon_type in [b'icp4', b'icp5']:
            img = Image.open(filepath)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Extract channels and compress with PackBits
            pixels = list(img.getdata())
            r_channel = []
            g_channel = []
            b_channel = []
            
            for r, g, b, a in pixels:
                r_channel.append(r)
                g_channel.append(g)
                b_channel.append(b)
            
            r_compressed = pack_bits_compress(bytes(r_channel))
            g_compressed = pack_bits_compress(bytes(g_channel))
            b_compressed = pack_bits_compress(bytes(b_channel))
            
            block_data = r_compressed + g_compressed + b_compressed
        else:
            block_data = png_data
        
        # Create block header
        block = icon_type + struct.pack('>I', len(block_data) + 8) + block_data
        blocks.append((icon_type, block))
    
    if not blocks:
        return False
    
    # Sort blocks by type (icp types first, then ic0* types)
    blocks.sort(key=lambda x: x[0])
    
    # Build ICNS file
    blocks_data = b''.join(block for _, block in blocks)
    
    # ICNS header
    total_size = 8 + len(blocks_data)
    icns_data = b'icns' + struct.pack('>I', total_size) + blocks_data
    
    # Write to file
    with open(icns_path, 'wb') as f:
        f.write(icns_data)
    
    return True

class IconExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows EXE to macOS ICNS Converter")
        self.root.geometry("900x700")
        
        # Configure styles
        # self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.exe_path = tk.StringVar()
        self.selected_icons = []
        self.icon_series = {}
        self.selected_series_key = None
        
        # Create UI
        self.create_widgets()
        
        # Check for required tools
        self.check_requirements()
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="EXE to ICNS Converter", 
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Step 1: Select EXE file
        step1_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Windows Executable", padding="10")
        step1_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        step1_frame.columnconfigure(1, weight=1)
        
        ttk.Label(step1_frame, text="EXE File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        exe_entry = ttk.Entry(step1_frame, textvariable=self.exe_path, width=50)
        exe_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(step1_frame, text="Browse...", command=self.browse_exe).grid(row=0, column=2)
        ttk.Button(step1_frame, text="Extract Icons", command=self.extract_icons).grid(row=0, column=3, padx=(10, 0))
        
        # Step 2: Icon display area
        step2_frame = ttk.LabelFrame(main_frame, text="Step 2: Select Icon Series", padding="10")
        step2_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        step2_frame.columnconfigure(0, weight=1)
        step2_frame.rowconfigure(0, weight=1)
        
        # Canvas with scrollbar for icons
        icon_canvas_frame = ttk.Frame(step2_frame)
        icon_canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        icon_canvas_frame.columnconfigure(0, weight=1)
        icon_canvas_frame.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(icon_canvas_frame, highlightthickness=1, highlightbackground='#ccc')
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(icon_canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.icon_container = ttk.Frame(canvas)
        self.icon_window = canvas.create_window((0, 0), window=self.icon_container, anchor=tk.NW)
        
        # Configure canvas scrolling
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self.icon_window, width=canvas.winfo_width())
        
        self.icon_container.bind("<Configure>", configure_canvas)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.icon_window, width=e.width))
        
        # Step 3: Conversion options
        step3_frame = ttk.LabelFrame(main_frame, text="Step 3: Convert to macOS ICNS", padding="10")
        step3_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(step3_frame, text="Output Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.output_name = tk.StringVar(value="appicon")
        output_entry = ttk.Entry(step3_frame, textvariable=self.output_name, width=30)
        output_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Button(step3_frame, text="Create ICNS Package", command=self.create_icns).grid(row=0, column=2)
        
        # Status area
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_text = tk.Text(status_frame, height=6, width=80, state=tk.DISABLED, 
                                   relief=tk.FLAT)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights for main frame rows
        main_frame.rowconfigure(2, weight=1)
        
    def check_requirements(self):
        """Check if required tools are available"""
        missing_tools = []
        
        # Check for pefile library (required for internal PE resource parsing)
        if pefile is None:
            missing_tools.append("pefile (Python package)")

        # Check for PIL (used for ICNS creation - cross-platform)
        try:
            Image.__version__
        except:
            missing_tools.append("Pillow (Python imaging library)")
        
        if missing_tools:
            messagebox.showwarning("Missing Tools", 
                f"The following tools are required:\n\n{chr(10).join(missing_tools)}\n\nPlease install them to use all features.")
    
    def browse_exe(self):
        filename = filedialog.askopenfilename(
            title="Select Windows File with Resources",
            filetypes=[("Windows files with resources", "*.exe *.dll *.mun"), ("All files", "*.*")]
        )
        if filename:
            self.exe_path.set(filename)
            self.log_status(f"Selected file: {filename}")
    
    def extract_icons(self):
        if not self.exe_path.get():
            messagebox.showerror("Error", "Please select an EXE file first")
            return
        
        # Clear previous icons
        for widget in self.icon_container.winfo_children():
            widget.destroy()
        
        self.selected_icons = []
        self.icon_series = {}
        
        thread = threading.Thread(target=self._extract_icons_thread)
        thread.daemon = True
        thread.start()
    
    def _extract_icons_thread(self):
        self.log_status("Extracting resources from EXE file...")
        
        try:
            self.log_status("Extracting icons from PE resources...")

            icon_files = self.extract_icons_from_pe(self.exe_path.get())
            if not icon_files:
                self.log_status("No icons found in the PE resources.")
                return

            self.icon_series = icon_files
            self.log_status(f"Extracted {len(self.icon_series)} icon groups from PE resources.")

            # Display icons in UI (must be done in main thread)
            self.root.after(0, self.display_icons)
            return

        except Exception as e:
            self.log_status(f"Error during extraction: {str(e)}")
            return

    def _extract_resources_by_type(self, pe, resource_type_id):
        """Extract all resources of a specific type with proper recursion."""
        results = []
        
        if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            return results
        
        resource_type_name = pefile.RESOURCE_TYPE.get(resource_type_id, f"UNKNOWN_{resource_type_id}")
        
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id == resource_type_id:
                self.log_status(f"Debug: Found {resource_type_name} (ID={resource_type_id})")
                
                if hasattr(entry, 'directory') and entry.directory:
                    for sub_entry in entry.directory.entries:
                        sub_id = sub_entry.id if sub_entry.id else 0
                        sub_name = sub_entry.name if sub_entry.name else None
                        
                        self.log_status(f"Debug:   Resource ID={sub_id}, name={sub_name}")
                        
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

    def _fix_dib_data(self, data):
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

    def _read_icon_image(self, pe, offset, size):
        """Read icon image from PE file and return RGBA PIL Image.
        
        Args:
            pe: pefile.PE object
            offset: offset to icon data in memory-mapped image
            size: size of icon data
            
        Returns:
            PIL Image in RGBA format, or None if extraction fails
        """
        raw_data = pe.get_memory_mapped_image()[offset:offset+size]
        fixed_data = self._fix_dib_data(raw_data)
        
        try:
            img = Image.open(BytesIO(fixed_data))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            return img
        except Exception:
            return None

    def extract_icons_from_pe(self, file_path):
        """Extract icon groups from PE resources using pefile."""
        try:
            if pefile is None:
                self.log_status("pefile library not available")
                return {}

            pe = pefile.PE(file_path)

            if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
                self.log_status("No resource directory found in PE file")
                return {}

            self.log_status("Debug: Starting resource directory traversal...")
            self.log_status(f"Debug: Root resource entries: {len(pe.DIRECTORY_ENTRY_RESOURCE.entries)}")
            
            for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                self.log_status(f"Debug: Root entry id={entry.id}, name={entry.name}")

            icon_by_id = {}
            groups = {}

            rt_icon_resources = self._extract_resources_by_type(pe, pefile.RESOURCE_TYPE['RT_ICON'])
            self.log_status(f"Debug: Found {len(rt_icon_resources)} RT_ICON entries")
            
            for res in rt_icon_resources:
                icon_by_id[(res['id'], res['lang'])] = {
                    'offset': res['offset'],
                    'size': res['size']
                }

            rt_group_resources = self._extract_resources_by_type(pe, pefile.RESOURCE_TYPE['RT_GROUP_ICON'])
            self.log_status(f"Debug: Found {len(rt_group_resources)} RT_GROUP_ICON entries")
            
            group_icon_entries = [(res['id'], res['lang'], res['offset'], res['size']) for res in rt_group_resources]

            # Parse each group icon after all ICON resources are collected
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
                    img = self._read_icon_image(pe, icon_data.get('offset', 0), icon_data.get('size', 0))
                    if img:
                        icon_list.append({
                            'width': width,
                            'height': height,
                            'image': img
                        })

                if icon_list:
                    groups[group_key] = icon_list
                else:
                    self.log_status(f"Warning: Icon group {group_id} has no valid icons")

            for group_key, icon_list in groups.items():
                self.log_status(f"Debug: Group {group_key}: {len(icon_list)} icon(s)")

            return groups

        except Exception as e:
            self.log_status(f"PE icon extraction failed: {str(e)}")
            return {}

    def display_icons(self):
        """Display extracted icons in the UI"""
        row, col = 0, 0
        max_cols = 5
        
        for series_name, icon_data_list in self.icon_series.items():
            series_frame = ttk.LabelFrame(self.icon_container, text=series_name, padding="5")
            series_frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            if icon_data_list:
                try:
                    first_icon = icon_data_list[0]
                    img = first_icon['image'].resize((64, 64), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    
                    icon_label = ttk.Label(series_frame, image=photo)
                    icon_label.image = photo
                    icon_label.grid(row=0, column=0, padx=5, pady=5)
                    
                except Exception as e:
                    error_label = ttk.Label(series_frame, text=f"Error: {str(e)[:20]}")
                    error_label.grid(row=0, column=0, padx=5, pady=5)
            
            info_label = ttk.Label(series_frame, text=f"{len(icon_data_list)} icons")
            info_label.grid(row=1, column=0, padx=5, pady=(0, 5))
            
            select_btn = ttk.Button(series_frame, text="Select Series", 
                                    command=lambda sn=series_name: self.select_series(sn))
            select_btn.grid(row=2, column=0, padx=5, pady=(0, 5))
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.log_status(f"Found {len(self.icon_series)} icon series. Select one to convert.")
    
    def select_series(self, series_name):
        """Select an icon series for conversion"""
        self.selected_series_key = series_name
        self.log_status(f"Selected series: {series_name} with {len(self.icon_series[series_name])} icons")
        
        # Highlight selected series (simple visual feedback)
        for child in self.icon_container.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if child.cget('text') == series_name:
                    child.configure(relief=tk.SUNKEN)
                else:
                    child.configure(relief=tk.RAISED)
    
    def create_icns(self):
        if (self.selected_series_key is None) or not self.icon_series.get(self.selected_series_key):
            messagebox.showerror("Error", "Please select an icon series first")
            return
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        
        # Run conversion in thread
        thread = threading.Thread(target=self._create_icns_thread, args=(output_dir,))
        thread.daemon = True
        thread.start()
    
    def _create_icns_thread(self, output_dir):
        self.log_status("Starting ICNS conversion...")
        
        try:
            icon_data_list = self.icon_series[self.selected_series_key]
            
            iconset_name = self.output_name.get() + ".iconset"
            iconset_path = os.path.join(output_dir, iconset_name)
            
            if os.path.exists(iconset_path):
                shutil.rmtree(iconset_path)
            
            os.makedirs(iconset_path)
            
            mac_icon_sizes = [
                (16, 16), (32, 32), (64, 64), (128, 128),
                (256, 256), (512, 512), (1024, 1024)
            ]
            
            icon_sizes = []
            for icon_entry in icon_data_list:
                try:
                    img = icon_entry['image'].copy()
                    icon_sizes.append((icon_entry['width'], icon_entry['height'], img))
                except Exception as e:
                    self.log_status(f"Warning: Could not read icon data: {str(e)}")
                    continue
            
            icon_sizes.sort(key=lambda x: x[0] * x[1], reverse=True)
            
            self.log_status(f"Processing {len(icon_sizes)} icons...")
            
            created_files = []
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
                        
                        regular_name = f"icon_{target_w}x{target_h}.png"
                        regular_path = os.path.join(iconset_path, regular_name)
                        resized.save(regular_path, 'PNG')
                        created_files.append(regular_path)
                        
                        retina_name = f"icon_{target_w//2}x{target_h//2}@2x.png"
                        retina_path = os.path.join(iconset_path, retina_name)
                        
                        if src_w >= target_w and src_h >= target_h:
                            retina_img = resized
                            retina_img.save(retina_path, 'PNG')
                            created_files.append(retina_path)
                    
                    except Exception as e:
                        self.log_status(f"Error processing icon: {str(e)}")
            
            self.log_status(f"Created {len(created_files)} PNG files in iconset.")
            
            # Create ICNS file using custom implementation with proper icon types
            icns_path = os.path.join(output_dir, self.output_name.get() + ".icns")
            
            try:
                if create_icns_file(iconset_path, icns_path):
                    self.log_status(f"Successfully created ICNS file: {icns_path}")
                    
                    # Optionally clean up iconset directory
                    response = messagebox.askyesno("Success", 
                        f"ICNS file created successfully!\n\n"
                        f"Location: {icns_path}\n\n"
                        f"Keep the iconset directory for future modifications?")
                    
                    if not response:
                        shutil.rmtree(iconset_path)
                else:
                    self.log_status(f"Failed to create ICNS")
                    self.log_status(f"PNG files saved in: {iconset_path}")
            except Exception as e:
                self.log_status(f"Failed to create ICNS: {str(e)}")
                self.log_status(f"PNG files saved in: {iconset_path}")
            
            # Open output directory
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                subprocess.run(['open', output_dir])
            elif sys.platform == 'linux':
                subprocess.run(['xdg-open', output_dir])
                
        except Exception as e:
            self.log_status(f"Error creating ICNS: {str(e)}")
    
    def log_status(self, message):
        """Add message to status text area"""
        def update_status():
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, message + "\n")
            self.status_text.see(tk.END)
            self.status_text.config(state=tk.DISABLED)
        
        self.root.after(0, update_status)

def main():
    root = tk.Tk()
    app = IconExtractorApp(root)
    
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
