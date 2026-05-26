import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TkinterDnD = None
    DND_FILES = None

from .core.extract import extract_images, PE_EXTENSIONS
from .core.images import detect_input_type, IMAGE_EXTENSIONS
from .core.convert import convert_icons_to_icns_sizes, save_iconset
from .core.icns import ICON_TYPE_MAP, create_icns_from_images
from exe2iconset.gui_dialogs import FilePicker


def safe_progress_update(progressbar, current, total):
    try:
        if progressbar.winfo_exists():
            progressbar.config(value=current * 100 // total)
    except tk.TclError:
        pass


def safe_call_after(root, func):
    try:
        if root.winfo_exists():
            func()
    except tk.TclError:
        pass


class IconExtractorApp:
    def __init__(self, root, external_mode=False):
        self.root = root
        self.external_mode = external_mode
        if external_mode:
            self.root.title("Select Icon Series")
        else:
            self.root.title("Windows EXE to macOS ICNS Converter")
        self.root.geometry("900x700")
        
        self.dnd_available = TkinterDnD is not None
        
        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.selected_icons = []
        self.icon_series = {}
        self.selected_series_key = None
        self.thumbnail_images = []
        self.thumbnail_cache = {}
        self.log_messages = []
        self.input_type = None
        
        self.create_widgets()
        self.check_requirements()
        
        if self.dnd_available:
            self.setup_dnd()

    def setup_dnd(self):
        if not self.dnd_available:
            return
        
        try:
            if hasattr(self.step1_frame, 'drop_target_register'):
                self.step1_frame.drop_target_register(DND_FILES)
                self.step1_frame.dnd_bind('<<Drop>>', self._handle_drop)
                self.log_status("Drag & drop is enabled. Drag files here.")
        except Exception as e:
            self.dnd_available = False
            self.log_status(f"Drag & drop unavailable: {e}")

    def _handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        if files:
            input_path = files[0]
            in_type = detect_input_type(input_path)
            if in_type == 'unknown':
                messagebox.showwarning("Unsupported File", 
                    f"Unsupported file type. Please drop an EXE, DLL, MUN, or image file.")
                return
            
            self.input_path.set(input_path)
            
            if os.path.isfile(input_path):
                input_dir = os.path.dirname(input_path)
                input_stem = os.path.splitext(os.path.basename(input_path))[0]
            else:
                input_dir = input_path
                input_stem = os.path.basename(input_path)
            
            if hasattr(self, 'output_dir'):
                self.output_dir.set(input_dir)
            if hasattr(self, 'output_name'):
                self.output_name.set(input_stem)
            if hasattr(self, 'output_preview'):
                self.update_output_preview()
            self.log_status(f"Dropped: {input_path}")
            self.extract_icons()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        step1_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Input File", padding="10")
        step1_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        step1_frame.columnconfigure(1, weight=1)
        self.step1_frame = step1_frame
        
        ttk.Label(step1_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        input_entry = ttk.Entry(step1_frame, textvariable=self.input_path, width=50)
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        input_entry.bind('<Return>', lambda e: self.extract_icons())
        
        ttk.Button(step1_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2, padx=(2, 0))
        
        if not self.external_mode:
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
        
        step3_label = "Step 2: Select Icon" if self.external_mode else "Step 3: Select and Convert"
        step3_frame = ttk.LabelFrame(main_frame, text=step3_label, padding="10")
        step3_row = 2 if self.external_mode else 3
        step3_frame.grid(row=step3_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        step3_frame.columnconfigure(0, weight=1)
        step3_frame.rowconfigure(1, weight=1)
        
        self.progress = ttk.Progressbar(step3_frame, mode='determinate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        tree_frame = ttk.Frame(step3_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        tv_style = ttk.Style(self.root)
        tv_style.configure("Icons.Treeview", rowheight=130)

        self.icon_tree = ttk.Treeview(tree_frame, columns=("details",), selectmode="browse", style="Icons.Treeview")
        
        self.icon_tree.heading("#0", text="Icons Preview")
        self.icon_tree.heading("details", text="Details")
        self.icon_tree.column("#0", width=300, minwidth=300)
        self.icon_tree.column("details", width=200, minwidth=200)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._on_tree_scroll)
        def _on_yscroll(*args):
            vsb.set(*args)
            self.root.after(50, self._prepare_visible_thumbnails)
        self.icon_tree.configure(yscrollcommand=_on_yscroll)
        
        self.icon_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.icon_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        btn_text = "SELECT" if self.external_mode else "Convert to ICNS"
        self.convert_btn = ttk.Button(step3_frame, text=btn_text, command=self.on_convert_click)
        self.convert_btn.grid(row=2, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.log_messages = []
        
        status_frame = ttk.Frame(main_frame)
        status_row = 3 if self.external_mode else 4
        status_frame.grid(row=status_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, 
                                      anchor=tk.W, padding=(5, 2))
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.status_label.bind("<Button-1>", self._show_log_popup)
        
        weight_row = 2 if self.external_mode else 3
        main_frame.rowconfigure(weight_row, weight=1)
    
    def _on_tree_scroll(self, *args):
        self.icon_tree.yview(*args)
        self.root.after(50, self._prepare_visible_thumbnails)
    
    def check_requirements(self):
        try:
            import pefile
        except ImportError:
            messagebox.showerror("Missing Required Package", 
                "pefile (Python package) is required.\nPlease install it: pip install pefile")
            return
        
        try:
            Image.__version__
        except:
            messagebox.showerror("Missing Required Package", 
                "Pillow is required.\nPlease install it: pip install Pillow")
            return
        
        if not self.dnd_available:
            self.log_status("Drag & drop unavailable - use Browse button")
    
    def browse_input(self):
        filetypes = [
            ("All supported", f"{' '.join(f'*{ext}' for ext in sorted(PE_EXTENSIONS | IMAGE_EXTENSIONS))}"),
            ("PE files", " ".join(f"*{ext}" for ext in sorted(PE_EXTENSIONS))),
            ("Image files", " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS))),
        ]
        
        picker = FilePicker(self.root, title="Select Input File or Folder", filetypes=filetypes)
        result = picker.go()
        
        if result:
            self.input_path.set(result)
            
            if os.path.isfile(result):
                input_dir = os.path.dirname(result)
                input_stem = os.path.splitext(os.path.basename(result))[0]
                self.output_dir.set(input_dir)
                self.output_name.set(input_stem)
            else:
                self.output_dir.set(result)
                self.output_name.set(os.path.basename(result))
            
            self.update_output_preview()
            self.log_status(f"Selected: {result}")
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
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input file first")
            return
        
        self.input_type = detect_input_type(self.input_path.get())
        if self.input_type == 'unknown':
            messagebox.showerror("Error", "Unsupported input file type")
            return
        
        for item in self.icon_tree.get_children():
            self.icon_tree.delete(item)
        
        self.visible_items = []
        self.loaded_count = 0
        self.progress["maximum"] = 100
        self.progress["value"] = 0
        
        self.selected_icons = []
        self.icon_series = {}
        
        thread = threading.Thread(target=self._extract_icons_thread)
        thread.daemon = True
        thread.start()
    
    def _extract_icons_thread(self):
        def progress_callback(current, total):
            self.root.after(0, lambda c=current, t=total: safe_progress_update(self.progress, c, t))
        
        try:
            self.log_status("Loading images...")
            icon_files = extract_images(self.input_path.get(), self.log_status, progress_callback)
            
            if not icon_files:
                self.log_status("No images found.")
                self.root.after(0, lambda: safe_progress_update(self.progress, 0, 1))
                return

            self.icon_series = icon_files
            self.log_status(f"Found {len(self.icon_series)} image groups.")

            self.display_icons()
            return

        except Exception as e:
            self.log_status(f"Error during extraction: {str(e)}")
            return
    
    def display_icons(self):
        self.visible_items = list(self.icon_series.keys())
        total = len(self.visible_items)
        
        for item in self.icon_tree.get_children():
            self.icon_tree.delete(item)
        
        self.thumbnail_cache = {}
        self.thumbnail_images = []
        
        for series_name, icon_data_list in self.icon_series.items():
            count = len(icon_data_list)
            
            if icon_data_list:
                parts = series_name.split('_')
                id_part = parts[1] if len(parts) > 1 else "?"
                lang_part = parts[2] if len(parts) > 2 else "?"
                
                sorted_icons = sorted(icon_data_list, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
                
                # Group icons by resolution
                by_res = {}
                for icon in sorted_icons:
                    w = icon.get('width', 0)
                    h = icon.get('height', 0)
                    cb = icon.get('bit_count', 0)
                    if w and h and cb:
                        key = f"{w}x{h}"
                        if key not in by_res:
                            by_res[key] = set()
                        by_res[key].add(cb)
                
                res_parts = []
                for res_key in by_res:
                    bits = sorted(by_res[res_key], reverse=True)
                    res = res_key.split('x')
                    w = res[0]
                    h = res[1]
                    superscript = '²'
                    if h == w:
                        res_str = f"{w}{superscript}"
                    else:
                        res_str = f"{w}×{h}"
                    if len(bits) == 1:
                        res_parts.append(f"{res_str}×{bits[0]}bit")
                    else:
                        bits_str = ','.join(str(b) for b in bits)
                        res_parts.append(f"{res_str}×{{{bits_str}}}bit")
                
                details = f"ID:{id_part}, LANG:{lang_part}, all:{', '.join(res_parts)}"
                
                self.thumbnail_cache[series_name] = icon_data_list
                self.icon_tree.insert("", "end", iid=series_name, values=(details,))
            else:
                self.icon_tree.insert("", "end", iid=series_name, values=("No icons",))
        
        self.progress["maximum"] = total
        self.progress["value"] = total
        
        self.icon_tree.bind("<Configure>", lambda e: self._prepare_visible_thumbnails())
        self.root.after(100, self._prepare_visible_thumbnails)
        
        self.progress["maximum"] = total
        self.progress["value"] = total
        
        if total == 1:
            first_key = list(self.icon_series.keys())[0]
            first_item = self.icon_tree.get_children()[0]
            self.icon_tree.selection_set(first_item)
            self.selected_series_key = first_key
            action = "SELECT" if self.external_mode else "Convert"
            self.log_status(f"Found 1 icon series. Click '{action}' to continue.")
        else:
            action = "SELECT" if self.external_mode else "Convert"
            self.log_status(f"Found {len(self.icon_series)} icon series. Select one and click '{action}'.")
    
    def _on_tree_select(self, event):
        selection = self.icon_tree.selection()
        if selection:
            item_id = selection[0]
            self.select_series(item_id)
            self._prepare_visible_thumbnails()
    
    def select_series(self, series_name):
        self.selected_series_key = series_name
        self.log_status(f"Selected series: {series_name} with {len(self.icon_series[series_name])} icons")
    
    def on_convert_click(self):
        if self.selected_series_key is None:
            if len(self.icon_series) == 1:
                self.selected_series_key = list(self.icon_series.keys())[0]
            else:
                messagebox.showwarning("Select Series", "Please select an icon series from the list.")
                return
        
        if self.external_mode:
            self.select_and_return()
        else:
            self.create_icns()
    
    def select_and_return(self):
        if self.selected_series_key is not None:
            self.root.quit()
            self.root.destroy()
    
    def create_icns(self):
        if (self.selected_series_key is None) or not self.icon_series.get(self.selected_series_key):
            messagebox.showerror("Error", "Please select an icon series first")
            return
        
        if not self.output_dir.get():
            self.browse_output_dir()
            if not self.output_dir.get():
                return
        
        self.icon_tree.config(selectmode="none")
        
        thread = threading.Thread(target=self._create_icns_thread)
        thread.daemon = True
        thread.start()
    
    def _prepare_visible_thumbnails(self):
        all_items = list(self.thumbnail_cache.keys())
        
        target_height = 130
        
        for item_id in all_items:
            if self.icon_tree.item(item_id, "image"):
                continue
            
            bbox = self.icon_tree.bbox(item_id)
            if not bbox:
                continue
            
            icon_data_list = self.thumbnail_cache[item_id]
            
            sorted_icons = sorted(icon_data_list, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
            
            thumbnails = []
            for icon in sorted_icons:
                try:
                    w, h = icon.get('width', 32), icon.get('height', 32)
                    img = icon['image'].copy()
                    if h > target_height:
                        scale = target_height / h
                        new_w, new_h = int(w * scale), target_height
                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    thumbnails.append(img)
                except:
                    pass
            
            if thumbnails:
                total_width = sum(t.width for t in thumbnails)
                composite = Image.new('RGBA', (total_width, target_height), (0, 0, 0, 0))
                x_offset = 0
                for thumb in thumbnails:
                    composite.paste(thumb, (x_offset, 0))
                    x_offset += thumb.width
                
                photo = ImageTk.PhotoImage(composite)
                self.thumbnail_images.append(photo)
                self.icon_tree.item(item_id, image=photo)
    
    def _create_icns_thread(self):
        output_dir = self.output_dir.get()
        self.log_status("Starting ICNS conversion...")
        
        try:
            icon_data_list = self.icon_series[self.selected_series_key]
            output_name = self.output_name.get()
            
            iconset_name = output_name + ".iconset"
            iconset_path = os.path.join(output_dir, iconset_name)                      
            
            mac_icon_sizes = list(ICON_TYPE_MAP.keys())
            total_sizes = len(mac_icon_sizes)
            
            self.log_status(f"Converting {len(icon_data_list)} icons to {total_sizes} sizes...")
            
            regular_icons = convert_icons_to_icns_sizes(icon_data_list, mac_icon_sizes)
            
            self.log_status(f"Created {len(regular_icons)} icon sizes.")
            
            icns_path = os.path.join(output_dir, output_name + ".icns")
            
            saved = []
            try:
                if self.save_icns.get():
                    self.log_status("Creating ICNS file...")
                    if create_icns_from_images(regular_icons, icns_path):
                        saved.append(icns_path)
                        self.log_status(f"Successfully created ICNS file: {icns_path}")
                    else:
                        self.log_status("Failed to create ICNS")
                if self.save_iconset.get():
                    self.log_status("Creating iconset directory...")
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
        finally:
            self.root.after(0, lambda: safe_call_after(self.root, lambda: self.icon_tree.config(selectmode="browse")))
    
    def log_status(self, message):
        def update_status():
            try:
                if self.status_label.winfo_exists():
                    self.log_messages.append(message)
                    self.status_label.config(text=message)
            except tk.TclError:
                pass
        
        self.root.after(0, update_status)
    
    def _show_log_popup(self, event):
        if not self.log_messages:
            return
        
        popup = tk.Toplevel(self.root)
        popup.title("Log")
        popup.geometry("600x400")
        
        text_frame = tk.Frame(popup)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text = tk.Text(text_frame, wrap=tk.WORD)
        text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        vsb = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        text.configure(yscrollcommand=vsb.set)
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        for msg in self.log_messages:
            text.insert(tk.END, msg + "\n")
        
        text.config(state=tk.DISABLED)


def _destroy_orphaned_tk_windows():
    """Find and destroy any orphaned Tk windows that weren't assigned."""
    import gc
    
    gc.collect()
    for obj in gc.get_objects():
        try:
            if isinstance(obj, tk.Tk):
                if obj.winfo_exists():
                    obj.withdraw()
                    obj.destroy()
        except Exception:
            pass


def run_gui(external_mode=False, input_file=None, parent=None):
    global TkinterDnD, DND_FILES
    
    root = None
    
    if parent:
        root = tk.Toplevel(parent)
        root.transient(parent)
    elif TkinterDnD:
        try:
            root = TkinterDnD.Tk()
        except Exception:
            _destroy_orphaned_tk_windows()
            TkinterDnD = None
            DND_FILES = None
            root = tk.Tk()
    else:
        root = tk.Tk()
    
    app = IconExtractorApp(root, external_mode=external_mode)
    
    if external_mode and input_file:
        app.input_path.set(input_file)
        app.extract_icons()
    
    result = {}
    
    def on_select():
        if app.selected_series_key:
            result["series_key"] = app.selected_series_key
            result["icons"] = app.icon_series[app.selected_series_key]
        root.destroy()
    
    if external_mode:
        app.convert_btn.config(command=on_select)
        if parent:
            root.protocol("WM_DELETE_WINDOW", root.destroy)
        else:
            root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))
    else:
        root.protocol("WM_DELETE_WINDOW", root.destroy)
    
    if parent:
        root.grab_set()
        parent.wait_window(root)
    else:
        root.mainloop()
    
    if result:
        return result
    return None
