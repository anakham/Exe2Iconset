import os
import struct
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import shutil
from pathlib import Path
import json
import threading
from io import BytesIO

try:
    import pefile
except ImportError:
    pefile = None

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

        # Check for iconutil (macOS) - we'll use alternative if not available
        self.iconutil_available = False
        if sys.platform == 'darwin':
            try:
                subprocess.run(['iconutil', '--help'], capture_output=True)
                self.iconutil_available = True
            except FileNotFoundError:
                self.log_status("Note: iconutil not found, will use PNG conversion only")
        
        # Check for PIL
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

    def _traverse_resource_directory(self, pe, entry, depth=0, results=None):
        """Recursively traverse resource directory entries."""
        if results is None:
            results = []
        
        indent = "  " * depth
        self.log_status(f"Debug: {indent}Level {depth}, entries: {len(entry.directory.entries)}")
        
        for idx, sub_entry in enumerate(entry.directory.entries):
            entry_id = sub_entry.id if sub_entry.id else 0
            entry_name = sub_entry.name if sub_entry.name else None
            
            self.log_status(f"Debug: {indent}  [{idx}] id={entry_id}, name={entry_name}")
            
            if hasattr(sub_entry, 'directory') and sub_entry.directory:
                self._traverse_resource_directory(pe, sub_entry, depth + 1, results)
            elif hasattr(sub_entry, 'data') and sub_entry.data:
                rva = sub_entry.data.struct.OffsetToData
                size = sub_entry.data.struct.Size
                results.append({
                    'id': entry_id,
                    'name': entry_name,
                    'rva': rva,
                    'size': size,
                    'depth': depth
                })
        
        return results

    def _extract_resources_by_type(self, pe, resource_type_id):
        """Extract all resources of a specific type with proper recursion."""
        results = []
        
        if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            return results
        
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id == resource_type_id:
                self.log_status(f"Debug: Found RT_{'ICON' if resource_type_id == 3 else 'GROUP_ICON'} (ID={resource_type_id})")
                
                if hasattr(entry, 'directory') and entry.directory:
                    for sub_entry in entry.directory.entries:
                        sub_id = sub_entry.id if sub_entry.id else 0
                        sub_name = sub_entry.name if sub_entry.name else None
                        
                        self.log_status(f"Debug:   Resource ID={sub_id}, name={sub_name}")
                        
                        if hasattr(sub_entry, 'directory') and sub_entry.directory:
                            for lang_entry in sub_entry.directory.entries:
                                lang_id = lang_entry.id if lang_entry.id else 0
                                
                                if hasattr(lang_entry, 'data') and lang_entry.data:
                                    rva = lang_entry.data.struct.OffsetToData
                                    size = lang_entry.data.struct.Size
                                    results.append({
                                        'id': sub_id,
                                        'name': sub_name,
                                        'lang': lang_id,
                                        'rva': rva,
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
            buf = BytesIO()
            img.save(buf, 'PNG')
            return buf.getvalue()
        
        fixed_data = bytearray(data)
        struct.pack_into('<i', fixed_data, 8, biHeight // 2)
        return bytes(fixed_data)

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
                data = pe.get_memory_mapped_image()[res['rva']:res['rva']+res['size']]
                icon_by_id[res['id']] = data

            rt_group_resources = self._extract_resources_by_type(pe, pefile.RESOURCE_TYPE['RT_GROUP_ICON'])
            self.log_status(f"Debug: Found {len(rt_group_resources)} RT_GROUP_ICON entries")
            
            group_icon_entries = [(res['id'], res['rva'], res['size']) for res in rt_group_resources]

            # Parse each group icon after all ICON resources are collected
            for group_id, data_rva, size in group_icon_entries:
                data = pe.get_memory_mapped_image()[data_rva:data_rva+size]
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

                group_key = f"icongroup_{group_id}"
                icon_list = []

                for e in entries:
                    rid = e['id']
                    icon_data = icon_by_id.get(rid)
                    if not icon_data:
                        continue
                    width = e['width'] if e['width'] != 0 else 256
                    height = e['height'] if e['height'] != 0 else 256
                    icon_list.append({
                        'width': width,
                        'height': height,
                        'data': icon_data
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
                    img_data = self._fix_dib_data(first_icon['data'])
                    img = Image.open(BytesIO(img_data))
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    
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
                    img = Image.open(BytesIO(icon_entry['data']))
                    icon_sizes.append((icon_entry['width'], icon_entry['height'], icon_entry['data']))
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
                    src_w, src_h, src_data = best_source
                    
                    try:
                        img_data = self._fix_dib_data(src_data)
                        img = Image.open(BytesIO(img_data))
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        
                        resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        
                        regular_name = f"icon_{target_w}x{target_h}.png"
                        regular_path = os.path.join(iconset_path, regular_name)
                        resized.save(regular_path, 'PNG')
                        created_files.append(regular_path)
                        
                        retina_name = f"icon_{target_w//2}x{target_h//2}@2x.png"
                        retina_path = os.path.join(iconset_path, retina_name)
                        
                        if src_w >= target_w and src_h >= target_h:
                            retina_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                            retina_img.save(retina_path, 'PNG')
                            created_files.append(retina_path)
                    
                    except Exception as e:
                        self.log_status(f"Error processing icon: {str(e)}")
            
            self.log_status(f"Created {len(created_files)} PNG files in iconset.")
            
            # Create ICNS file if iconutil is available
            icns_path = os.path.join(output_dir, self.output_name.get() + ".icns")
            
            if self.iconutil_available and sys.platform == 'darwin':
                # Use macOS iconutil to create ICNS
                cmd = ['iconutil', '-c', 'icns', iconset_path, '-o', icns_path]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_status(f"Successfully created ICNS file: {icns_path}")
                    
                    # Optionally clean up iconset directory
                    response = messagebox.askyesno("Success", 
                        f"ICNS file created successfully!\n\n"
                        f"Location: {icns_path}\n\n"
                        f"Keep the iconset directory for future modifications?")
                    
                    if not response:
                        shutil.rmtree(iconset_path)
                else:
                    self.log_status(f"iconutil failed: {result.stderr}")
                    self.log_status(f"PNG files saved in: {iconset_path}")
            else:
                # For Windows or without iconutil, just save the PNGs
                self.log_status(f"PNG iconset created at: {iconset_path}")
                self.log_status("Note: On macOS, use 'iconutil -c icns <iconset>' to create ICNS")
                
                # Create a simple batch script for macOS users
                if sys.platform != 'darwin':
                    script_path = os.path.join(output_dir, "create_icns_mac.command")
                    with open(script_path, 'w') as f:
                        f.write("#!/bin/bash\n")
                        f.write(f'iconutil -c icns "{iconset_name}"\n')
                        f.write('echo "ICNS file created!"\n')
                    
                    os.chmod(script_path, 0o755)
                    self.log_status(f"Created macOS conversion script: {script_path}")
            
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
