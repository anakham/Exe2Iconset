import os
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

class IconExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows EXE to macOS ICNS Converter")
        self.root.geometry("900x700")
        
        # Configure styles
        # self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.exe_path = tk.StringVar()
        self.extracted_path = tk.StringVar()
        self.selected_icons = []
        self.icon_series = {}
        self.temp_dir = None
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
        
        # Check for 7z
        try:
            subprocess.run(['7z', '--help'], capture_output=True)
        except FileNotFoundError:
            missing_tools.append("7-Zip (7z.exe)")
        
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
        
        # Create temp directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        self.temp_dir = tempfile.mkdtemp()
        self.extracted_path.set(self.temp_dir)
        
        # Run extraction in thread to avoid UI freeze
        thread = threading.Thread(target=self._extract_icons_thread)
        thread.daemon = True
        thread.start()
    
    def _extract_icons_thread(self):
        self.log_status("Extracting resources from EXE file...")
        
        try:
            # Use 7z to extract resources
            cmd = ['7z', 'x', self.exe_path.get(), '-o' + self.temp_dir, '-y']
            
            # Run 7z extraction
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_status(f"Extraction failed: {result.stderr}")
                return
            
            self.log_status("Extraction completed. Scanning for icons...")
            
            # Find icon files
            icon_files = []
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file.lower().endswith('.ico') or '.icon' in file.lower():
                        icon_files.append(os.path.join(root, file))
            
            if not icon_files:
                # Look for any image files that might be icons
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in ['.png', '.bmp', '.jpg', '.jpeg']):
                            icon_files.append(os.path.join(root, file))
            
            if not icon_files:
                self.log_status("No icons found in the extracted resources.")
                return
            
            self.log_status(f"Found {len(icon_files)} potential icon files.")
            
            # Group icons by series (by base name)
            for icon_file in icon_files:
                basename = os.path.basename(icon_file)
                # Extract series name (remove numbers and extensions)
                import re
                series_name = re.sub(r'\d+', '', basename)
                series_name = re.sub(r'[._-].*$', '', series_name)
                series_name = series_name.lower()
                
                if series_name not in self.icon_series:
                    self.icon_series[series_name] = []
                
                self.icon_series[series_name].append(icon_file)
            
            # Display icons in UI (must be done in main thread)
            self.root.after(0, self.display_icons)
            
        except Exception as e:
            self.log_status(f"Error during extraction: {str(e)}")
    
    def display_icons(self):
        """Display extracted icons in the UI"""
        row, col = 0, 0
        max_cols = 5
        
        for series_name, icon_files in self.icon_series.items():
            # Create a frame for this series
            series_frame = ttk.LabelFrame(self.icon_container, text=series_name, padding="5")
            series_frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Display first icon in series as preview
            if icon_files:
                try:
                    # Try to open as ICO or image
                    if icon_files[0].lower().endswith('.ico'):
                        # For ICO files, extract first image
                        from PIL import Image
                        img = Image.open(icon_files[0])
                        # Get the largest icon from the ICO
                        img_size = img.size
                        img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    else:
                        img = Image.open(icon_files[0])
                        img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    
                    icon_label = ttk.Label(series_frame, image=photo)
                    icon_label.image = photo  # Keep reference
                    icon_label.grid(row=0, column=0, padx=5, pady=5)
                    
                except Exception as e:
                    error_label = ttk.Label(series_frame, text="Error loading")
                    error_label.grid(row=0, column=0, padx=5, pady=5)
            
            # Series info
            info_label = ttk.Label(series_frame, text=f"{len(icon_files)} icons")
            info_label.grid(row=1, column=0, padx=5, pady=(0, 5))
            
            # Select button
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
            icon_files = self.icon_series[self.selected_series_key]
            
            # Create iconset directory
            iconset_name = self.output_name.get() + ".iconset"
            iconset_path = os.path.join(output_dir, iconset_name)
            
            if os.path.exists(iconset_path):
                shutil.rmtree(iconset_path)
            
            os.makedirs(iconset_path)
            
            # macOS icon sizes (in pixels)
            mac_icon_sizes = [
                (16, 16), (32, 32), (64, 64), (128, 128),
                (256, 256), (512, 512), (1024, 1024)
            ]
            
            # Sort icon files by size (largest first)
            icon_sizes = []
            for icon_file in icon_files:
                try:
                    with Image.open(icon_file) as img:
                        icon_sizes.append((img.width, img.height, icon_file))
                except:
                    continue
            
            # Sort by total pixels (width * height)
            icon_sizes.sort(key=lambda x: x[0] * x[1], reverse=True)
            
            self.log_status(f"Processing {len(icon_sizes)} icons...")
            
            # Create resized versions for each macOS size
            created_files = []
            for target_w, target_h in mac_icon_sizes:
                # Find the closest source icon
                best_source = None
                best_diff = float('inf')
                
                for src_w, src_h, src_file in icon_sizes:
                    diff = abs(src_w - target_w) + abs(src_h - target_h)
                    if diff < best_diff:
                        best_diff = diff
                        best_source = (src_w, src_h, src_file)
                
                if best_source:
                    src_w, src_h, src_file = best_source
                    
                    try:
                        with Image.open(src_file) as img:
                            # Resize to target size
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')
                            
                            # Create resized image
                            resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                            
                            # Save in iconset with proper naming
                            # Regular size
                            regular_name = f"icon_{target_w}x{target_h}.png"
                            regular_path = os.path.join(iconset_path, regular_name)
                            resized.save(regular_path, 'PNG')
                            created_files.append(regular_path)
                            
                            # Retina size (2x)
                            retina_name = f"icon_{target_w//2}x{target_h//2}@2x.png"
                            retina_path = os.path.join(iconset_path, retina_name)
                            
                            # Create retina version if source is large enough
                            if src_w >= target_w and src_h >= target_h:
                                retina_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                                retina_img.save(retina_path, 'PNG')
                                created_files.append(retina_path)
                    
                    except Exception as e:
                        self.log_status(f"Error processing {src_file}: {str(e)}")
            
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
    
    # Handle window closing
    def on_closing():
        # Clean up temp directory
        if app.temp_dir and os.path.exists(app.temp_dir):
            try:
                shutil.rmtree(app.temp_dir)
            except:
                pass
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
