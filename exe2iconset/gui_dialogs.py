"""Custom dialogs for exe2iconset GUI."""

import os
import fnmatch
import tkinter as tk
from tkinter import ttk, messagebox


class FilePicker:
    """Custom file/folder picker dialog.
    
    Displays a treeview with directories and files from a selected directory.
    Allows selecting a file (double-click or single-click + Open) or
    returns the current directory if nothing is selected.
    
    Usage:
        picker = FilePicker(root, filetypes=[("All Files", "*.*")])
        result = picker.go()
        # Returns: file path, directory path, or None (cancelled)
    """
    
    def __init__(self, master, title="Select File or Folder", filetypes=None):
        """Initialize the FilePicker dialog.
        
        Args:
            master: Parent Tk window
            title: Dialog title
            filetypes: List of (name, pattern) tuples, e.g., [("Text", "*.txt")]
        """
        self.master = master
        self.result = None
        self.current_dir = os.path.abspath(os.getcwd())
        self.filetypes = filetypes if filetypes else [("All Files", "*.*")]
        
        self._create_dialog(title)
    
    def _create_dialog(self, title):
        """Create the dialog UI."""
        self.top = tk.Toplevel(self.master)
        self.top.title(title)
        self.top.geometry("600x500")
        self.top.minsize(400, 300)
        
        self._create_navigation()
        self._create_file_list()
        self._create_filter()
        self._create_buttons()
        
        self.tree.bind("<Double-1>", self._on_double_click)
        self.refresh_tree()
        self.top.protocol("WM_DELETE_WINDOW", self._cancel_command)
    
    def _create_navigation(self):
        """Create navigation bar."""
        nav_frame = ttk.Frame(self.top)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(nav_frame, text="▲ Up", width=5, command=self._go_up).pack(side="left")
        
        self.path_label = ttk.Label(nav_frame, text=self.current_dir, background="#eee")
        self.path_label.pack(side="left", fill="x", expand=True, padx=5)
    
    def _create_file_list(self):
        """Create file list using Treeview."""
        self.tree = ttk.Treeview(self.top, show="tree")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scrollbar.set)
    
    def _create_filter(self):
        """Create file type filter dropdown."""
        filter_frame = ttk.Frame(self.top)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Files of type:").pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar()
        self.filter_box = ttk.Combobox(filter_frame, textvariable=self.filter_var, state="readonly")
        self.filter_box["values"] = [f"{name} ({ext})" for name, ext in self.filetypes]
        self.filter_box.current(0)
        self.filter_box.pack(side="left", fill="x", expand=True)
        self.filter_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())
    
    def _create_buttons(self):
        """Create action buttons."""
        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Open", command=self._ok_command).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel_command).pack(side="right")
    
    def refresh_tree(self):
        """Refresh the file list."""
        self.tree.delete(*self.tree.get_children())
        self.path_label.config(text=self.current_dir)
        
        current_filter_idx = self.filter_box.current()
        pattern = self.filetypes[current_filter_idx][1]
        
        # Split pattern (can be multiple like "*.exe *.dll *.png")
        patterns = pattern.split()
        
        try:
            items = os.listdir(self.current_dir)
        except PermissionError:
            tk.messagebox.showerror("Error", "Permission Denied")
            return
        
        dirs = [i for i in items if os.path.isdir(os.path.join(self.current_dir, i))]
        files = [i for i in items if os.path.isfile(os.path.join(self.current_dir, i))]
        
        # Filter files by any matching pattern
        if patterns == ["*.*"] or not patterns:
            filtered_files = files
        else:
            filtered_files = [f for f in files if any(fnmatch.fnmatch(f, p) for p in patterns)]
        
        for d in sorted(dirs, key=str.lower):
            path = os.path.join(self.current_dir, d)
            self.tree.insert("", "end", iid=path, text="📁 " + d)
        
        for f in sorted(filtered_files, key=str.lower):
            path = os.path.join(self.current_dir, f)
            self.tree.insert("", "end", iid=path, text="📄 " + f)
    
    def _go_up(self):
        """Navigate to parent directory."""
        parent = os.path.dirname(self.current_dir)
        if parent != self.current_dir:
            self.current_dir = parent
            self.refresh_tree()
    
    def _on_double_click(self, event):
        """Handle double-click on tree item."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        
        if os.path.isdir(item_id):
            self.current_dir = item_id
            self.refresh_tree()
        elif os.path.isfile(item_id):
            self.result = item_id
            self._done()
    
    def _ok_command(self):
        """Handle Open button click."""
        selection = self.tree.selection()
        if selection:
            self.result = selection[0]
        else:
            self.result = self.current_dir
        self._done()
    
    def _cancel_command(self):
        """Handle Cancel button or window close."""
        self.result = None
        self._done()
    
    def _done(self):
        """Close the dialog."""
        self.top.grab_release()
        self.top.destroy()
    
    def go(self):
        """Show the dialog and return the result.
        
        Returns:
            str: Selected file path, directory path, or None if cancelled
        """
        self.top.grab_set()
        self.top.wait_window()
        return self.result