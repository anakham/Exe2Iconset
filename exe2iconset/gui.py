import os
import struct
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
from io import BytesIO

from .core.extract import extract_icons_from_pe
from .core.convert import convert_icons_to_icns_sizes, save_iconset
from .core.icns import ICON_TYPE_MAP, create_icns_from_images


class IconExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows EXE to macOS ICNS Converter")
        self.root.geometry("900x700")
        
        self.exe_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.selected_icons = []
        self.icon_series = {}
        self.selected_series_key = None
        
        self.create_widgets()
        self.check_requirements()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, text="EXE to ICNS Converter", 
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        step1_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Windows Executable", padding="10")
        step1_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        step1_frame.columnconfigure(1, weight=1)
        
        ttk.Label(step1_frame, text="EXE File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        exe_entry = ttk.Entry(step1_frame, textvariable=self.exe_path, width=50)
        exe_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        exe_entry.bind('<Return>', lambda e: self.extract_icons())
        
        ttk.Button(step1_frame, text="Browse...", command=self.browse_exe).grid(row=0, column=2)
        
        self.output_name = tk.StringVar(value="appicon")
        self.save_icns = tk.BooleanVar(value=True)
        self.save_iconset = tk.BooleanVar(value=False)
        
        step2_frame = ttk.LabelFrame(main_frame, text="Step 2: Select Output Path", padding="10")
        step2_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        step2_frame.columnconfigure(1, weight=1)
        
        ttk.Label(step2_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        output_dir_entry = ttk.Entry(step2_frame, textvariable=self.output_dir, width=50)
        output_dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.output_dir.trace_add('write', lambda *args: self.update_output_preview())
        
        ttk.Button(step2_frame, text="Browse...", command=self.browse_output_dir).grid(row=0, column=2)
        
        ttk.Label(step2_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        
        output_name_entry = ttk.Entry(step2_frame, textvariable=self.output_name, width=30)
        output_name_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        self.output_name.trace_add('write', lambda *args: self.update_output_preview())
        
        ttk.Checkbutton(step2_frame, text=".icns", variable=self.save_icns, command=self.update_output_preview).grid(row=1, column=2, padx=(10, 0))
        ttk.Checkbutton(step2_frame, text=".iconset directory", variable=self.save_iconset, command=self.update_output_preview).grid(row=1, column=3)
        
        self.output_preview = ttk.Label(step2_frame, text="", font=("Arial", 9), foreground="#666")
        self.output_preview.grid(row=2, column=0, columnspan=4, pady=(5, 0))
        
        step3_frame = ttk.LabelFrame(main_frame, text="Step 3: Select and Convert", padding="10")
        step3_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        step3_frame.columnconfigure(0, weight=1)
        step3_frame.rowconfigure(0, weight=1)
        
        icon_canvas_frame = ttk.Frame(step3_frame)
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
        
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self.icon_window, width=canvas.winfo_width())
        
        self.icon_container.bind("<Configure>", configure_canvas)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.icon_window, width=e.width))
        
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_text = tk.Text(status_frame, height=6, width=80, state=tk.DISABLED, 
                                   relief=tk.FLAT)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        main_frame.rowconfigure(3, weight=1)
    
    def check_requirements(self):
        missing_tools = []
        
        try:
            import pefile
        except ImportError:
            missing_tools.append("pefile (Python package)")
        
        try:
            Image.__version__
        except:
            missing_tools.append("Pillow")
        
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
            
            exe_dir = os.path.dirname(filename)
            exe_stem = os.path.splitext(os.path.basename(filename))[0]
            self.output_dir.set(exe_dir)
            self.output_name.set(exe_stem)
            self.update_output_preview()
            
            self.log_status(f"Selected file: {filename}")
            self.extract_icons()
    
    def browse_output_dir(self):
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_dir.set(dirname)
            self.update_output_preview()
    
    def update_output_preview(self, *args):
        output_dir = self.output_dir.get()
        output_name = self.output_name.get()
        parts = []
        if self.save_icns.get():
            parts.append(output_name + ".icns")
        if self.save_iconset.get():
            parts.append(output_name + ".iconset")
        if not parts:
            self.output_preview.config(text="Select .icns and/or .iconset to save output")
        elif output_dir:
            preview_text = "Output: " + ", ".join(parts) + " in " + output_dir
            self.output_preview.config(text=preview_text)
    
    def extract_icons(self):
        if not self.exe_path.get():
            messagebox.showerror("Error", "Please select an EXE file first")
            return
        
        for widget in self.icon_container.winfo_children():
            widget.destroy()
        
        self.selected_icons = []
        self.icon_series = {}
        
        thread = threading.Thread(target=self._extract_icons_thread)
        thread.daemon = True
        thread.start()
    
    def _extract_icons_thread(self):
        self.log_status("Extracting icons from PE resources...")
        
        try:
            icon_files = extract_icons_from_pe(self.exe_path.get(), self.log_status)
            if not icon_files:
                self.log_status("No icons found in the PE resources.")
                return

            self.icon_series = icon_files
            self.log_status(f"Extracted {len(self.icon_series)} icon groups from PE resources.")

            self.root.after(0, self.display_icons)
            return

        except Exception as e:
            self.log_status(f"Error during extraction: {str(e)}")
            return
    
    def display_icons(self):
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
            
            convert_btn = ttk.Button(series_frame, text="Convert", 
                                    command=lambda sn=series_name: self.select_and_convert(sn))
            convert_btn.grid(row=2, column=0, padx=5, pady=(0, 5))
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.log_status(f"Found {len(self.icon_series)} icon series. Click 'Convert' to create ICNS.")
    
    def select_series(self, series_name):
        self.selected_series_key = series_name
        self.log_status(f"Selected series: {series_name} with {len(self.icon_series[series_name])} icons")
        
        for child in self.icon_container.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if child.cget('text') == series_name:
                    child.configure(relief=tk.SUNKEN)
                else:
                    child.configure(relief=tk.RAISED)
    
    def select_and_convert(self, series_name):
        self.select_series(series_name)
        self.create_icns()
    
    def create_icns(self):
        if (self.selected_series_key is None) or not self.icon_series.get(self.selected_series_key):
            messagebox.showerror("Error", "Please select an icon series first")
            return
        
        if not self.output_dir.get():
            self.browse_output_dir()
            if not self.output_dir.get():
                return
        
        thread = threading.Thread(target=self._create_icns_thread)
        thread.daemon = True
        thread.start()
    
    def _create_icns_thread(self):
        output_dir = self.output_dir.get()
        self.log_status("Starting ICNS conversion...")
        
        try:
            icon_data_list = self.icon_series[self.selected_series_key]
            output_name = self.output_name.get()
            
            iconset_name = output_name + ".iconset"
            iconset_path = os.path.join(output_dir, iconset_name)                      
            
            mac_icon_sizes = list(ICON_TYPE_MAP.keys())
            
            regular_icons = convert_icons_to_icns_sizes(icon_data_list, mac_icon_sizes)
            
            self.log_status(f"Created {len(regular_icons)} icon sizes for ICNS.")
            
            icns_path = os.path.join(output_dir, output_name + ".icns")
            
            saved = []
            try:
                if self.save_icns.get():
                    if create_icns_from_images(regular_icons, icns_path):
                        saved.append(icns_path)
                        self.log_status(f"Successfully created ICNS file: {icns_path}")
                    else:
                        self.log_status("Failed to create ICNS")
                if self.save_iconset.get():
                    if not os.path.exists(iconset_path):
                        os.makedirs(iconset_path)
                    save_iconset(regular_icons, iconset_path)
                    saved.append(iconset_path)
                    self.log_status(f"Successfully created iconset: {iconset_path}")
            except Exception as e:
                self.log_status(f"Failed to create output: {str(e)}")
            
            if saved:
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Created:\n" + "\n".join(saved)))
                
        except Exception as e:
            self.log_status(f"Error creating ICNS: {str(e)}")
    
    def log_status(self, message):
        def update_status():
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, message + "\n")
            self.status_text.see(tk.END)
            self.status_text.config(state=tk.DISABLED)
        
        self.root.after(0, update_status)


def run_gui():
    root = tk.Tk()
    app = IconExtractorApp(root)
    
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
